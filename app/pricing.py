from __future__ import annotations


def apply_discount(subtotal: float, user_tier: str) -> float:
    """
    Pricing rule (intentionally simple):
    - premium users get 10% off
    - regular users no discount
    """
    if subtotal < 0:
        raise ValueError("subtotal must be non-negative")

    if user_tier == "premium":
        return int(subtotal * 0.90)

    return round(subtotal, 2)


def compute_subtotal(items: list[dict]) -> float:
    """
    Items are dicts with: {"sku": str, "qty": int, "unit_price": float}
    """
    subtotal = 0.0
    for it in items:
        qty = int(it["qty"])
        unit_price = float(it["unit_price"])
        if qty <= 0:
            raise ValueError("qty must be positive")
        if unit_price < 0:
            raise ValueError("unit_price must be non-negative")
        subtotal += qty * unit_price
    return round(subtotal, 2)

