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
    """Test that regular users get no discount (bug test: catches hardcoded 'premium')"""
    res = checkout(
        authorization_header="Bearer user_456",
        items=[{"sku": "b", "qty": 2, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0, "Regular users should NOT get discount"
    assert res.message == "ok"


def test_checkout_respects_user_tier_parameter():
    """Critical test: verify user_tier parameter is actually used, not hardcoded"""
    # Premium user should get 10% discount
    premium_res = checkout(
        authorization_header="Bearer user_premium",
        items=[{"sku": "item1", "qty": 1, "unit_price": 100.0}],
        user_tier="premium",
    )
    assert premium_res.total == 90.0, "Premium user should get 10% discount"
    
    # Regular user should get NO discount
    regular_res = checkout(
        authorization_header="Bearer user_regular",
        items=[{"sku": "item1", "qty": 1, "unit_price": 100.0}],
        user_tier="regular",
    )
    assert regular_res.total == 100.0, "Regular user should get NO discount"


def test_checkout_unauthorized_with_empty_header():
    """Test empty string authorization header"""
    res = checkout("", items=[{"sku": "x", "qty": 1, "unit_price": 5.0}])
    assert res.authorized is False
    assert res.message == "unauthorized"
    assert res.subtotal == 0.0
    assert res.total == 0.0


def test_checkout_unauthorized_with_malformed_bearer():
    """Test malformed Bearer token format"""
    res = checkout(
        authorization_header="Bearer",
        items=[{"sku": "y", "qty": 1, "unit_price": 10.0}],
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_invalid_token_prefix():
    """Test token that doesn't start with 'user_'"""
    res = checkout(
        authorization_header="Bearer invalid_token",
        items=[{"sku": "z", "qty": 1, "unit_price": 15.0}],
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_wrong_scheme():
    """Test authorization with non-Bearer scheme"""
    res = checkout(
        authorization_header="Basic user_123",
        items=[{"sku": "a", "qty": 1, "unit_price": 5.0}],
    )
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_with_single_item():
    """Test checkout with single item"""
    res = checkout(
        authorization_header="Bearer user_single",
        items=[{"sku": "single", "qty": 1, "unit_price": 25.50}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 25.50
    assert res.total == 25.50
    assert res.message == "ok"


def test_checkout_with_multiple_items():
    """Test checkout with multiple different items"""
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


def test_checkout_with_multiple_items_premium():
    """Test checkout with multiple items and premium discount"""
    res = checkout(
        authorization_header="Bearer user_multi_premium",
        items=[
            {"sku": "item1", "qty": 2, "unit_price": 10.0},
            {"sku": "item2", "qty": 3, "unit_price": 5.0},
            {"sku": "item3", "qty": 1, "unit_price": 7.50},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 42.50
    assert res.total == 38.25  # 42.50 * 0.90
    assert res.message == "ok"


def test_checkout_with_empty_items_list():
    """Test checkout with no items (edge case)"""
    res = checkout(
        authorization_header="Bearer user_empty",
        items=[],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 0.0
    assert res.total == 0.0
    assert res.message == "ok"


def test_checkout_with_high_quantity():
    """Test checkout with large quantity"""
    res = checkout(
        authorization_header="Bearer user_bulk",
        items=[{"sku": "bulk_item", "qty": 1000, "unit_price": 2.99}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 2990.0
    assert res.total == 2990.0
    assert res.message == "ok"


def test_checkout_with_decimal_prices():
    """Test checkout with various decimal prices"""
    res = checkout(
        authorization_header="Bearer user_decimal",
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


def test_checkout_with_zero_price_item():
    """Test checkout with free item (zero price)"""
    res = checkout(
        authorization_header="Bearer user_free",
        items=[
            {"sku": "free_item", "qty": 1, "unit_price": 0.0},
            {"sku": "paid_item", "qty": 1, "unit_price": 10.0},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 10.0
    assert res.total == 10.0
    assert res.message == "ok"


def test_checkout_default_user_tier():
    """Test checkout uses 'regular' as default user_tier"""
    res = checkout(
        authorization_header="Bearer user_default",
        items=[{"sku": "item", "qty": 1, "unit_price": 50.0}],
    )
    assert res.authorized is True
    assert res.subtotal == 50.0
    assert res.total == 50.0  # Should be no discount for default regular tier
    assert res.message == "ok"


def test_checkout_premium_with_small_amount():
    """Test premium discount on small purchase"""
    res = checkout(
        authorization_header="Bearer user_small_premium",
        items=[{"sku": "small", "qty": 1, "unit_price": 1.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 1.0
    assert res.total == 0.90  # 10% off
    assert res.message == "ok"


def test_checkout_regular_with_large_amount():
    """Test regular user with large purchase gets no discount"""
    res = checkout(
        authorization_header="Bearer user_large_regular",
        items=[{"sku": "expensive", "qty": 5, "unit_price": 200.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 1000.0
    assert res.total == 1000.0  # No discount for regular
    assert res.message == "ok"


def test_checkout_premium_with_large_amount():
    """Test premium user with large purchase gets discount"""
    res = checkout(
        authorization_header="Bearer user_large_premium",
        items=[{"sku": "expensive", "qty": 5, "unit_price": 200.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 1000.0
    assert res.total == 900.0  # 10% discount
    assert res.message == "ok"


def test_checkout_case_sensitive_bearer():
    """Test that Bearer scheme is case-insensitive (per HTTP spec)"""
    res = checkout(
        authorization_header="bearer user_lowercase",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.message == "ok"


def test_checkout_with_whitespace_in_header():
    """Test authorization header with extra whitespace"""
    res = checkout(
        authorization_header="  Bearer   user_whitespace  ",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    # This should fail due to split() behavior with extra spaces
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_result_immutability():
    """Test that CheckoutResult is immutable (frozen dataclass)"""
    res = checkout(
        authorization_header="Bearer user_immutable",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.0}],
        user_tier="regular",
    )
    
    # Attempting to modify should raise an error
    try:
        res.authorized = False
        assert False, "Should not be able to modify frozen dataclass"
    except AttributeError:
        pass  # Expected behavior


def test_checkout_consistency_across_calls():
    """Test that identical calls produce identical results"""
    items = [{"sku": "consistent", "qty": 2, "unit_price": 15.0}]
    
    res1 = checkout(
        authorization_header="Bearer user_consistent",
        items=items,
        user_tier="premium",
    )
    
    res2 = checkout(
        authorization_header="Bearer user_consistent",
        items=items,
        user_tier="premium",
    )
    
    assert res1.authorized == res2.authorized
    assert res1.subtotal == res2.subtotal
    assert res1.total == res2.total
    assert res1.message == res2.message


def test_checkout_unknown_user_tier():
    """Test checkout with unknown user tier (should treat as regular/no discount)"""
    res = checkout(
        authorization_header="Bearer user_unknown_tier",
        items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
        user_tier="vip",  # Unknown tier
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0  # Should not get discount
    assert res.message == "ok"
