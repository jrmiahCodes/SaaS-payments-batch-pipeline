"""FastAPI app for webhook ingestion."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from payments_pipeline.clients.webhook_signing import SignatureVerificationError
from payments_pipeline.config.settings import Settings, get_settings
from payments_pipeline.webhooks.handler import handle_stripe_webhook


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="payments-pipeline-webhooks")
    app.state.settings = settings or get_settings()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/webhooks/stripe")
    async def stripe_webhook(request: Request) -> JSONResponse:
        payload = await request.body()
        headers = {k: v for k, v in request.headers.items()}
        settings_obj: Settings = request.app.state.settings
        try:
            result = handle_stripe_webhook(payload, headers, settings_obj)
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "event_id": result.event_id,
                    "duplicate": result.duplicate,
                },
            )
        except SignatureVerificationError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
        except Exception as exc:  # pragma: no cover
            return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})

    return app


app = create_app()
