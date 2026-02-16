from payments_pipeline.load.paths import (
    bronze_relative_path,
    gold_relative_path,
    latest_model_relative_path,
    silver_relative_path,
)


def test_path_builders() -> None:
    assert bronze_relative_path("charges", "2026-02-15", "run-1", part=3).endswith("part-00003.jsonl")
    assert silver_relative_path("charges", "2026-02-15") == "silver/source=stripe/entity=charges/dt=2026-02-15/data.parquet"
    assert gold_relative_path("fct_payments", "2026-02-15") == "gold/model=fct_payments/dt=2026-02-15/data.parquet"
    assert latest_model_relative_path("fct_payments") == "_state/manifests/_latest/fct_payments.json"
