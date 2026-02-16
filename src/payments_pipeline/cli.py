"""Command-line entrypoint for the payments pipeline."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from payments_pipeline.clients.mock_stripe import MockStripeClient
from payments_pipeline.config.logging import configure_logging, get_logger, set_run_context
from payments_pipeline.config.settings import Settings, get_settings
from payments_pipeline.extract.charges import ChargesExtractor
from payments_pipeline.extract.customers import CustomersExtractor
from payments_pipeline.extract.invoices import InvoicesExtractor
from payments_pipeline.extract.payment_intents import PaymentIntentsExtractor
from payments_pipeline.load.writer import BronzeWriter
from payments_pipeline.quality.freshness import run_freshness_checks
from payments_pipeline.quality.reconciliation import run_reconciliation
from payments_pipeline.quality.schema import run_schema_checks
from payments_pipeline.state.manifests import ManifestStore, write_run_manifest
from payments_pipeline.transform.duckdb_runner import run_transforms
from payments_pipeline.utils.ids import new_run_id


@dataclass(slots=True)
class RunContext:
    run_id: str
    env: str
    now: datetime
    settings: Settings

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "env": self.env,
            "now": self.now,
            "settings": self.settings,
            "base_dir": str(self.settings.local_data_dir),
        }


def _build_extractors(settings: Settings) -> dict[str, Any]:
    client = MockStripeClient(settings.mock_api_base_url)
    writer = BronzeWriter(settings)
    return {
        "payment_intents": PaymentIntentsExtractor(client, writer),
        "charges": ChargesExtractor(client, writer),
        "invoices": InvoicesExtractor(client, writer),
        "customers": CustomersExtractor(client, writer),
    }


def cmd_run_batch(args: argparse.Namespace, run_context: RunContext) -> int:
    logger = get_logger(__name__)
    extractors = _build_extractors(run_context.settings)
    if args.entity not in extractors:
        logger.error("invalid_entity", extra={"entity": args.entity})
        return 2

    result = extractors[args.entity].run(run_context.as_dict(), days=args.days)
    manifest = ManifestStore(run_context.settings.manifests_root)
    write_run_manifest(
        manifest,
        run_context.run_id,
        {
            "extract": {
                "entity": result.entity,
                "records": result.records,
                "pages": result.pages,
                "api_calls": result.api_calls,
                "retries": result.retries,
                "failures": result.failures,
                "bronze_paths": result.bronze_paths,
            }
        },
    )
    return 0


def cmd_run_all(args: argparse.Namespace, run_context: RunContext) -> int:
    extractors = _build_extractors(run_context.settings)
    results = []
    for name in ["payment_intents", "charges", "invoices", "customers"]:
        results.append(extractors[name].run(run_context.as_dict(), days=args.days))

    manifest = ManifestStore(run_context.settings.manifests_root)
    write_run_manifest(
        manifest,
        run_context.run_id,
        {
            "extract": [
                {
                    "entity": r.entity,
                    "records": r.records,
                    "pages": r.pages,
                    "api_calls": r.api_calls,
                    "retries": r.retries,
                    "failures": r.failures,
                    "bronze_paths": r.bronze_paths,
                }
                for r in results
            ]
        },
    )
    return 0


def cmd_run_transforms(run_context: RunContext) -> int:
    metrics = run_transforms(run_context.as_dict())
    manifest = ManifestStore(run_context.settings.manifests_root)
    write_run_manifest(
        manifest,
        run_context.run_id,
        {"transforms": [asdict(m) for m in metrics]},
    )
    return 0


def cmd_run_quality(run_context: RunContext) -> int:
    schema_results = run_schema_checks(run_context.settings.local_data_dir)
    freshness_results = run_freshness_checks(ManifestStore(run_context.settings.manifests_root))
    recon_result = run_reconciliation(
        run_context.settings.local_data_dir, ManifestStore(run_context.settings.manifests_root)
    )

    failed = (
        any(not r.passed for r in schema_results)
        or any(not r.passed for r in freshness_results)
        or not recon_result.passed
    )

    manifest = ManifestStore(run_context.settings.manifests_root)
    write_run_manifest(
        manifest,
        run_context.run_id,
        {
            "quality": {
                "schema": [asdict(r) for r in schema_results],
                "freshness": [asdict(r) for r in freshness_results],
                "reconciliation": asdict(recon_result),
            }
        },
    )
    return 1 if failed else 0


def cmd_run_webhooks(args: argparse.Namespace, run_context: RunContext) -> int:
    import uvicorn

    uvicorn.run(
        "payments_pipeline.webhooks.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


def cmd_run_pipeline(args: argparse.Namespace, run_context: RunContext) -> int:
    args.days = args.days or run_context.settings.default_days
    extract_exit = cmd_run_all(args, run_context)
    if extract_exit != 0:
        return extract_exit
    transform_exit = cmd_run_transforms(run_context)
    if transform_exit != 0:
        return transform_exit
    return cmd_run_quality(run_context)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="payments-pipeline")
    parser.add_argument("--run-id", default=None, help="Explicit run_id for cross-step traceability")
    sub = parser.add_subparsers(dest="command", required=True)

    p_batch = sub.add_parser("run-batch")
    p_batch.add_argument(
        "--entity", required=True, choices=["payment_intents", "charges", "invoices", "customers"]
    )
    p_batch.add_argument("--days", type=int, default=None)

    p_all = sub.add_parser("run-all")
    p_all.add_argument("--days", type=int, default=None)

    sub.add_parser("run-transforms")
    sub.add_parser("run-quality")
    p_pipeline = sub.add_parser("run-pipeline")
    p_pipeline.add_argument("--days", type=int, default=None)

    p_wh = sub.add_parser("run-webhooks")
    p_wh.add_argument("--host", default="0.0.0.0")
    p_wh.add_argument("--port", type=int, default=8000)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = get_settings()
        configure_logging(settings.log_level)
        run_id = args.run_id or os.getenv("RUN_ID") or new_run_id()
        run_context = RunContext(
            run_id=run_id,
            env=settings.pipeline_env,
            now=datetime.now(tz=UTC),
            settings=settings,
        )
        set_run_context(run_id=run_context.run_id)

        if args.command == "run-batch":
            args.days = args.days or settings.default_days
            return cmd_run_batch(args, run_context)
        if args.command == "run-all":
            args.days = args.days or settings.default_days
            return cmd_run_all(args, run_context)
        if args.command == "run-transforms":
            return cmd_run_transforms(run_context)
        if args.command == "run-quality":
            return cmd_run_quality(run_context)
        if args.command == "run-pipeline":
            return cmd_run_pipeline(args, run_context)
        if args.command == "run-webhooks":
            return cmd_run_webhooks(args, run_context)

        parser.print_help()
        return 2
    except Exception:
        get_logger(__name__).exception(
            "pipeline_command_failed", extra={"command": getattr(args, "command", "unknown")}
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
