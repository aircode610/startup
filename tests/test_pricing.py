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
# Additional comprehensive tests for apply_discount with int truncation
# ============================================================================


def test_apply_discount_premium_truncates_down():
    """Premium discount should truncate (not round) the result to an integer."""
    # 99.99 * 0.90 = 89.991, which should truncate to 89 (not round to 90)
    assert apply_discount(99.99, "premium") == 89


def test_apply_discount_premium_with_decimal_that_would_round_up():
    """Test cases where old rounding would go up but int truncation goes down."""
    # 105.56 * 0.90 = 95.004, would round to 95.00, truncates to 95
    assert apply_discount(105.56, "premium") == 95
    
    # 111.11 * 0.90 = 99.999, would round to 100.00, but truncates to 99
    assert apply_discount(111.11, "premium") == 99


def test_apply_discount_premium_with_various_decimals():
    """Test premium discount truncation with various decimal amounts."""
    # 50.50 * 0.90 = 45.45 -> truncates to 45
    assert apply_discount(50.50, "premium") == 45
    
    # 33.33 * 0.90 = 29.997 -> truncates to 29
    assert apply_discount(33.33, "premium") == 29
    
    # 77.77 * 0.90 = 69.993 -> truncates to 69
    assert apply_discount(77.77, "premium") == 69


def test_apply_discount_premium_small_amounts():
    """Test premium discount with small amounts where truncation matters."""
    # 1.11 * 0.90 = 0.999 -> truncates to 0
    assert apply_discount(1.11, "premium") == 0
    
    # 5.55 * 0.90 = 4.995 -> truncates to 4
    assert apply_discount(5.55, "premium") == 4
    
    # 10.01 * 0.90 = 9.009 -> truncates to 9
    assert apply_discount(10.01, "premium") == 9


def test_apply_discount_premium_zero_subtotal():
    """Premium discount on zero should return zero."""
    assert apply_discount(0.0, "premium") == 0


def test_apply_discount_premium_exact_integer_result():
    """When discount results in exact integer, no truncation loss."""
    # 200.0 * 0.90 = 180.0 -> 180
    assert apply_discount(200.0, "premium") == 180
    
    # 1000.0 * 0.90 = 900.0 -> 900
    assert apply_discount(1000.0, "premium") == 900


def test_apply_discount_premium_large_amounts():
    """Test premium discount with large subtotals."""
    # 9999.99 * 0.90 = 8999.991 -> truncates to 8999
    assert apply_discount(9999.99, "premium") == 8999
    
    # 10000.50 * 0.90 = 9000.45 -> truncates to 9000
    assert apply_discount(10000.50, "premium") == 9000


def test_apply_discount_premium_return_type_is_int():
    """Verify that premium discount returns an integer type."""
    result = apply_discount(100.0, "premium")
    assert isinstance(result, int)
    assert result == 90


def test_apply_discount_regular_maintains_rounding():
    """Regular tier should still use round() with 2 decimal places."""
    assert apply_discount(100.0, "regular") == 100.0
    assert apply_discount(99.99, "regular") == 99.99
    assert apply_discount(50.555, "regular") == 50.56  # rounds up
    assert apply_discount(50.554, "regular") == 50.55  # rounds down


def test_apply_discount_regular_return_type_is_float():
    """Verify that regular tier returns a float type."""
    result = apply_discount(100.0, "regular")
    assert isinstance(result, float)


def test_apply_discount_regular_zero_subtotal():
    """Regular discount on zero should return zero."""
    assert apply_discount(0.0, "regular") == 0.0


def test_apply_discount_regular_with_decimals():
    """Test regular tier with various decimal amounts."""
    assert apply_discount(33.333, "regular") == 33.33
    assert apply_discount(66.666, "regular") == 66.67
    assert apply_discount(99.995, "regular") == 100.0


def test_apply_discount_unknown_tier_treated_as_regular():
    """Unknown user tiers should be treated as regular (no discount)."""
    assert apply_discount(100.0, "gold") == 100.0
    assert apply_discount(100.0, "silver") == 100.0
    assert apply_discount(100.0, "vip") == 100.0
    assert apply_discount(100.0, "") == 100.0


def test_apply_discount_tier_case_sensitivity():
    """Tier names should be case-sensitive."""
    # Only lowercase "premium" gets discount
    assert apply_discount(100.0, "premium") == 90
    assert apply_discount(100.0, "Premium") == 100.0
    assert apply_discount(100.0, "PREMIUM") == 100.0


def test_apply_discount_boundary_values():
    """Test boundary values for subtotal."""
    # Very small positive value
    assert apply_discount(0.01, "premium") == 0  # 0.009 truncates to 0
    assert apply_discount(0.01, "regular") == 0.01
    
    # Just above zero
    assert apply_discount(0.001, "premium") == 0
    assert apply_discount(0.001, "regular") == 0.0


def test_apply_discount_rejects_negative_subtotal_regular():
    """Regular tier should also reject negative subtotals."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "regular")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-100.0, "regular")


def test_apply_discount_rejects_negative_subtotal_premium():
    """Premium tier should reject negative subtotals."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-1.0, "premium")
    
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-999.99, "premium")


def test_apply_discount_precision_loss_awareness():
    """Document that int truncation causes precision loss for premium users."""
    # This test documents the behavior change from round to int
    # 123.45 * 0.90 = 111.105
    # Old behavior: round(111.105, 2) = 111.11 (or 111.10 depending on banker's rounding)
    # New behavior: int(111.105) = 111
    result = apply_discount(123.45, "premium")
    assert result == 111
    # Premium users lose the fractional cents


# ============================================================================
# Additional comprehensive tests for compute_subtotal
# ============================================================================


def test_compute_subtotal_empty_list():
    """Empty items list should return 0.0."""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_single_item():
    """Single item calculation."""
    items = [{"sku": "x", "qty": 1, "unit_price": 9.99}]
    assert compute_subtotal(items) == 9.99


def test_compute_subtotal_multiple_same_price():
    """Multiple items with same price."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 5.0},
        {"sku": "b", "qty": 2, "unit_price": 5.0},
    ]
    assert compute_subtotal(items) == 25.0


def test_compute_subtotal_large_quantities():
    """Test with large quantities."""
    items = [{"sku": "bulk", "qty": 1000, "unit_price": 0.50}]
    assert compute_subtotal(items) == 500.0


def test_compute_subtotal_decimal_prices():
    """Test with various decimal unit prices."""
    items = [
        {"sku": "a", "qty": 1, "unit_price": 1.99},
        {"sku": "b", "qty": 1, "unit_price": 2.49},
        {"sku": "c", "qty": 1, "unit_price": 3.99},
    ]
    assert compute_subtotal(items) == 8.47


def test_compute_subtotal_rounding_precision():
    """Test that subtotal is rounded to 2 decimal places."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 3.333},
    ]
    # 3 * 3.333 = 9.999, rounds to 10.0
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_with_zero_price():
    """Items with zero price should be allowed."""
    items = [
        {"sku": "free", "qty": 5, "unit_price": 0.0},
        {"sku": "paid", "qty": 1, "unit_price": 10.0},
    ]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_rejects_negative_qty():
    """Negative quantities should raise ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 5.0}])


def test_compute_subtotal_rejects_zero_qty():
    """Zero quantity should raise ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 5.0}])


def test_compute_subtotal_rejects_negative_price():
    """Negative unit prices should raise ValueError."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -5.0}])


def test_compute_subtotal_rejects_invalid_qty_in_middle():
    """Invalid qty in middle of list should still raise."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 5.0},
        {"sku": "b", "qty": 0, "unit_price": 10.0},  # Invalid
        {"sku": "c", "qty": 1, "unit_price": 15.0},
    ]
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal(items)


def test_compute_subtotal_rejects_invalid_price_in_middle():
    """Invalid price in middle of list should still raise."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 5.0},
        {"sku": "b", "qty": 1, "unit_price": -10.0},  # Invalid
        {"sku": "c", "qty": 1, "unit_price": 15.0},
    ]
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal(items)


def test_compute_subtotal_type_coercion():
    """Function should handle string numbers via int/float coercion."""
    items = [
        {"sku": "a", "qty": "2", "unit_price": "5.5"},
        {"sku": "b", "qty": "3", "unit_price": "10.0"},
    ]
    # 2*5.5 + 3*10.0 = 11.0 + 30.0 = 41.0
    assert compute_subtotal(items) == 41.0


def test_compute_subtotal_float_qty_truncates():
    """Float quantities should truncate to int."""
    items = [{"sku": "a", "qty": 2.9, "unit_price": 10.0}]
    # int(2.9) = 2, so 2 * 10.0 = 20.0
    assert compute_subtotal(items) == 20.0


def test_compute_subtotal_handles_missing_keys():
    """Missing keys should raise KeyError."""
    with pytest.raises(KeyError):
        compute_subtotal([{"sku": "a", "qty": 1}])  # Missing unit_price
    
    with pytest.raises(KeyError):
        compute_subtotal([{"sku": "a", "unit_price": 5.0}])  # Missing qty


def test_compute_subtotal_multiple_items_complex():
    """Complex real-world scenario with multiple items."""
    items = [
        {"sku": "WIDGET-001", "qty": 5, "unit_price": 12.99},
        {"sku": "GADGET-202", "qty": 2, "unit_price": 49.99},
        {"sku": "TOOL-303", "qty": 1, "unit_price": 199.99},
        {"sku": "PART-404", "qty": 10, "unit_price": 2.50},
    ]
    # 5*12.99 + 2*49.99 + 1*199.99 + 10*2.50
    # = 64.95 + 99.98 + 199.99 + 25.0
    # = 389.92
    assert compute_subtotal(items) == 389.92
