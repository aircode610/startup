import pytest

from app.pricing import apply_discount, compute_subtotal


def test_compute_subtotal_basic():
    items = [
        {"sku": "a", "qty": 2, "unit_price": 3.50},
        {"sku": "b", "qty": 1, "unit_price": 10.00},
    ]
    assert compute_subtotal(items) == 17.0


def test_apply_discount_premium():
    assert apply_discount(100.0, "premium") == 90.0


def test_apply_discount_regular():
    assert apply_discount(100.0, "regular") == 100.0


def test_compute_subtotal_rejects_bad_qty():
    with pytest.raises(ValueError):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 1.0}])


def test_apply_discount_rejects_negative_subtotal():
    with pytest.raises(ValueError):
        apply_discount(-1.0, "premium")



# Additional comprehensive tests for apply_discount with int() truncation behavior

def test_apply_discount_premium_truncates_decimal():
    """Test that premium discount truncates rather than rounds"""
    # 105.99 * 0.90 = 95.391 -> should truncate to 95, not round to 95
    assert apply_discount(105.99, "premium") == 95


def test_apply_discount_premium_truncates_high_decimal():
    """Test truncation when decimal part is >= 0.5"""
    # 111.11 * 0.90 = 99.999 -> should truncate to 99, not round to 100
    assert apply_discount(111.11, "premium") == 99


def test_apply_discount_premium_small_amount():
    """Test premium discount on small amounts"""
    # 1.00 * 0.90 = 0.90 -> truncates to 0
    assert apply_discount(1.00, "premium") == 0


def test_apply_discount_premium_very_small_amount():
    """Test premium discount on very small amounts"""
    # 0.50 * 0.90 = 0.45 -> truncates to 0
    assert apply_discount(0.50, "premium") == 0


def test_apply_discount_premium_zero():
    """Test premium discount on zero subtotal"""
    assert apply_discount(0.0, "premium") == 0


def test_apply_discount_premium_large_amount():
    """Test premium discount on large amounts"""
    # 10000.00 * 0.90 = 9000.00
    assert apply_discount(10000.00, "premium") == 9000


def test_apply_discount_premium_with_cents():
    """Test premium discount with various cent amounts"""
    # 99.99 * 0.90 = 89.991 -> truncates to 89
    assert apply_discount(99.99, "premium") == 89


def test_apply_discount_premium_rounds_down_not_up():
    """Test that values close to next integer truncate down"""
    # 222.22 * 0.90 = 199.998 -> truncates to 199, not 200
    assert apply_discount(222.22, "premium") == 199


def test_apply_discount_premium_exact_integer_result():
    """Test when discount results in exact integer"""
    # 1000.00 * 0.90 = 900.00 -> exact integer
    assert apply_discount(1000.00, "premium") == 900


def test_apply_discount_premium_fractional_input():
    """Test premium discount with fractional input"""
    # 15.55 * 0.90 = 13.995 -> truncates to 13
    assert apply_discount(15.55, "premium") == 13


def test_apply_discount_premium_many_decimals():
    """Test with many decimal places in input"""
    # 123.456 * 0.90 = 111.1104 -> truncates to 111
    assert apply_discount(123.456, "premium") == 111


def test_apply_discount_regular_zero():
    """Test regular user with zero subtotal"""
    assert apply_discount(0.0, "regular") == 0.0


def test_apply_discount_regular_with_decimals():
    """Test regular user preserves rounding to 2 decimal places"""
    assert apply_discount(99.999, "regular") == 100.0
    assert apply_discount(99.994, "regular") == 99.99


def test_apply_discount_regular_rounds_properly():
    """Test that regular tier still uses round() function"""
    # Should round to 2 decimal places
    assert apply_discount(12.345, "regular") == 12.35
    assert apply_discount(12.344, "regular") == 12.34


def test_apply_discount_regular_large_amount():
    """Test regular user with large amount"""
    assert apply_discount(9999.99, "regular") == 9999.99


def test_apply_discount_unknown_tier_no_discount():
    """Test that unknown user tiers get no discount (treated as regular)"""
    assert apply_discount(100.0, "gold") == 100.0
    assert apply_discount(100.0, "platinum") == 100.0
    assert apply_discount(100.0, "") == 100.0


def test_apply_discount_case_sensitivity():
    """Test that user_tier comparison is case-sensitive"""
    # "Premium" (capitalized) should not match "premium"
    assert apply_discount(100.0, "Premium") == 100.0
    assert apply_discount(100.0, "PREMIUM") == 100.0


def test_apply_discount_premium_boundary_values():
    """Test boundary values for premium discount"""
    # Test values that result in .99, .01, .5 after discount
    assert apply_discount(111.0, "premium") == 99  # 99.9 -> 99
    assert apply_discount(1.11, "premium") == 0    # 0.999 -> 0
    assert apply_discount(555.56, "premium") == 500 # 500.004 -> 500


def test_apply_discount_premium_returns_int_type():
    """Test that premium discount returns an int (even though type hint says float)"""
    result = apply_discount(100.0, "premium")
    assert isinstance(result, int)
    assert result == 90


def test_apply_discount_regular_returns_float_type():
    """Test that regular discount returns a float"""
    result = apply_discount(100.0, "regular")
    assert isinstance(result, float)
    assert result == 100.0


# Edge cases for compute_subtotal to improve coverage

def test_compute_subtotal_empty_list():
    """Test compute_subtotal with empty items list"""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_single_item():
    """Test compute_subtotal with single item"""
    items = [{"sku": "x", "qty": 5, "unit_price": 2.50}]
    assert compute_subtotal(items) == 12.5


def test_compute_subtotal_rounds_to_two_decimals():
    """Test that compute_subtotal rounds to 2 decimal places"""
    items = [{"sku": "a", "qty": 3, "unit_price": 3.333}]
    # 3 * 3.333 = 9.999 -> should round to 10.0
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_large_quantities():
    """Test compute_subtotal with large quantities"""
    items = [{"sku": "bulk", "qty": 1000, "unit_price": 0.99}]
    assert compute_subtotal(items) == 990.0


def test_compute_subtotal_free_item():
    """Test compute_subtotal with zero price item"""
    items = [
        {"sku": "free", "qty": 5, "unit_price": 0.0},
        {"sku": "paid", "qty": 1, "unit_price": 10.0},
    ]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_multiple_items_complex():
    """Test compute_subtotal with multiple items and complex decimals"""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 1.99},
        {"sku": "b", "qty": 2, "unit_price": 5.49},
        {"sku": "c", "qty": 1, "unit_price": 0.99},
    ]
    # 3*1.99 + 2*5.49 + 1*0.99 = 5.97 + 10.98 + 0.99 = 17.94
    assert compute_subtotal(items) == 17.94


def test_compute_subtotal_rejects_negative_qty():
    """Test that negative quantities are rejected"""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 5.0}])


def test_compute_subtotal_rejects_negative_price():
    """Test that negative unit prices are rejected"""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -5.0}])


def test_compute_subtotal_handles_string_numbers():
    """Test that compute_subtotal handles string numbers (gets converted)"""
    items = [{"sku": "a", "qty": "2", "unit_price": "5.0"}]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_rejects_zero_qty():
    """Test that zero quantity is explicitly rejected"""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 10.0}])


def test_apply_discount_with_float_near_boundary():
    """Test premium discount with floats very close to rounding boundaries"""
    # 100.01 * 0.90 = 90.009 -> truncates to 90
    assert apply_discount(100.01, "premium") == 90
    # 100.10 * 0.90 = 90.09 -> truncates to 90
    assert apply_discount(100.10, "premium") == 90
    # 100.11 * 0.90 = 90.099 -> truncates to 90
    assert apply_discount(100.11, "premium") == 90


def test_apply_discount_premium_consecutive_values():
    """Test premium discount behavior across consecutive subtotal values"""
    # Verify truncation is consistent
    assert apply_discount(10.0, "premium") == 9   # 9.0 -> 9
    assert apply_discount(11.0, "premium") == 9   # 9.9 -> 9
    assert apply_discount(12.0, "premium") == 10  # 10.8 -> 10
    assert apply_discount(13.0, "premium") == 11  # 11.7 -> 11


def test_apply_discount_real_world_scenarios():
    """Test realistic shopping cart scenarios"""
    # Cart total: $45.67 -> premium gets 41.103 -> truncates to 41
    assert apply_discount(45.67, "premium") == 41
    
    # Cart total: $123.45 -> premium gets 111.105 -> truncates to 111
    assert apply_discount(123.45, "premium") == 111
    
    # Cart total: $999.99 -> premium gets 899.991 -> truncates to 899
    assert apply_discount(999.99, "premium") == 899
