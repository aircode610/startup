import pytest
from unittest.mock import patch

from app.cart import CheckoutResult, checkout


# =============================================================================
# Authorization Tests
# =============================================================================

def test_checkout_unauthorized_when_missing_header():
    """Test that checkout fails when authorization header is None."""
    res = checkout(None, items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"
    assert res.subtotal == 0.0
    assert res.total == 0.0


def test_checkout_unauthorized_with_empty_string_header():
    """Test that checkout fails with empty authorization header."""
    res = checkout("", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"
    assert res.subtotal == 0.0
    assert res.total == 0.0


def test_checkout_unauthorized_with_malformed_bearer_token():
    """Test that checkout fails with malformed Bearer token (missing token part)."""
    res = checkout("Bearer", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_invalid_token_format():
    """Test that checkout fails when token doesn't start with 'user_'."""
    res = checkout("Bearer invalid_token", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_wrong_scheme():
    """Test that checkout fails with non-Bearer scheme."""
    res = checkout("Basic user_123", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


def test_checkout_unauthorized_with_extra_whitespace():
    """Test that checkout fails with extra parts in authorization header."""
    res = checkout("Bearer user_123 extra", items=[{"sku": "a", "qty": 1, "unit_price": 5.0}], user_tier="regular")
    assert res.authorized is False
    assert res.message == "unauthorized"


# =============================================================================
# Happy Path Tests - User Tier Variations
# =============================================================================

def test_checkout_authorized_happy_path_premium():
    """Test successful checkout for premium user with discount applied."""
    res = checkout(
        authorization_header="Bearer user_123",
        items=[{"sku": "a", "qty": 2, "unit_price": 10.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 18.0  # 10% discount applied
    assert res.message == "ok"


def test_checkout_authorized_happy_path_regular():
    """Test successful checkout for regular user with no discount."""
    res = checkout(
        authorization_header="Bearer user_456",
        items=[{"sku": "b", "qty": 2, "unit_price": 10.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 20.0
    assert res.total == 20.0  # No discount for regular users
    assert res.message == "ok"


def test_checkout_regular_user_should_not_get_premium_discount():
    """Critical test: Verify regular users don't receive premium discount."""
    res = checkout(
        authorization_header="Bearer user_regular",
        items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0, "Regular user should not receive premium discount"
    assert res.message == "ok"


def test_checkout_premium_user_gets_correct_discount():
    """Verify premium users receive exactly 10% discount."""
    res = checkout(
        authorization_header="Bearer user_premium",
        items=[{"sku": "item", "qty": 1, "unit_price": 50.0}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 50.0
    assert res.total == 45.0  # 10% discount
    assert res.message == "ok"


def test_checkout_default_user_tier():
    """Test checkout with default user_tier parameter (should be 'regular')."""
    res = checkout(
        authorization_header="Bearer user_default",
        items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    # Default is "regular", so no discount expected
    assert res.total == 100.0
    assert res.message == "ok"


# =============================================================================
# Edge Cases - Item Variations
# =============================================================================

def test_checkout_with_empty_items_list():
    """Test checkout with no items in cart."""
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
            {"sku": "item2", "qty": 1, "unit_price": 5.0},
            {"sku": "item3", "qty": 3, "unit_price": 2.50},
        ],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 32.50  # (2*10) + (1*5) + (3*2.5)
    assert res.total == 29.25  # 10% discount
    assert res.message == "ok"


def test_checkout_with_large_quantity():
    """Test checkout with large item quantity."""
    res = checkout(
        authorization_header="Bearer user_bulk",
        items=[{"sku": "bulk", "qty": 100, "unit_price": 1.0}],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    assert res.total == 100.0
    assert res.message == "ok"


def test_checkout_with_decimal_prices():
    """Test checkout with precise decimal prices."""
    res = checkout(
        authorization_header="Bearer user_decimal",
        items=[
            {"sku": "item1", "qty": 3, "unit_price": 3.33},
            {"sku": "item2", "qty": 2, "unit_price": 7.77},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 25.53  # (3*3.33) + (2*7.77) = 9.99 + 15.54
    assert res.total == 25.53
    assert res.message == "ok"


def test_checkout_with_zero_price_item():
    """Test checkout with zero-priced item (e.g., free sample)."""
    res = checkout(
        authorization_header="Bearer user_free",
        items=[
            {"sku": "paid", "qty": 1, "unit_price": 10.0},
            {"sku": "free", "qty": 1, "unit_price": 0.0},
        ],
        user_tier="regular",
    )
    assert res.authorized is True
    assert res.subtotal == 10.0
    assert res.total == 10.0
    assert res.message == "ok"


# =============================================================================
# Token Variations
# =============================================================================

def test_checkout_with_different_valid_token_formats():
    """Test various valid token formats that start with 'user_'."""
    valid_tokens = [
        "Bearer user_123",
        "Bearer user_abc",
        "Bearer user_123abc",
        "Bearer user_",
        "Bearer user_with_underscores",
    ]
    
    for token in valid_tokens:
        res = checkout(
            authorization_header=token,
            items=[{"sku": "test", "qty": 1, "unit_price": 10.0}],
            user_tier="regular",
        )
        assert res.authorized is True, f"Token {token} should be valid"
        assert res.message == "ok"


def test_checkout_with_bearer_case_insensitivity():
    """Test that Bearer scheme is case-insensitive."""
    case_variations = ["bearer user_123", "BEARER user_123", "BeArEr user_123"]
    
    for header in case_variations:
        res = checkout(
            authorization_header=header,
            items=[{"sku": "test", "qty": 1, "unit_price": 10.0}],
            user_tier="regular",
        )
        assert res.authorized is True, f"Header {header} should be valid"


# =============================================================================
# CheckoutResult Dataclass Tests
# =============================================================================

def test_checkout_result_is_frozen():
    """Test that CheckoutResult is immutable (frozen dataclass)."""
    result = CheckoutResult(
        authorized=True,
        subtotal=10.0,
        total=9.0,
        message="ok"
    )
    
    with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
        result.authorized = False


def test_checkout_result_equality():
    """Test CheckoutResult equality comparison."""
    result1 = CheckoutResult(authorized=True, subtotal=10.0, total=9.0, message="ok")
    result2 = CheckoutResult(authorized=True, subtotal=10.0, total=9.0, message="ok")
    result3 = CheckoutResult(authorized=False, subtotal=0.0, total=0.0, message="unauthorized")
    
    assert result1 == result2
    assert result1 != result3


# =============================================================================
# Integration with Mocked Dependencies
# =============================================================================

def test_checkout_with_mocked_invalid_token_validation():
    """Test checkout behavior when token validation is mocked to fail."""
    with patch('app.cart.validate_token', return_value=False):
        res = checkout(
            authorization_header="Bearer user_123",
            items=[{"sku": "test", "qty": 1, "unit_price": 10.0}],
            user_tier="regular",
        )
        assert res.authorized is False
        assert res.message == "unauthorized"
        assert res.subtotal == 0.0
        assert res.total == 0.0


def test_checkout_with_mocked_token_extraction_failure():
    """Test checkout when token extraction is mocked to return None."""
    with patch('app.cart.extract_bearer_token', return_value=None):
        res = checkout(
            authorization_header="Bearer user_123",
            items=[{"sku": "test", "qty": 1, "unit_price": 10.0}],
            user_tier="regular",
        )
        assert res.authorized is False
        assert res.message == "unauthorized"


def test_checkout_with_mocked_pricing_functions():
    """Test checkout with mocked pricing to verify call chain."""
    with patch('app.cart.compute_subtotal', return_value=100.0) as mock_subtotal, \
         patch('app.cart.apply_discount', return_value=85.0) as mock_discount:
        
        items = [{"sku": "test", "qty": 1, "unit_price": 100.0}]
        res = checkout(
            authorization_header="Bearer user_test",
            items=items,
            user_tier="premium",
        )
        
        assert res.authorized is True
        assert res.subtotal == 100.0
        assert res.total == 85.0
        
        # Verify the functions were called with correct arguments
        mock_subtotal.assert_called_once_with(items)
        mock_discount.assert_called_once_with(100.0, "premium")


# =============================================================================
# Error Propagation Tests
# =============================================================================

def test_checkout_propagates_compute_subtotal_errors():
    """Test that ValueError from compute_subtotal propagates correctly."""
    with pytest.raises(ValueError, match="qty must be positive"):
        checkout(
            authorization_header="Bearer user_test",
            items=[{"sku": "bad", "qty": 0, "unit_price": 10.0}],
            user_tier="regular",
        )


def test_checkout_propagates_negative_price_errors():
    """Test that ValueError from negative price propagates correctly."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        checkout(
            authorization_header="Bearer user_test",
            items=[{"sku": "bad", "qty": 1, "unit_price": -10.0}],
            user_tier="regular",
        )


def test_checkout_with_missing_item_fields():
    """Test checkout behavior with malformed item dictionaries."""
    with pytest.raises(KeyError):
        checkout(
            authorization_header="Bearer user_test",
            items=[{"sku": "incomplete"}],  # Missing qty and unit_price
            user_tier="regular",
        )


# =============================================================================
# Boundary and Special Cases
# =============================================================================

def test_checkout_with_very_small_prices():
    """Test checkout with very small decimal prices."""
    res = checkout(
        authorization_header="Bearer user_small",
        items=[{"sku": "penny", "qty": 1, "unit_price": 0.01}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 0.01
    assert res.total == 0.01  # 10% of 0.01 rounds to 0.01


def test_checkout_with_large_prices():
    """Test checkout with very large prices."""
    res = checkout(
        authorization_header="Bearer user_rich",
        items=[{"sku": "expensive", "qty": 1, "unit_price": 999999.99}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 999999.99
    assert res.total == 899999.99  # 10% discount


def test_checkout_rounding_behavior():
    """Test that prices are rounded correctly to 2 decimal places."""
    res = checkout(
        authorization_header="Bearer user_round",
        items=[{"sku": "item", "qty": 1, "unit_price": 10.006}],
        user_tier="regular",
    )
    assert res.authorized is True
    # compute_subtotal should round to 2 decimals
    assert res.subtotal == 10.01
    assert res.total == 10.01


def test_checkout_premium_discount_rounding():
    """Test premium discount rounding behavior."""
    res = checkout(
        authorization_header="Bearer user_premium_round",
        items=[{"sku": "item", "qty": 1, "unit_price": 33.33}],
        user_tier="premium",
    )
    assert res.authorized is True
    assert res.subtotal == 33.33
    # 33.33 * 0.9 = 29.997, should round to 30.00
    assert res.total == 30.00


# =============================================================================
# User Tier Edge Cases
# =============================================================================

def test_checkout_with_unknown_user_tier():
    """Test checkout with unrecognized user tier (should behave like regular)."""
    res = checkout(
        authorization_header="Bearer user_unknown",
        items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
        user_tier="gold",  # Unknown tier
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    # Unknown tiers get no discount (behave like regular)
    assert res.total == 100.0


def test_checkout_with_empty_string_user_tier():
    """Test checkout with empty string as user tier."""
    res = checkout(
        authorization_header="Bearer user_empty_tier",
        items=[{"sku": "item", "qty": 1, "unit_price": 50.0}],
        user_tier="",
    )
    assert res.authorized is True
    assert res.subtotal == 50.0
    assert res.total == 50.0  # No discount for empty tier


def test_checkout_with_case_sensitive_user_tier():
    """Test that user tier is case-sensitive."""
    res = checkout(
        authorization_header="Bearer user_case",
        items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
        user_tier="PREMIUM",  # Uppercase
    )
    assert res.authorized is True
    assert res.subtotal == 100.0
    # "PREMIUM" != "premium", so no discount
    assert res.total == 100.0
