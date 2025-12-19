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



# ============================================================================
# Additional comprehensive tests for apply_discount behavior changes
# ============================================================================

def test_apply_discount_premium_truncates_not_rounds():
    """Premium discount now uses int() truncation instead of round()"""
    # 99.99 * 0.90 = 89.991, int() truncates to 89 (not rounds to 90)
    assert apply_discount(99.99, "premium") == 89
    
    # 111.11 * 0.90 = 99.999, int() truncates to 99 (not rounds to 100)
    assert apply_discount(111.11, "premium") == 99


def test_apply_discount_premium_returns_integer_type():
    """Verify that premium discount returns an integer, not float"""
    result = apply_discount(100.0, "premium")
    assert isinstance(result, int)
    assert result == 90


def test_apply_discount_premium_with_decimal_amounts():
    """Test premium discount with various decimal subtotals"""
    # Test truncation with different decimal values
    assert apply_discount(50.50, "premium") == 45  # 50.50 * 0.90 = 45.45 -> 45
    assert apply_discount(75.75, "premium") == 68  # 75.75 * 0.90 = 68.175 -> 68
    assert apply_discount(123.45, "premium") == 111  # 123.45 * 0.90 = 111.105 -> 111
    assert apply_discount(99.95, "premium") == 89  # 99.95 * 0.90 = 89.955 -> 89


def test_apply_discount_premium_edge_case_near_rounding_boundary():
    """Test cases where int() and round() would give different results"""
    # 55.56 * 0.90 = 50.004, int() = 50, round() would be 50
    assert apply_discount(55.56, "premium") == 50
    
    # 55.57 * 0.90 = 50.013, int() = 50, round() would be 50
    assert apply_discount(55.57, "premium") == 50
    
    # 166.67 * 0.90 = 150.003, int() = 150, round() would be 150
    assert apply_discount(166.67, "premium") == 150


def test_apply_discount_premium_with_whole_numbers():
    """Test premium discount with whole number subtotals"""
    assert apply_discount(10.0, "premium") == 9  # 10.0 * 0.90 = 9.0 -> 9
    assert apply_discount(50.0, "premium") == 45  # 50.0 * 0.90 = 45.0 -> 45
    assert apply_discount(200.0, "premium") == 180  # 200.0 * 0.90 = 180.0 -> 180
    assert apply_discount(1000.0, "premium") == 900  # 1000.0 * 0.90 = 900.0 -> 900


def test_apply_discount_premium_with_small_amounts():
    """Test premium discount with small subtotals"""
    assert apply_discount(0.0, "premium") == 0  # 0.0 * 0.90 = 0.0 -> 0
    assert apply_discount(0.01, "premium") == 0  # 0.01 * 0.90 = 0.009 -> 0
    assert apply_discount(1.0, "premium") == 0  # 1.0 * 0.90 = 0.9 -> 0
    assert apply_discount(1.11, "premium") == 0  # 1.11 * 0.90 = 0.999 -> 0
    assert apply_discount(1.12, "premium") == 1  # 1.12 * 0.90 = 1.008 -> 1


def test_apply_discount_premium_with_large_amounts():
    """Test premium discount with large subtotals"""
    assert apply_discount(10000.0, "premium") == 9000
    assert apply_discount(99999.99, "premium") == 89999  # 99999.99 * 0.90 = 89999.991 -> 89999
    assert apply_discount(123456.78, "premium") == 111111  # 123456.78 * 0.90 = 111111.102 -> 111111


def test_apply_discount_regular_maintains_rounding():
    """Regular users should still get rounded results"""
    assert apply_discount(99.99, "regular") == 99.99
    assert apply_discount(50.50, "regular") == 50.50
    assert apply_discount(123.456, "regular") == 123.46  # Should round to 2 decimals
    assert apply_discount(99.994, "regular") == 99.99  # Should round to 2 decimals
    assert apply_discount(99.995, "regular") == 100.0  # Should round to 2 decimals


def test_apply_discount_regular_returns_float():
    """Verify that regular discount returns a float"""
    result = apply_discount(100.0, "regular")
    assert isinstance(result, float)
    assert result == 100.0


def test_apply_discount_regular_with_zero():
    """Test regular discount with zero subtotal"""
    assert apply_discount(0.0, "regular") == 0.0


def test_apply_discount_with_unknown_tier():
    """Test behavior with unknown user tier (should be treated as regular)"""
    assert apply_discount(100.0, "unknown") == 100.0
    assert apply_discount(50.50, "gold") == 50.50
    assert apply_discount(75.0, "") == 75.0
    assert apply_discount(100.0, "PREMIUM") == 100.0  # Case sensitive


def test_apply_discount_case_sensitivity():
    """Verify that user_tier matching is case-sensitive"""
    # Only exact "premium" should get discount
    assert apply_discount(100.0, "premium") == 90
    assert apply_discount(100.0, "Premium") == 100.0
    assert apply_discount(100.0, "PREMIUM") == 100.0
    assert apply_discount(100.0, "PrEmIuM") == 100.0


def test_apply_discount_with_floating_point_precision():
    """Test edge cases related to floating point precision"""
    # Test values that might have floating point representation issues
    assert apply_discount(33.33, "premium") == 29  # 33.33 * 0.90 = 29.997 -> 29
    assert apply_discount(66.66, "premium") == 59  # 66.66 * 0.90 = 59.994 -> 59
    assert apply_discount(0.99, "premium") == 0  # 0.99 * 0.90 = 0.891 -> 0


def test_apply_discount_premium_exact_90_percent():
    """Verify the discount is exactly 10% off (90% of original)"""
    test_values = [10.0, 25.0, 100.0, 250.0, 1000.0]
    for val in test_values:
        result = apply_discount(val, "premium")
        expected = int(val * 0.90)
        assert result == expected, f"For {val}, expected {expected}, got {result}"


# ============================================================================
# Additional comprehensive tests for compute_subtotal
# ============================================================================

def test_compute_subtotal_empty_list():
    """Test compute_subtotal with empty items list"""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_single_item():
    """Test compute_subtotal with a single item"""
    items = [{"sku": "x", "qty": 5, "unit_price": 2.0}]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_multiple_items():
    """Test compute_subtotal with multiple items"""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 5.00},
        {"sku": "b", "qty": 2, "unit_price": 7.50},
        {"sku": "c", "qty": 1, "unit_price": 10.00},
    ]
    # 3*5.00 + 2*7.50 + 1*10.00 = 15.00 + 15.00 + 10.00 = 40.00
    assert compute_subtotal(items) == 40.0


def test_compute_subtotal_with_decimal_unit_prices():
    """Test compute_subtotal with various decimal unit prices"""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 3.99},
        {"sku": "b", "qty": 3, "unit_price": 12.50},
    ]
    # 2*3.99 + 3*12.50 = 7.98 + 37.50 = 45.48
    assert compute_subtotal(items) == 45.48


def test_compute_subtotal_rounds_to_two_decimals():
    """Test that compute_subtotal properly rounds to 2 decimal places"""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 3.333},
    ]
    # 3 * 3.333 = 9.999, should round to 10.00
    assert compute_subtotal(items) == 10.0
    
    items = [
        {"sku": "b", "qty": 7, "unit_price": 1.428571},
    ]
    # 7 * 1.428571 = 9.999997, should round to 10.00
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_with_zero_unit_price():
    """Test compute_subtotal with zero unit price (free items)"""
    items = [
        {"sku": "free", "qty": 10, "unit_price": 0.0},
    ]
    assert compute_subtotal(items) == 0.0
    
    # Mixed free and paid items
    items = [
        {"sku": "free", "qty": 5, "unit_price": 0.0},
        {"sku": "paid", "qty": 2, "unit_price": 10.0},
    ]
    assert compute_subtotal(items) == 20.0


def test_compute_subtotal_with_large_quantities():
    """Test compute_subtotal with large quantities"""
    items = [
        {"sku": "bulk", "qty": 1000, "unit_price": 0.50},
    ]
    assert compute_subtotal(items) == 500.0
    
    items = [
        {"sku": "wholesale", "qty": 10000, "unit_price": 1.99},
    ]
    assert compute_subtotal(items) == 19900.0


def test_compute_subtotal_with_large_unit_prices():
    """Test compute_subtotal with expensive items"""
    items = [
        {"sku": "luxury", "qty": 1, "unit_price": 9999.99},
    ]
    assert compute_subtotal(items) == 9999.99
    
    items = [
        {"sku": "premium", "qty": 2, "unit_price": 5432.10},
    ]
    assert compute_subtotal(items) == 10864.20


def test_compute_subtotal_rejects_negative_qty():
    """Test that negative quantities are rejected"""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 10.0}])
    
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -100, "unit_price": 5.0}])


def test_compute_subtotal_rejects_zero_qty():
    """Test that zero quantity is rejected"""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 10.0}])


def test_compute_subtotal_rejects_negative_unit_price():
    """Test that negative unit prices are rejected"""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -1.0}])
    
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 5, "unit_price": -10.50}])


def test_compute_subtotal_rejects_bad_qty_in_multi_item_list():
    """Test that validation works for each item in a multi-item list"""
    items = [
        {"sku": "good", "qty": 5, "unit_price": 10.0},
        {"sku": "bad", "qty": 0, "unit_price": 5.0},
        {"sku": "also_good", "qty": 2, "unit_price": 3.0},
    ]
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal(items)


def test_compute_subtotal_rejects_bad_unit_price_in_multi_item_list():
    """Test that unit_price validation works in multi-item lists"""
    items = [
        {"sku": "good", "qty": 5, "unit_price": 10.0},
        {"sku": "bad", "qty": 2, "unit_price": -5.0},
    ]
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal(items)


def test_compute_subtotal_with_string_numeric_values():
    """Test that string values are properly converted to numbers"""
    items = [
        {"sku": "a", "qty": "3", "unit_price": "5.50"},
    ]
    assert compute_subtotal(items) == 16.50


def test_compute_subtotal_with_float_qty():
    """Test that float quantities are converted to int"""
    items = [
        {"sku": "a", "qty": 5.9, "unit_price": 2.0},
    ]
    # qty is converted via int(5.9) = 5
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_precision_with_many_items():
    """Test floating point precision with many items"""
    items = [
        {"sku": f"item_{i}", "qty": 1, "unit_price": 0.01}
        for i in range(100)
    ]
    # 100 * 0.01 = 1.00
    assert compute_subtotal(items) == 1.0


def test_compute_subtotal_mixed_decimal_precision():
    """Test mixed precision scenarios"""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 10.005},  # 30.015
        {"sku": "b", "qty": 2, "unit_price": 5.004},   # 10.008
    ]
    # 30.015 + 10.008 = 40.023, rounds to 40.02
    assert compute_subtotal(items) == 40.02


# ============================================================================
# Integration tests for apply_discount + compute_subtotal
# ============================================================================

def test_full_pricing_flow_premium_user():
    """Test complete pricing flow for premium user"""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 25.50},
        {"sku": "b", "qty": 1, "unit_price": 49.00},
    ]
    subtotal = compute_subtotal(items)  # 2*25.50 + 1*49.00 = 51.00 + 49.00 = 100.00
    assert subtotal == 100.0
    
    total = apply_discount(subtotal, "premium")  # 100.00 * 0.90 = 90.0 -> 90
    assert total == 90
    assert isinstance(total, int)


def test_full_pricing_flow_regular_user():
    """Test complete pricing flow for regular user"""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 15.00},
        {"sku": "b", "qty": 2, "unit_price": 10.50},
    ]
    subtotal = compute_subtotal(items)  # 3*15.00 + 2*10.50 = 45.00 + 21.00 = 66.00
    assert subtotal == 66.0
    
    total = apply_discount(subtotal, "regular")  # No discount
    assert total == 66.0
    assert isinstance(total, float)


def test_full_pricing_flow_with_complex_calculation():
    """Test complex pricing scenario"""
    items = [
        {"sku": "item1", "qty": 5, "unit_price": 19.99},
        {"sku": "item2", "qty": 3, "unit_price": 7.50},
        {"sku": "item3", "qty": 1, "unit_price": 99.95},
    ]
    subtotal = compute_subtotal(items)  # 5*19.99 + 3*7.50 + 1*99.95 = 99.95 + 22.50 + 99.95 = 222.40
    assert subtotal == 222.40
    
    premium_total = apply_discount(subtotal, "premium")  # 222.40 * 0.90 = 200.16 -> 200
    assert premium_total == 200
    
    regular_total = apply_discount(subtotal, "regular")
    assert regular_total == 222.40
