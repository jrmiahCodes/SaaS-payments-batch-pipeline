"""Mock Stripe-like API server."""

from __future__ import annotations

from fastapi import FastAPI

from mock_api.data_generator import GenerationConfig, generate_dataset
from mock_api.routes import register_routes


def create_app() -> FastAPI:
    app = FastAPI(title="mock-stripe-api")
    app.state.dataset = generate_dataset(GenerationConfig(seed=42, days=45, customers_per_day=6))

    @app.get("/")
    def root() -> dict[str, object]:
        return {
            "service": "mock-stripe-api",
            "status": "ok",
            "docs": "/docs",
            "health": "/health",
            "endpoints": [
                "/v1/payment_intents",
                "/v1/charges",
                "/v1/invoices",
                "/v1/customers",
            ],
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mock_api.app:app", host="127.0.0.1", port=8000, reload=False)
