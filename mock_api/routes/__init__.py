"""Route registration for mock API."""

from __future__ import annotations

from fastapi import FastAPI

from mock_api.routes.charges import router as charges_router
from mock_api.routes.customers import router as customers_router
from mock_api.routes.invoices import router as invoices_router
from mock_api.routes.payment_intents import router as payment_intents_router


def register_routes(app: FastAPI) -> None:
    app.include_router(payment_intents_router)
    app.include_router(charges_router)
    app.include_router(invoices_router)
    app.include_router(customers_router)


__all__ = [
    "charges_router",
    "customers_router",
    "invoices_router",
    "payment_intents_router",
    "register_routes",
]
