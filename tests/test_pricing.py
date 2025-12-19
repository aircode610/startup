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
# Additional comprehensive tests for apply_discount with integer truncation
# ============================================================================

def test_apply_discount_premium_truncates_to_integer():
    """Test that premium discount truncates to integer, not rounds."""
    # 105.0 * 0.90 = 94.5, should truncate to 94
    assert apply_discount(105.0, "premium") == 94
    assert isinstance(apply_discount(105.0, "premium"), int)


def test_apply_discount_premium_with_decimals_various_amounts():
    """Test premium discount truncation with various decimal amounts."""
    # 99.99 * 0.90 = 89.991 -> 89
    assert apply_discount(99.99, "premium") == 89
    
    # 50.55 * 0.90 = 45.495 -> 45
    assert apply_discount(50.55, "premium") == 45
    
    # 33.33 * 0.90 = 29.997 -> 29
    assert apply_discount(33.33, "premium") == 29
    
    # 10.01 * 0.90 = 9.009 -> 9
    assert apply_discount(10.01, "premium") == 9


def test_apply_discount_premium_small_amounts():
    """Test premium discount with small amounts near zero."""
    # 1.0 * 0.90 = 0.9 -> 0
    assert apply_discount(1.0, "premium") == 0
    
    # 0.50 * 0.90 = 0.45 -> 0
    assert apply_discount(0.50, "premium") == 0
    
    # 0.01 * 0.90 = 0.009 -> 0
    assert apply_discount(0.01, "premium") == 0


def test_apply_discount_premium_zero_subtotal():
    """Test premium discount with zero subtotal."""
    assert apply_discount(0.0, "premium") == 0


def test_apply_discount_premium_large_amounts():
    """Test premium discount with large amounts."""
    # 10000.0 * 0.90 = 9000.0 -> 9000
    assert apply_discount(10000.0, "premium") == 9000
    
    # 9999.99 * 0.90 = 8999.991 -> 8999
    assert apply_discount(9999.99, "premium") == 8999
    
    # 1000000.0 * 0.90 = 900000.0 -> 900000
    assert apply_discount(1000000.0, "premium") == 900000


def test_apply_discount_premium_edge_case_just_above_whole_number():
    """Test amounts where 90% is just above a whole number."""
    # 111.12 * 0.90 = 100.008 -> 100
    assert apply_discount(111.12, "premium") == 100
    
    # 222.23 * 0.90 = 200.007 -> 200
    assert apply_discount(222.23, "premium") == 200


def test_apply_discount_premium_edge_case_just_below_whole_number():
    """Test amounts where 90% is just below a whole number."""
    # 111.10 * 0.90 = 99.99 -> 99
    assert apply_discount(111.10, "premium") == 99
    
    # 55.54 * 0.90 = 49.986 -> 49
    assert apply_discount(55.54, "premium") == 49


def test_apply_discount_regular_maintains_decimal_precision():
    """Test that regular users still get proper decimal rounding."""
    assert apply_discount(99.999, "regular") == 100.0
    assert apply_discount(50.555, "regular") == 50.56
    assert apply_discount(10.001, "regular") == 10.0
    assert apply_discount(0.01, "regular") == 0.01


def test_apply_discount_regular_zero():
    """Test regular discount with zero subtotal."""
    assert apply_discount(0.0, "regular") == 0.0


def test_apply_discount_regular_large_amounts():
    """Test regular discount preserves large amounts correctly."""
    assert apply_discount(10000.0, "regular") == 10000.0
    assert apply_discount(9999.99, "regular") == 9999.99


def test_apply_discount_unknown_tier_treated_as_regular():
    """Test that unknown user tiers are treated as regular (no discount)."""
    assert apply_discount(100.0, "gold") == 100.0
    assert apply_discount(100.0, "silver") == 100.0
    assert apply_discount(100.0, "unknown") == 100.0
    assert apply_discount(100.0, "") == 100.0


def test_apply_discount_case_sensitivity():
    """Test that user_tier is case-sensitive."""
    # Only lowercase "premium" gets discount
    assert apply_discount(100.0, "PREMIUM") == 100.0
    assert apply_discount(100.0, "Premium") == 100.0
    assert apply_discount(100.0, "premium") == 90


def test_apply_discount_rejects_negative_premium():
    """Test that premium users also can't have negative subtotals."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "premium")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-100.0, "premium")


def test_apply_discount_rejects_negative_regular():
    """Test that regular users can't have negative subtotals."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "regular")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-100.0, "regular")


# ============================================================================
# Additional comprehensive tests for compute_subtotal
# ============================================================================

def test_compute_subtotal_single_item():
    """Test subtotal calculation with a single item."""
    items = [{"sku": "a", "qty": 1, "unit_price": 5.0}]
    assert compute_subtotal(items) == 5.0


def test_compute_subtotal_empty_list():
    """Test subtotal with no items."""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_multiple_items():
    """Test subtotal with multiple items."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 10.00},
        {"sku": "b", "qty": 2, "unit_price": 5.50},
        {"sku": "c", "qty": 1, "unit_price": 20.00},
    ]
    # 30.00 + 11.00 + 20.00 = 61.00
    assert compute_subtotal(items) == 61.0


def test_compute_subtotal_high_quantity():
    """Test subtotal with high quantities."""
    items = [{"sku": "a", "qty": 100, "unit_price": 1.99}]
    assert compute_subtotal(items) == 199.0


def test_compute_subtotal_zero_price():
    """Test subtotal with zero unit price (free items)."""
    items = [
        {"sku": "a", "qty": 5, "unit_price": 0.0},
        {"sku": "b", "qty": 1, "unit_price": 10.0},
    ]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_decimal_precision():
    """Test that subtotal rounds to 2 decimal places correctly."""
    items = [{"sku": "a", "qty": 3, "unit_price": 3.333}]
    # 3 * 3.333 = 9.999, should round to 10.0
    assert compute_subtotal(items) == 10.0
    
    items = [{"sku": "b", "qty": 2, "unit_price": 5.555}]
    # 2 * 5.555 = 11.11
    assert compute_subtotal(items) == 11.11


def test_compute_subtotal_string_qty_converted_to_int():
    """Test that string quantities are converted to int."""
    items = [{"sku": "a", "qty": "5", "unit_price": 2.0}]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_string_price_converted_to_float():
    """Test that string prices are converted to float."""
    items = [{"sku": "a", "qty": 2, "unit_price": "7.50"}]
    assert compute_subtotal(items) == 15.0


def test_compute_subtotal_rejects_negative_qty():
    """Test that negative quantities are rejected."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 5.0}])


def test_compute_subtotal_rejects_zero_qty():
    """Test that zero quantity is rejected."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 5.0}])


def test_compute_subtotal_rejects_negative_price():
    """Test that negative prices are rejected."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -1.0}])


def test_compute_subtotal_multiple_items_one_invalid_qty():
    """Test that computation fails if any item has invalid quantity."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 5.0},
        {"sku": "b", "qty": 0, "unit_price": 10.0},
    ]
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal(items)


def test_compute_subtotal_multiple_items_one_invalid_price():
    """Test that computation fails if any item has invalid price."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 5.0},
        {"sku": "b", "qty": 1, "unit_price": -10.0},
    ]
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal(items)


def test_compute_subtotal_large_numbers():
    """Test subtotal with large quantities and prices."""
    items = [{"sku": "a", "qty": 1000, "unit_price": 999.99}]
    assert compute_subtotal(items) == 999990.0


def test_compute_subtotal_float_qty_converted():
    """Test that float quantities are converted to int (truncated)."""
    items = [{"sku": "a", "qty": 5.9, "unit_price": 2.0}]
    # int(5.9) = 5, so 5 * 2.0 = 10.0
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_preserves_order_independence():
    """Test that item order doesn't affect the result."""
    items1 = [
        {"sku": "a", "qty": 1, "unit_price": 10.0},
        {"sku": "b", "qty": 2, "unit_price": 5.0},
    ]
    items2 = [
        {"sku": "b", "qty": 2, "unit_price": 5.0},
        {"sku": "a", "qty": 1, "unit_price": 10.0},
    ]
    assert compute_subtotal(items1) == compute_subtotal(items2) == 20.0
