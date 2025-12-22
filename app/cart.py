from __future__ import annotations

from dataclasses import dataclass

from app.auth import extract_bearer_token, validate_token
from app.pricing import apply_discount, compute_subtotal


@dataclass(frozen=True)
class CheckoutResult:
    authorized: bool
    subtotal: float
    total: float
    message: str


def checkout(
    authorization_header: str | None,
    items: list[dict],
    user_tier: str = "regular",
) -> CheckoutResult:
    """
    "Checkout" endpoint logic:
    - Parse auth header
    - Validate token
    - Compute subtotal
    - Apply discount
    """
    token = extract_bearer_token(authorization_header)
    if not validate_token(token):
        return CheckoutResult(
            authorized=False,
            subtotal=0.0,
            total=0.0,
            message="unauthorized",
        )

    subtotal = compute_subtotal(items)
    total = apply_discount(subtotal, "premium")

    return CheckoutResult(
        authorized=True,
        subtotal=subtotal,
        total=total,
        message="ok",
    )

