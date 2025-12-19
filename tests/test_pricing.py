import pytest

from app.pricing import apply_discount, compute_subtotal


def test_compute_subtotal_basic():
    items = [
        {"sku": "a", "qty": 2, "unit_price": 3.50},
        {"sku": "b", "qty": 1, "unit_price": 10.00},
    ]
    assert compute_subtotal(items) == 17.0


def test_apply_discount_premium():
    assert apply_discount(100.0, "premium") == 90


def test_apply_discount_regular():
    assert apply_discount(100.0, "regular") == 100.0


def test_compute_subtotal_rejects_bad_qty():
    with pytest.raises(ValueError):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 1.0}])


def test_apply_discount_rejects_negative_subtotal():
    with pytest.raises(ValueError):
        apply_discount(-1.0, "premium")


# ============================================================================
# COMPREHENSIVE TESTS FOR apply_discount - focusing on int() conversion change
# ============================================================================

def test_apply_discount_premium_returns_integer_type():
    """Verify that premium discount returns an integer, not a float."""
    result = apply_discount(100.0, "premium")
    assert isinstance(result, int)
    assert result == 90


def test_apply_discount_premium_truncates_not_rounds():
    """Test that int() truncates decimals rather than rounding.
    
    Important: int(90.9) = 90, not 91 (truncation, not rounding)
    """
    # 99.0 * 0.90 = 89.1 → int() truncates to 89
    assert apply_discount(99.0, "premium") == 89
    
    # 101.0 * 0.90 = 90.9 → int() truncates to 90
    assert apply_discount(101.0, "premium") == 90
    
    # 109.0 * 0.90 = 98.1 → int() truncates to 98
    assert apply_discount(109.0, "premium") == 98
    
    # 111.0 * 0.90 = 99.9 → int() truncates to 99
    assert apply_discount(111.0, "premium") == 99


def test_apply_discount_premium_with_decimals():
    """Test premium discount with various decimal subtotals."""
    # 50.50 * 0.90 = 45.45 → 45
    assert apply_discount(50.50, "premium") == 45
    
    # 33.33 * 0.90 = 29.997 → 29
    assert apply_discount(33.33, "premium") == 29
    
    # 99.99 * 0.90 = 89.991 → 89
    assert apply_discount(99.99, "premium") == 89
    
    # 1.11 * 0.90 = 0.999 → 0
    assert apply_discount(1.11, "premium") == 0


def test_apply_discount_premium_small_amounts():
    """Test premium discount with small subtotals that might round to 0."""
    # 0.50 * 0.90 = 0.45 → 0
    assert apply_discount(0.50, "premium") == 0
    
    # 1.0 * 0.90 = 0.9 → 0
    assert apply_discount(1.0, "premium") == 0
    
    # 2.0 * 0.90 = 1.8 → 1
    assert apply_discount(2.0, "premium") == 1


def test_apply_discount_premium_large_amounts():
    """Test premium discount with large subtotals."""
    # 1000.0 * 0.90 = 900.0 → 900
    assert apply_discount(1000.0, "premium") == 900
    
    # 9999.99 * 0.90 = 8999.991 → 8999
    assert apply_discount(9999.99, "premium") == 8999
    
    # 10000.0 * 0.90 = 9000.0 → 9000
    assert apply_discount(10000.0, "premium") == 9000
    
    # 123456.78 * 0.90 = 111111.102 → 111111
    assert apply_discount(123456.78, "premium") == 111111


def test_apply_discount_premium_zero_subtotal():
    """Test premium discount with zero subtotal."""
    assert apply_discount(0.0, "premium") == 0
    assert isinstance(apply_discount(0.0, "premium"), int)


def test_apply_discount_premium_precision_edge_cases():
    """Test cases where truncation vs rounding makes a difference."""
    # These test values where .9 decimal would round up but int() truncates down
    
    # 10.01 * 0.90 = 9.009 → 9 (not 9.01)
    assert apply_discount(10.01, "premium") == 9
    
    # 20.01 * 0.90 = 18.009 → 18
    assert apply_discount(20.01, "premium") == 18
    
    # 11.12 * 0.90 = 10.008 → 10
    assert apply_discount(11.12, "premium") == 10


def test_apply_discount_regular_still_returns_float():
    """Verify regular tier still returns float with proper rounding."""
    result = apply_discount(100.0, "regular")
    assert isinstance(result, float)
    assert result == 100.0


def test_apply_discount_regular_rounds_correctly():
    """Test that regular users get proper float rounding."""
    # Should round to 2 decimal places
    assert apply_discount(99.999, "regular") == 100.0
    assert apply_discount(50.505, "regular") == 50.51
    assert apply_discount(50.504, "regular") == 50.5
    assert apply_discount(33.333, "regular") == 33.33


def test_apply_discount_regular_zero():
    """Test regular discount with zero subtotal."""
    assert apply_discount(0.0, "regular") == 0.0
    assert isinstance(apply_discount(0.0, "regular"), float)


def test_apply_discount_regular_small_amounts():
    """Test regular tier with small amounts."""
    assert apply_discount(0.01, "regular") == 0.01
    assert apply_discount(0.1, "regular") == 0.1
    assert apply_discount(1.0, "regular") == 1.0


def test_apply_discount_regular_large_amounts():
    """Test regular tier with large amounts."""
    assert apply_discount(10000.0, "regular") == 10000.0
    assert apply_discount(99999.99, "regular") == 99999.99


def test_apply_discount_unknown_tier_treated_as_regular():
    """Test that unknown tiers are treated as regular (no discount)."""
    assert apply_discount(100.0, "gold") == 100.0
    assert apply_discount(100.0, "silver") == 100.0
    assert apply_discount(100.0, "basic") == 100.0
    assert apply_discount(100.0, "") == 100.0
    assert apply_discount(100.0, "PREMIUM") == 100.0  # Case-sensitive


def test_apply_discount_negative_subtotal_raises_error():
    """Test that negative subtotals raise ValueError for all tiers."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "premium")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-1.0, "premium")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-100.0, "regular")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "regular")


def test_apply_discount_premium_maintains_mathematical_relationship():
    """Verify the 10% discount calculation is correct across values."""
    test_values = [10, 25, 50, 75, 100, 150, 200, 500, 1000]
    for value in test_values:
        result = apply_discount(float(value), "premium")
        expected = int(value * 0.90)
        assert result == expected, f"Failed for subtotal={value}"


# ============================================================================
# COMPREHENSIVE TESTS FOR compute_subtotal
# ============================================================================

def test_compute_subtotal_empty_list():
    """Test compute_subtotal with empty items list."""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_single_item():
    """Test compute_subtotal with a single item."""
    items = [{"sku": "abc", "qty": 5, "unit_price": 2.50}]
    assert compute_subtotal(items) == 12.5


def test_compute_subtotal_multiple_items():
    """Test compute_subtotal with multiple items."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 10.0},
        {"sku": "b", "qty": 2, "unit_price": 15.50},
        {"sku": "c", "qty": 1, "unit_price": 5.0},
    ]
    # 3*10 + 2*15.50 + 1*5 = 30 + 31 + 5 = 66.0
    assert compute_subtotal(items) == 66.0


def test_compute_subtotal_rounds_to_two_decimals():
    """Test that subtotal is rounded to 2 decimal places."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 3.333},  # 9.999
    ]
    assert compute_subtotal(items) == 10.0
    
    items = [
        {"sku": "b", "qty": 1, "unit_price": 10.004},
    ]
    assert compute_subtotal(items) == 10.0
    
    items = [
        {"sku": "c", "qty": 1, "unit_price": 10.005},
    ]
    assert compute_subtotal(items) == 10.01


def test_compute_subtotal_large_quantities():
    """Test compute_subtotal with large quantities."""
    items = [{"sku": "bulk", "qty": 1000, "unit_price": 0.99}]
    assert compute_subtotal(items) == 990.0


def test_compute_subtotal_large_prices():
    """Test compute_subtotal with large unit prices."""
    items = [{"sku": "expensive", "qty": 1, "unit_price": 9999.99}]
    assert compute_subtotal(items) == 9999.99


def test_compute_subtotal_zero_price():
    """Test compute_subtotal with zero unit price (free items)."""
    items = [{"sku": "free", "qty": 10, "unit_price": 0.0}]
    assert compute_subtotal(items) == 0.0


def test_compute_subtotal_mixed_zero_and_nonzero():
    """Test compute_subtotal with mix of free and paid items."""
    items = [
        {"sku": "free", "qty": 5, "unit_price": 0.0},
        {"sku": "paid", "qty": 2, "unit_price": 10.0},
    ]
    assert compute_subtotal(items) == 20.0


def test_compute_subtotal_decimal_quantities_converted_to_int():
    """Test that decimal quantities are converted to int."""
    items = [{"sku": "a", "qty": 5.9, "unit_price": 2.0}]
    # int(5.9) = 5, so 5 * 2.0 = 10.0
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_string_quantities_converted():
    """Test that string quantities can be converted to int."""
    items = [{"sku": "a", "qty": "3", "unit_price": 5.0}]
    assert compute_subtotal(items) == 15.0


def test_compute_subtotal_string_prices_converted():
    """Test that string prices can be converted to float."""
    items = [{"sku": "a", "qty": 2, "unit_price": "7.50"}]
    assert compute_subtotal(items) == 15.0


def test_compute_subtotal_zero_qty_raises_error():
    """Test that zero quantity raises ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 10.0}])


def test_compute_subtotal_negative_qty_raises_error():
    """Test that negative quantity raises ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 10.0}])
    
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -5, "unit_price": 10.0}])


def test_compute_subtotal_negative_price_raises_error():
    """Test that negative unit price raises ValueError."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -1.0}])
    
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 2, "unit_price": -0.01}])


def test_compute_subtotal_multiple_items_one_invalid_qty():
    """Test that invalid qty in multi-item list raises error."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 5.0},
        {"sku": "b", "qty": 0, "unit_price": 10.0},  # Invalid
    ]
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal(items)


def test_compute_subtotal_multiple_items_one_invalid_price():
    """Test that invalid price in multi-item list raises error."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 5.0},
        {"sku": "b", "qty": 1, "unit_price": -1.0},  # Invalid
    ]
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal(items)


def test_compute_subtotal_very_small_amounts():
    """Test compute_subtotal with very small amounts."""
    items = [{"sku": "penny", "qty": 1, "unit_price": 0.01}]
    assert compute_subtotal(items) == 0.01
    
    items = [{"sku": "pennies", "qty": 3, "unit_price": 0.01}]
    assert compute_subtotal(items) == 0.03


def test_compute_subtotal_precision_accumulation():
    """Test that rounding happens at the end, not per item."""
    items = [
        {"sku": "a", "qty": 1, "unit_price": 0.333},
        {"sku": "b", "qty": 1, "unit_price": 0.333},
        {"sku": "c", "qty": 1, "unit_price": 0.334},
    ]
    # 0.333 + 0.333 + 0.334 = 1.0, rounded to 1.0
    assert compute_subtotal(items) == 1.0


# ============================================================================
# INTEGRATION TESTS - apply_discount + compute_subtotal
# ============================================================================

def test_full_pricing_flow_premium():
    """Test complete flow: compute subtotal then apply premium discount."""
    items = [
        {"sku": "item1", "qty": 2, "unit_price": 25.0},
        {"sku": "item2", "qty": 1, "unit_price": 50.0},
    ]
    subtotal = compute_subtotal(items)  # 2*25 + 1*50 = 100.0
    assert subtotal == 100.0
    
    total = apply_discount(subtotal, "premium")  # 100 * 0.9 = 90
    assert total == 90
    assert isinstance(total, int)


def test_full_pricing_flow_regular():
    """Test complete flow: compute subtotal then apply regular discount."""
    items = [
        {"sku": "item1", "qty": 3, "unit_price": 15.50},
        {"sku": "item2", "qty": 2, "unit_price": 10.25},
    ]
    subtotal = compute_subtotal(items)  # 3*15.50 + 2*10.25 = 46.5 + 20.5 = 67.0
    assert subtotal == 67.0
    
    total = apply_discount(subtotal, "regular")
    assert total == 67.0
    assert isinstance(total, float)


def test_full_pricing_flow_premium_with_truncation():
    """Test flow where premium discount causes truncation."""
    items = [
        {"sku": "item1", "qty": 1, "unit_price": 99.99},
    ]
    subtotal = compute_subtotal(items)  # 99.99
    assert subtotal == 99.99
    
    total = apply_discount(subtotal, "premium")  # 99.99 * 0.9 = 89.991 → 89
    assert total == 89


def test_full_pricing_flow_edge_case_small_premium():
    """Test flow with small amounts that truncate to 0 for premium."""
    items = [
        {"sku": "cheap", "qty": 1, "unit_price": 1.00},
    ]
    subtotal = compute_subtotal(items)  # 1.0
    assert subtotal == 1.0
    
    total = apply_discount(subtotal, "premium")  # 1.0 * 0.9 = 0.9 → 0
    assert total == 0
