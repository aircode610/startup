import pytest

from app.cart import CheckoutResult, checkout


# ============================================================================
# Authorization Tests
# ============================================================================


def test_checkout_unauthorized_when_missing_header():
    """Test that checkout fails when authorization header is None."""
    res = checkout(None, items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"
    assert res.subtotal == 0.0
    assert res.total == 0.0


def test_checkout_unauthorized_when_empty_header():
    """Test that checkout fails with empty string authorization header."""
    res = checkout("", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"
    assert res.subtotal == 0.0
    assert res.total == 0.0


def test_checkout_unauthorized_when_malformed_header():
    """Test that checkout fails with malformed authorization header (no Bearer prefix)."""
    res = checkout("user_123", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_when_invalid_token():
    """Test that checkout fails when token doesn't start with 'user_'."""
    res = checkout("Bearer invalid_token", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_when_token_only_spaces():
    """Test that checkout fails when token is only whitespace."""
    res = checkout("Bearer    ", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_when_wrong_scheme():
    """Test that checkout fails when using 'Basic' instead of 'Bearer'."""
    res = checkout("Basic user_123", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_authorized_with_valid_token():
    """Test that checkout succeeds with valid Bearer token."""
    res = checkout(
        authorization_header="Bearer user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.message == "ok"


def test_checkout_authorized_with_different_valid_tokens():
    """Test that checkout works with various valid user tokens."""
    tokens = ["user_123", "user_abc", "user_999", "user_admin", "user_"]
    for token in tokens:
        res = checkout(
            authorization_header=f"Bearer {token}",
            items=[{"sku": "a", "qty": 1, "unit_price": 10.0}],
            user_tier="regular",
        )
        assert res.authorized is True, f"Token {token} should be valid"
        assert res.message == "ok"


# ============================================================================
# User Tier and Discount Tests - CRITICAL for catching the bug!
# ============================================================================


def test_checkout_regular_user_no_discount():
    """Test that regular users get NO discount (this catches the bug!)."""
    res = checkout(
        authorization_header="Bearer user_regular",
        items=[{"sku": "a", "qty": 1, "unit_price": 100.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0  # No discount for regular users
    assert res.message == "ok"


def test_checkout_authorized_happy_path_premium():
    """Test that premium users get 10% discount."""
    res = checkout(
        authorization_header="Bearer user_123",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 18.0  # 10% discount applied
    assert res.message == "ok"


def test_checkout_premium_user_gets_discount():
    """Test premium discount calculation with different amounts."""
    res = checkout(
        authorization_header="Bearer user_premium",
        items=[{"sku": "widget", "qty": 1, "unit_price": 50.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 50.0
    assert res.total == 45.0  # 10% off = 45.0
    assert res.message == "ok"


def test_checkout_default_user_tier_is_regular():
    """Test that default user_tier parameter is 'regular' (no discount)."""
    res = checkout(
        authorization_header="Bearer user_default",
        items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
        # user_tier not specified, should default to "regular"
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0  # Should be no discount with default tier
    assert res.message == "ok"


def test_checkout_unknown_tier_treated_as_regular():
    """Test that unknown user tiers don't get premium discount."""
    res = checkout(
        authorization_header="Bearer user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 100.0}],
        user_tier="platinum",  # Unknown tier
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0  # No discount for unknown tiers
    assert res.message == "ok"


def test_checkout_tier_case_sensitivity():
    """Test that user_tier 'PREMIUM' (uppercase) is different from 'premium'."""
    res = checkout(
        authorization_header="Bearer user_upper",
        items=[{"sku": "a", "qty": 1, "unit_price": 100.0}],
        user_tier="PREMIUM",  # Uppercase
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    # Assuming case-sensitive comparison, no discount
    assert res.total == 100.0
    assert res.message == "ok"


# ============================================================================
# Items and Pricing Tests
# ============================================================================


def test_checkout_single_item():
    """Test checkout with a single item."""
    res = checkout(
        authorization_header="Bearer user_single",
        items=[{"sku": "laptop", "qty": 1, "unit_price": 999.99}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 999.99
    assert res.total == 999.99
    assert res.message == "ok"


def test_checkout_multiple_items():
    """Test checkout with multiple different items."""
    res = checkout(
        authorization_header="Bearer user_multi",
        items=[
            {"sku": "item1", "qty": 2, "unit_price": 10.0},
            {"sku": "item2", "qty": 1, "unit_price": 5.0},
            {"sku": "item3", "qty": 3, "unit_price": 7.5},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 47.5  # (2*10) + (1*5) + (3*7.5)
    assert res.total == 47.5
    assert res.message == "ok"


def test_checkout_multiple_items_with_premium_discount():
    """Test checkout with multiple items and premium discount."""
    res = checkout(
        authorization_header="Bearer user_premium_multi",
        items=[
            {"sku": "item1", "qty": 2, "unit_price": 25.0},
            {"sku": "item2", "qty": 1, "unit_price": 50.0},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 100.0  # (2*25) + (1*50)
    assert res.total == 90.0  # 10% discount
    assert res.message == "ok"


def test_checkout_empty_items_list():
    """Test checkout with empty items list (edge case)."""
    res = checkout(
        authorization_header="Bearer user_empty",
        items=[],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_zero_price_items():
    """Test checkout with items that have zero unit price."""
    res = checkout(
        authorization_header="Bearer user_free",
        items=[
            {"sku": "free_item", "qty": 5, "unit_price": 0.0},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_large_quantity():
    """Test checkout with large quantity of items."""
    res = checkout(
        authorization_header="Bearer user_bulk",
        items=[{"sku": "bulk_item", "qty": 1000, "unit_price": 2.5}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 2500.0
    assert res.total == 2500.0
    assert res.message == "ok"


def test_checkout_large_quantity_with_premium():
    """Test that premium discount applies correctly to large orders."""
    res = checkout(
        authorization_header="Bearer user_bulk_premium",
        items=[{"sku": "bulk_item", "qty": 1000, "unit_price": 1.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 1000.0
    assert res.total == 900.0  # 10% discount
    assert res.message == "ok"


def test_checkout_fractional_prices():
    """Test checkout with fractional unit prices."""
    res = checkout(
        authorization_header="Bearer user_fraction",
        items=[
            {"sku": "item1", "qty": 3, "unit_price": 1.99},
            {"sku": "item2", "qty": 2, "unit_price": 3.49},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 12.95  # (3*1.99) + (2*3.49) = 5.97 + 6.98
    assert res.total == 12.95
    assert res.message == "ok"


def test_checkout_rounding_with_premium():
    """Test that premium discount is properly rounded."""
    res = checkout(
        authorization_header="Bearer user_round",
        items=[{"sku": "item", "qty": 1, "unit_price": 33.33}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 33.33
    assert res.total == 30.0  # 33.33 * 0.9 = 29.997 -> rounds to 30.0
    assert res.message == "ok"


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_checkout_invalid_qty_zero():
    """Test that checkout raises ValueError for zero quantity."""
    with pytest.raises(ValueError, match="qty must be positive"):
        checkout(
            authorization_header="Bearer user_bad_qty",
            items=[{"sku": "item", "qty": 0, "unit_price": 10.0}],
            user_tier="regular",
        )


def test_checkout_invalid_qty_negative():
    """Test that checkout raises ValueError for negative quantity."""
    with pytest.raises(ValueError, match="qty must be positive"):
        checkout(
            authorization_header="Bearer user_neg_qty",
            items=[{"sku": "item", "qty": -5, "unit_price": 10.0}],
            user_tier="regular",
        )


def test_checkout_invalid_negative_price():
    """Test that checkout raises ValueError for negative unit price."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        checkout(
            authorization_header="Bearer user_neg_price",
            items=[{"sku": "item", "qty": 1, "unit_price": -10.0}],
            user_tier="regular",
        )


def test_checkout_mixed_valid_and_invalid_items():
    """Test that checkout fails if any item is invalid, even if others are valid."""
    with pytest.raises(ValueError):
        checkout(
            authorization_header="Bearer user_mixed",
            items=[
                {"sku": "valid", "qty": 1, "unit_price": 10.0},
                {"sku": "invalid", "qty": 0, "unit_price": 5.0},  # Invalid qty
            ],
            user_tier="regular",
        )


# ============================================================================
# CheckoutResult Dataclass Tests
# ============================================================================


def test_checkout_result_is_frozen():
    """Test that CheckoutResult is immutable (frozen dataclass)."""
    result = CheckoutResult(authorized=True, subtotal=100.0, total=90.0, message="ok")
    with pytest.raises(Exception):  # FrozenInstanceError in dataclasses
        result.total = 80.0


def test_checkout_result_structure():
    """Test CheckoutResult has all expected fields with correct types."""
    res = checkout(
        authorization_header="Bearer user_structure",
        items=[{"sku": "test", "qty": 1, "unit_price": 50.0}],
        user_tier="premium",
    )
    assert hasattr(res, "authorized")
    assert hasattr(res, "subtotal")
    assert hasattr(res, "total")
    assert hasattr(res, "message")
    assert isinstance(res.authorized, bool)
    assert isinstance(res.subtotal, float)
    assert isinstance(res.total, float)
    assert isinstance(res.message, str)


# ============================================================================
# Integration-style Tests (complete flows)
# ============================================================================


def test_checkout_complete_flow_regular_user():
    """Test complete checkout flow for a regular user."""
    # Simulate a regular user buying 3 items
    res = checkout(
        authorization_header="Bearer user_complete_regular",
        items=[
            {"sku": "book", "qty": 2, "unit_price": 15.99},
            {"sku": "pen", "qty": 5, "unit_price": 2.50},
            {"sku": "notebook", "qty": 1, "unit_price": 8.99},
        ],
        user_tier="regular",
    )
    expected_subtotal = (2 * 15.99) + (5 * 2.50) + (1 * 8.99)  # 53.47
    assert res.authorized is True
    assert res.subtotal == 53.47
    assert res.total == 53.47  # No discount for regular
    assert res.message == "ok"


def test_checkout_complete_flow_premium_user():
    """Test complete checkout flow for a premium user."""
    # Simulate a premium user buying the same items
    res = checkout(
        authorization_header="Bearer user_complete_premium",
        items=[
            {"sku": "book", "qty": 2, "unit_price": 15.99},
            {"sku": "pen", "qty": 5, "unit_price": 2.50},
            {"sku": "notebook", "qty": 1, "unit_price": 8.99},
        ],
        user_tier="premium",
    )
    expected_subtotal = (2 * 15.99) + (5 * 2.50) + (1 * 8.99)  # 53.47
    expected_total = round(expected_subtotal * 0.9, 2)  # 48.12
    assert res.authorized is True
    assert res.subtotal == 53.47
    assert res.total == 48.12  # 10% discount applied
    assert res.message == "ok"


def test_checkout_unauthorized_user_gets_zero_amounts():
    """Test that unauthorized users get zero subtotal and total regardless of items."""
    res = checkout(
        authorization_header="Bearer invalid_user",  # Invalid token
        items=[{"sku": "expensive", "qty": 10, "unit_price": 1000.0}],
        user_tier="premium",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"
