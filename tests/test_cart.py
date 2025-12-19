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



def test_checkout_authorized_happy_path_regular():
    """Test checkout with regular user tier - should NOT apply discount."""
    res = checkout(
        authorization_header="Bearer user_456",
        items=[{"sku": "b", "qty": 2, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0  # No discount for regular users
    assert res.message == "ok"


def test_checkout_respects_user_tier_parameter():
    """Critical test: Ensure user_tier parameter is actually used, not hardcoded."""
    # Premium user should get 10% discount
    premium_res = checkout(
        authorization_header="Bearer user_premium_123",
        items=[{"sku": "item1", "qty": 1, "unit_price": 100.0}],
        user_tier="premium",
    )
    assert premium_res.total == 90.0

    # Regular user should NOT get discount
    regular_res = checkout(
        authorization_header="Bearer user_regular_456",
        items=[{"sku": "item1", "qty": 1, "unit_price": 100.0}],
        user_tier="regular",
    )
    assert regular_res.total == 100.0


def test_checkout_default_user_tier():
    """Test that default user_tier='regular' works correctly."""
    res = checkout(
        authorization_header="Bearer user_default",
        items=[{"sku": "x", "qty": 1, "unit_price": 50.0}],
    )
    assert res.authorized is True
    assert res.subtotal == 50.0
    assert res.total == 50.0  # Default is regular, no discount
    assert res.message == "ok"


def test_checkout_unauthorized_empty_bearer_token():
    """Test checkout fails with empty Bearer token."""
    res = checkout(
        authorization_header="Bearer ",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="premium",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_unauthorized_invalid_token_format():
    """Test checkout fails with invalid token that doesn't start with 'user_'."""
    res = checkout(
        authorization_header="Bearer invalid_token_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="premium",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_unauthorized_malformed_header():
    """Test checkout fails with malformed authorization header."""
    res = checkout(
        authorization_header="NotBearer user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_header_without_bearer():
    """Test checkout fails when header doesn't contain 'Bearer' scheme."""
    res = checkout(
        authorization_header="user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_empty_string_header():
    """Test checkout fails with empty string authorization header."""
    res = checkout(
        authorization_header="",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_with_empty_items_list():
    """Test checkout with empty items list."""
    res = checkout(
        authorization_header="Bearer user_empty",
        items=[],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_with_single_item():
    """Test checkout with a single item."""
    res = checkout(
        authorization_header="Bearer user_single",
        items=[{"sku": "single", "qty": 1, "unit_price": 15.50}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 15.50
    assert res.total == 15.50
    assert res.message == "ok"


def test_checkout_with_multiple_items():
    """Test checkout with multiple different items."""
    res = checkout(
        authorization_header="Bearer user_multi",
        items=[
            {"sku": "item1", "qty": 2, "unit_price": 10.0},
            {"sku": "item2", "qty": 3, "unit_price": 5.0},
            {"sku": "item3", "qty": 1, "unit_price": 7.50},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 42.50  # (2*10) + (3*5) + (1*7.50)
    assert res.total == 42.50
    assert res.message == "ok"


def test_checkout_premium_with_multiple_items():
    """Test checkout premium user with multiple items gets proper discount."""
    res = checkout(
        authorization_header="Bearer user_premium_multi",
        items=[
            {"sku": "item1", "qty": 2, "unit_price": 10.0},
            {"sku": "item2", "qty": 3, "unit_price": 5.0},
            {"sku": "item3", "qty": 1, "unit_price": 7.50},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 42.50
    assert res.total == 38.25  # 42.50 * 0.90 = 38.25
    assert res.message == "ok"


def test_checkout_with_large_quantities():
    """Test checkout with large quantities."""
    res = checkout(
        authorization_header="Bearer user_bulk",
        items=[{"sku": "bulk", "qty": 100, "unit_price": 2.50}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 250.0
    assert res.total == 250.0
    assert res.message == "ok"


def test_checkout_with_decimal_prices():
    """Test checkout handles decimal prices correctly."""
    res = checkout(
        authorization_header="Bearer user_decimal",
        items=[
            {"sku": "decimal1", "qty": 3, "unit_price": 3.33},
            {"sku": "decimal2", "qty": 2, "unit_price": 7.77},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 25.53  # (3*3.33) + (2*7.77) = 9.99 + 15.54
    assert res.total == 25.53
    assert res.message == "ok"


def test_checkout_premium_with_decimal_prices():
    """Test premium discount with decimal prices rounds correctly."""
    res = checkout(
        authorization_header="Bearer user_premium_decimal",
        items=[{"sku": "item", "qty": 1, "unit_price": 33.33}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 33.33
    assert res.total == 30.0  # 33.33 * 0.90 = 29.997, rounded to 30.00
    assert res.message == "ok"


def test_checkout_with_zero_price_items():
    """Test checkout with items that have zero price (e.g., free items)."""
    res = checkout(
        authorization_header="Bearer user_free",
        items=[{"sku": "free_item", "qty": 5, "unit_price": 0.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_mixed_free_and_paid_items():
    """Test checkout with mix of free and paid items."""
    res = checkout(
        authorization_header="Bearer user_mixed",
        items=[
            {"sku": "paid", "qty": 2, "unit_price": 10.0},
            {"sku": "free", "qty": 1, "unit_price": 0.0},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0
    assert res.message == "ok"


def test_checkout_case_sensitivity_bearer():
    """Test that Bearer token scheme is case-insensitive."""
    res = checkout(
        authorization_header="bearer user_lowercase",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.message == "ok"


def test_checkout_result_immutability():
    """Test that CheckoutResult is immutable (frozen dataclass)."""
    res = checkout(
        authorization_header="Bearer user_immutable",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    # Attempting to modify should raise an error
    import pytest
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        res.total = 999.0


def test_checkout_different_valid_tokens():
    """Test checkout accepts various valid token formats starting with 'user_'."""
    valid_tokens = [
        "user_123",
        "user_abc",
        "user_",
        "user_admin",
        "user_premium_gold",
        "user_regular_silver",
    ]
    for token in valid_tokens:
        res = checkout(
            authorization_header=f"Bearer {token}",
            items=[{"sku": "test", "qty": 1, "unit_price": 10.0}],
            user_tier="regular",
        )
        assert res.authorized is True, f"Token {token} should be valid"
        assert res.message == "ok"


def test_checkout_preserves_subtotal_on_failure():
    """Test that unauthorized checkout returns zero for subtotal and total."""
    res = checkout(
        authorization_header="Bearer invalid",
        items=[{"sku": "expensive", "qty": 10, "unit_price": 100.0}],
        user_tier="premium",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_very_small_prices():
    """Test checkout with very small unit prices."""
    res = checkout(
        authorization_header="Bearer user_tiny",
        items=[{"sku": "tiny", "qty": 100, "unit_price": 0.01}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 1.0
    assert res.total == 1.0
    assert res.message == "ok"


def test_checkout_premium_very_small_prices():
    """Test premium discount with very small prices."""
    res = checkout(
        authorization_header="Bearer user_premium_tiny",
        items=[{"sku": "tiny", "qty": 10, "unit_price": 0.01}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 0.10
    assert res.total == 0.09  # 0.10 * 0.90 = 0.09
    assert res.message == "ok"


def test_checkout_unauthorized_extra_spaces_in_header():
    """Test checkout handles extra spaces in authorization header."""
    res = checkout(
        authorization_header="Bearer  user_123  extra",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_tier_distinction_edge_case():
    """
    Edge case test: Verify that a regular user and premium user
    with identical items get different totals.
    """
    items = [{"sku": "same", "qty": 5, "unit_price": 20.0}]
    
    regular_res = checkout(
        authorization_header="Bearer user_regular_edge",
        items=items,
        user_tier="regular",
    )
    
    premium_res = checkout(
        authorization_header="Bearer user_premium_edge",
        items=items,
        user_tier="premium",
    )
    
    # Both should be authorized
    assert regular_res.authorized is True
    assert premium_res.authorized is True
    
    # Both should have same subtotal
    assert regular_res.subtotal == 100.0
    assert premium_res.subtotal == 100.0
    
    # But different totals due to discount
    assert regular_res.total == 100.0
    assert premium_res.total == 90.0
    
    # Difference should be exactly 10% of subtotal
    assert regular_res.total - premium_res.total == 10.0
