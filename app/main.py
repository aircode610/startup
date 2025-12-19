from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.cart import checkout

app = FastAPI(title="Precedent Demo Marketplace", version="0.1.0")


class CartItem(BaseModel):
    sku: str
    qty: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)


class CheckoutRequest(BaseModel):
    items: list[CartItem]
    user_tier: str = "regular"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/checkout")
def checkout_endpoint(payload: CheckoutRequest, authorization: str | None = None) -> dict:
    # NOTE: in real apps you'd read the HTTP header "Authorization".
    # For demo, we accept a query param named "authorization" to keep it simple.
    result = checkout(
        authorization_header=authorization,
        items=[it.model_dump() for it in payload.items],
        user_tier=payload.user_tier,
    )
    return {
        "authorized": result.authorized,
        "subtotal": result.subtotal,
        "total": result.total,
        "message": result.message,
    }

