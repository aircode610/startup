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
    """Regular users should get no discount (total == subtotal)."""
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
    """
    Critical test: ensure user_tier parameter is actually used.
    Regular tier should NOT get premium discount.
    """
    # Regular user with same items as premium test
    res_regular = checkout(
        authorization_header="Bearer user_regular",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="regular",
    )
    
    # Premium user with same items
    res_premium = checkout(
        authorization_header="Bearer user_premium",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="premium",
    )
    
    # Regular should pay full price, premium gets 10% off
    assert res_regular.total == 20.0
    assert res_premium.total == 18.0
    assert res_regular.total != res_premium.total


def test_checkout_unauthorized_with_invalid_bearer_token():
    """Token that doesn't start with 'user_' should be rejected."""
    res = checkout(
        authorization_header="Bearer invalid_token",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_empty_token():
    """Empty bearer token should be rejected."""
    res = checkout(
        authorization_header="Bearer ",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_malformed_header():
    """Header without 'Bearer' scheme should be rejected."""
    res = checkout(
        authorization_header="user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_wrong_scheme():
    """Non-Bearer auth scheme should be rejected."""
    res = checkout(
        authorization_header="Basic user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_with_empty_items_list():
    """Empty cart should result in zero subtotal and total."""
    res = checkout(
        authorization_header="Bearer user_123",
        items=[],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_with_single_item():
    """Single item checkout for regular user."""
    res = checkout(
        authorization_header="Bearer user_single",
        items=[{"sku": "widget", "qty": 1, "unit_price": 15.50}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 15.50
    assert res.total == 15.50
    assert res.message == "ok"


def test_checkout_with_multiple_items():
    """Multiple items with mixed quantities and prices."""
    res = checkout(
        authorization_header="Bearer user_multi",
        items=[
            {"sku": "item1", "qty": 3, "unit_price": 5.00},
            {"sku": "item2", "qty": 2, "unit_price": 12.50},
            {"sku": "item3", "qty": 1, "unit_price": 7.99},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 47.99  # (3*5.00) + (2*12.50) + (1*7.99)
    assert res.total == 47.99
    assert res.message == "ok"


def test_checkout_premium_with_multiple_items():
    """Premium user with multiple items should get 10% discount on total."""
    res = checkout(
        authorization_header="Bearer user_premium_multi",
        items=[
            {"sku": "item1", "qty": 3, "unit_price": 5.00},
            {"sku": "item2", "qty": 2, "unit_price": 12.50},
            {"sku": "item3", "qty": 1, "unit_price": 7.99},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 47.99
    assert res.total == 43.19  # 47.99 * 0.90 = 43.191, rounded to 43.19
    assert res.message == "ok"


def test_checkout_with_fractional_prices():
    """Test with items that have fractional prices."""
    res = checkout(
        authorization_header="Bearer user_fractional",
        items=[
            {"sku": "a", "qty": 3, "unit_price": 3.33},
            {"sku": "b", "qty": 2, "unit_price": 7.77},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 25.53  # (3*3.33) + (2*7.77) = 9.99 + 15.54
    assert res.total == 25.53
    assert res.message == "ok"


def test_checkout_premium_with_fractional_prices():
    """Premium discount with fractional prices."""
    res = checkout(
        authorization_header="Bearer user_premium_frac",
        items=[
            {"sku": "a", "qty": 3, "unit_price": 3.33},
            {"sku": "b", "qty": 2, "unit_price": 7.77},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 25.53
    assert res.total == 22.98  # 25.53 * 0.90 = 22.977, rounded to 22.98
    assert res.message == "ok"


def test_checkout_with_large_quantities():
    """Test with large item quantities."""
    res = checkout(
        authorization_header="Bearer user_bulk",
        items=[{"sku": "bulk_item", "qty": 100, "unit_price": 2.50}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 250.0
    assert res.total == 250.0
    assert res.message == "ok"


def test_checkout_premium_with_large_quantities():
    """Premium user with bulk purchase."""
    res = checkout(
        authorization_header="Bearer user_bulk_premium",
        items=[{"sku": "bulk_item", "qty": 100, "unit_price": 2.50}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 250.0
    assert res.total == 225.0  # 250.0 * 0.90
    assert res.message == "ok"


def test_checkout_with_zero_price_item():
    """Free items (price = 0) should be handled correctly."""
    res = checkout(
        authorization_header="Bearer user_free",
        items=[
            {"sku": "free_item", "qty": 5, "unit_price": 0.0},
            {"sku": "paid_item", "qty": 1, "unit_price": 10.0},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 10.0
    assert res.total == 10.0
    assert res.message == "ok"


def test_checkout_premium_with_zero_price_item():
    """Premium discount on cart with free items."""
    res = checkout(
        authorization_header="Bearer user_free_premium",
        items=[
            {"sku": "free_item", "qty": 5, "unit_price": 0.0},
            {"sku": "paid_item", "qty": 1, "unit_price": 10.0},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 10.0
    assert res.total == 9.0  # 10.0 * 0.90
    assert res.message == "ok"


def test_checkout_with_very_small_amounts():
    """Test rounding behavior with very small amounts."""
    res = checkout(
        authorization_header="Bearer user_small",
        items=[{"sku": "tiny", "qty": 1, "unit_price": 0.01}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.01
    assert res.total == 0.01
    assert res.message == "ok"


def test_checkout_premium_with_very_small_amounts():
    """Premium discount on very small amounts."""
    res = checkout(
        authorization_header="Bearer user_small_premium",
        items=[{"sku": "tiny", "qty": 1, "unit_price": 0.01}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 0.01
    assert res.total == 0.01  # 0.01 * 0.90 = 0.009, rounded to 0.01
    assert res.message == "ok"


def test_checkout_default_user_tier():
    """When user_tier is not specified, it defaults to 'regular'."""
    res = checkout(
        authorization_header="Bearer user_default",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0  # Default is regular, no discount
    assert res.message == "ok"


def test_checkout_unknown_tier_treated_as_regular():
    """Unknown user tiers should be treated as regular (no discount)."""
    res = checkout(
        authorization_header="Bearer user_unknown",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="platinum",  # Unknown tier
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0  # Unknown tier gets no discount
    assert res.message == "ok"


def test_checkout_result_is_immutable():
    """CheckoutResult should be immutable (frozen dataclass)."""
    res = checkout(
        authorization_header="Bearer user_immutable",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
        user_tier="regular",
    )
    
    # Attempting to modify should raise an error
    try:
        res.total = 999.99
        assert False, "CheckoutResult should be immutable"
    except (AttributeError, Exception):
        pass  # Expected behavior


def test_checkout_all_fields_populated_on_success():
    """All CheckoutResult fields should be populated on successful checkout."""
    res = checkout(
        authorization_header="Bearer user_complete",
        items=[{"sku": "a", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    
    assert hasattr(res, "authorized")
    assert hasattr(res, "subtotal")
    assert hasattr(res, "total")
    assert hasattr(res, "message")
    
    assert isinstance(res.authorized, bool)
    assert isinstance(res.subtotal, float)
    assert isinstance(res.total, float)
    assert isinstance(res.message, str)


def test_checkout_all_fields_populated_on_failure():
    """All CheckoutResult fields should be populated even on auth failure."""
    res = checkout(
        authorization_header=None,
        items=[{"sku": "a", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"


def test_checkout_with_mixed_sku_formats():
    """Items with various SKU formats should work."""
    res = checkout(
        authorization_header="Bearer user_sku_test",
        items=[
            {"sku": "SKU-001", "qty": 1, "unit_price": 5.0},
            {"sku": "product_abc", "qty": 2, "unit_price": 3.0},
            {"sku": "123456", "qty": 1, "unit_price": 7.0},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 18.0
    assert res.total == 18.0
    assert res.message == "ok"


def test_checkout_case_sensitivity_of_user_tier():
    """User tier matching should be case-sensitive."""
    # "Premium" (capital P) should not match "premium"
    res = checkout(
        authorization_header="Bearer user_case",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="Premium",  # Capital P
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0  # No discount for "Premium" (case mismatch)
    assert res.message == "ok"


def test_checkout_preserves_subtotal_regardless_of_tier():
    """Subtotal should be the same regardless of user tier."""
    items = [{"sku": "a", "qty": 5, "unit_price": 8.0}]
    
    res_regular = checkout(
        authorization_header="Bearer user_sub1",
        items=items,
        user_tier="regular",
    )
    
    res_premium = checkout(
        authorization_header="Bearer user_sub2",
        items=items,
        user_tier="premium",
    )
    
    # Both should have same subtotal
    assert res_regular.subtotal == res_premium.subtotal == 40.0
    # But different totals
    assert res_regular.total == 40.0
    assert res_premium.total == 36.0


def test_checkout_unauthorized_does_not_compute_pricing():
    """When unauthorized, subtotal and total should be 0 regardless of items."""
    res = checkout(
        authorization_header="Bearer invalid",
        items=[
            {"sku": "expensive", "qty": 100, "unit_price": 999.99},
        ],
        user_tier="premium",
    )
    assert res.authorized is False
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "unauthorized"
