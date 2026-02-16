"""Transform model registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModelSpec:
    name: str
    layer: str
    sql_path: Path


BASE_SQL_DIR = Path(__file__).resolve().parent / "sql"

SILVER_MODELS: list[ModelSpec] = [
    ModelSpec(name="payment_intents", layer="silver", sql_path=BASE_SQL_DIR / "silver" / "payment_intents.sql"),
    ModelSpec(name="charges", layer="silver", sql_path=BASE_SQL_DIR / "silver" / "charges.sql"),
    ModelSpec(name="invoices", layer="silver", sql_path=BASE_SQL_DIR / "silver" / "invoices.sql"),
    ModelSpec(name="customers", layer="silver", sql_path=BASE_SQL_DIR / "silver" / "customers.sql"),
]

GOLD_MODELS: list[ModelSpec] = [
    ModelSpec(name="dim_customers", layer="gold", sql_path=BASE_SQL_DIR / "gold" / "dim_customers.sql"),
    ModelSpec(name="fct_payments", layer="gold", sql_path=BASE_SQL_DIR / "gold" / "fct_payments.sql"),
    ModelSpec(name="fct_invoices", layer="gold", sql_path=BASE_SQL_DIR / "gold" / "fct_invoices.sql"),
]

MODEL_EXECUTION_ORDER: list[ModelSpec] = [*SILVER_MODELS, *GOLD_MODELS]
