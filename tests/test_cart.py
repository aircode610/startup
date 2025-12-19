from app.cart import checkout


def test_checkout_unauthorized_when_missing_header():
    res = checkout(None, items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_authorized_happy_path_premium():
    res = checkout(
        authorization_header="Bearer user_123",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 18.0
    assert res.message == "ok"



# ============================================================================
# Additional comprehensive integration tests for checkout with integer truncation
# ============================================================================

def test_checkout_premium_with_decimal_truncation():
    """Test that premium checkout truncates discount to integer."""
    # Subtotal: 2 * 10.50 = 21.0
    # Premium discount: int(21.0 * 0.90) = int(18.9) = 18
    res = checkout(
        authorization_header="Bearer user_456",
        items=[{"sku": "item1", "qty": 2, "unit_price": 10.50}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 21.0
    assert res.total == 18
    assert isinstance(res.total, int)
    assert res.message == "ok"


def test_checkout_premium_loses_fractional_cents():
    """Test that premium users lose fractional cents due to truncation."""
    # Subtotal: 99.99
    # Premium discount: int(99.99 * 0.90) = int(89.991) = 89
    # User loses 0.991 in this transaction
    res = checkout(
        authorization_header="Bearer user_premium",
        items=[{"sku": "expensive", "qty": 1, "unit_price": 99.99}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 99.99
    assert res.total == 89
    assert res.message == "ok"


def test_checkout_premium_small_amount_becomes_zero():
    """Test that small premium purchases can result in zero total."""
    # Subtotal: 1.0
    # Premium discount: int(1.0 * 0.90) = int(0.9) = 0
    res = checkout(
        authorization_header="Bearer user_small",
        items=[{"sku": "cheap", "qty": 1, "unit_price": 1.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 1.0
    assert res.total == 0
    assert res.message == "ok"


def test_checkout_premium_multiple_items_with_truncation():
    """Test premium checkout with multiple items and truncation."""
    # Subtotal: (3 * 7.77) + (2 * 5.55) = 23.31 + 11.10 = 34.41
    # Premium discount: int(34.41 * 0.90) = int(30.969) = 30
    res = checkout(
        authorization_header="Bearer user_multi",
        items=[
            {"sku": "a", "qty": 3, "unit_price": 7.77},
            {"sku": "b", "qty": 2, "unit_price": 5.55},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 34.41
    assert res.total == 30
    assert res.message == "ok"


def test_checkout_regular_maintains_decimal_precision():
    """Test that regular users still get decimal precision in total."""
    # Subtotal: 2 * 10.555 = 21.11 (rounded)
    # Regular: round(21.11, 2) = 21.11
    res = checkout(
        authorization_header="Bearer user_regular",
        items=[{"sku": "item", "qty": 2, "unit_price": 10.555}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 21.11
    assert res.total == 21.11
    assert res.message == "ok"


def test_checkout_regular_with_rounding():
    """Test regular checkout with subtotal rounding."""
    # Subtotal: 3 * 3.333 = 9.999 -> rounds to 10.0
    # Regular: round(10.0, 2) = 10.0
    res = checkout(
        authorization_header="Bearer user_round",
        items=[{"sku": "item", "qty": 3, "unit_price": 3.333}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 10.0
    assert res.total == 10.0
    assert res.message == "ok"


def test_checkout_premium_large_order():
    """Test premium checkout with large order."""
    # Subtotal: 100 * 99.99 = 9999.0
    # Premium discount: int(9999.0 * 0.90) = int(8999.1) = 8999
    res = checkout(
        authorization_header="Bearer user_whale",
        items=[{"sku": "bulk", "qty": 100, "unit_price": 99.99}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 9999.0
    assert res.total == 8999
    assert res.message == "ok"


def test_checkout_unauthorized_with_empty_bearer():
    """Test checkout fails with empty bearer token."""
    res = checkout(
        authorization_header="Bearer ",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_invalid_token():
    """Test checkout fails with invalid token (not starting with user_)."""
    res = checkout(
        authorization_header="Bearer invalid_token",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="premium",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_malformed_header():
    """Test checkout fails with malformed authorization header."""
    res = checkout(
        authorization_header="NotBearer user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_no_space_in_header():
    """Test checkout fails with header missing space."""
    res = checkout(
        authorization_header="Beareruser_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_premium_empty_cart():
    """Test premium checkout with empty cart results in zero."""
    res = checkout(
        authorization_header="Bearer user_empty",
        items=[],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0
    assert res.message == "ok"


def test_checkout_regular_empty_cart():
    """Test regular checkout with empty cart."""
    res = checkout(
        authorization_header="Bearer user_empty_reg",
        items=[],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_with_free_items_premium():
    """Test premium checkout with free items."""
    # Mix of free and paid items
    # Subtotal: (5 * 0.0) + (2 * 10.0) = 20.0
    # Premium: int(20.0 * 0.90) = 18
    res = checkout(
        authorization_header="Bearer user_free",
        items=[
            {"sku": "free", "qty": 5, "unit_price": 0.0},
            {"sku": "paid", "qty": 2, "unit_price": 10.0},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 18
    assert res.message == "ok"


def test_checkout_default_tier_is_regular():
    """Test that default user_tier behavior works as regular."""
    # When user_tier is not explicitly premium, should behave as regular
    res = checkout(
        authorization_header="Bearer user_default",
        items=[{"sku": "a", "qty": 1, "unit_price": 100.0}],
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0
    assert res.message == "ok"


def test_checkout_unknown_tier_treated_as_regular():
    """Test that unknown tier is treated as regular (no discount)."""
    res = checkout(
        authorization_header="Bearer user_gold",
        items=[{"sku": "a", "qty": 1, "unit_price": 100.0}],
        user_tier="gold",
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0
    assert res.message == "ok"


def test_checkout_case_sensitive_tier():
    """Test that user_tier is case-sensitive."""
    # "PREMIUM" should not get discount
    res = checkout(
        authorization_header="Bearer user_caps",
        items=[{"sku": "a", "qty": 1, "unit_price": 100.0}],
        user_tier="PREMIUM",
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0
    assert res.message == "ok"
