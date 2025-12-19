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
# Additional comprehensive tests for apply_discount with int() truncation
# ============================================================================

def test_apply_discount_premium_truncates_decimals():
    """Test that premium discount truncates instead of rounding."""
    # 100.50 * 0.90 = 90.45 -> int() truncates to 90
    assert apply_discount(100.50, "premium") == 90
    

def test_apply_discount_premium_with_high_decimal():
    """Test truncation with .99 cents."""
    # 100.99 * 0.90 = 90.891 -> truncates to 90
    assert apply_discount(100.99, "premium") == 90


def test_apply_discount_premium_truncates_triple_nines():
    """Test case where result is very close to next integer."""
    # 111.11 * 0.90 = 99.999 -> truncates to 99, not 100
    assert apply_discount(111.11, "premium") == 99


def test_apply_discount_premium_small_amount_rounds_down_to_zero():
    """Test that small amounts can round down to 0."""
    # 1.0 * 0.90 = 0.9 -> truncates to 0
    assert apply_discount(1.0, "premium") == 0
    # 0.50 * 0.90 = 0.45 -> truncates to 0
    assert apply_discount(0.50, "premium") == 0


def test_apply_discount_premium_zero_subtotal():
    """Test that zero subtotal returns zero."""
    assert apply_discount(0.0, "premium") == 0


def test_apply_discount_premium_large_amount():
    """Test with large dollar amounts."""
    # 10000.00 * 0.90 = 9000.00
    assert apply_discount(10000.00, "premium") == 9000
    # 9999.99 * 0.90 = 8999.991 -> truncates to 8999
    assert apply_discount(9999.99, "premium") == 8999


def test_apply_discount_premium_realistic_cart_values():
    """Test with realistic shopping cart amounts."""
    # $49.99 cart: 49.99 * 0.90 = 44.991 -> 44
    assert apply_discount(49.99, "premium") == 44
    # $75.50 cart: 75.50 * 0.90 = 67.95 -> 67
    assert apply_discount(75.50, "premium") == 67
    # $123.45 cart: 123.45 * 0.90 = 111.105 -> 111
    assert apply_discount(123.45, "premium") == 111


def test_apply_discount_premium_returns_integer_type():
    """Verify that premium discount returns an integer, not a float."""
    result = apply_discount(100.0, "premium")
    assert isinstance(result, int)
    assert result == 90


def test_apply_discount_premium_penny_amounts():
    """Test with amounts that have many decimal places."""
    # 10.55 * 0.90 = 9.495 -> truncates to 9
    assert apply_discount(10.55, "premium") == 9
    # 33.33 * 0.90 = 29.997 -> truncates to 29
    assert apply_discount(33.33, "premium") == 29


def test_apply_discount_regular_returns_float_with_two_decimals():
    """Test that regular tier returns properly rounded float."""
    assert apply_discount(100.456, "regular") == 100.46
    assert apply_discount(99.994, "regular") == 99.99
    assert apply_discount(50.555, "regular") == 50.56


def test_apply_discount_regular_zero_subtotal():
    """Test regular tier with zero subtotal."""
    assert apply_discount(0.0, "regular") == 0.0


def test_apply_discount_regular_small_amounts():
    """Test regular tier preserves small amounts correctly."""
    assert apply_discount(0.01, "regular") == 0.01
    assert apply_discount(0.99, "regular") == 0.99
    assert apply_discount(1.50, "regular") == 1.50


def test_apply_discount_unknown_tier_treated_as_regular():
    """Test that unknown tiers are treated like regular (no discount)."""
    assert apply_discount(100.0, "gold") == 100.0
    assert apply_discount(100.0, "unknown") == 100.0
    assert apply_discount(50.50, "") == 50.50


def test_apply_discount_case_sensitive_tier():
    """Test that tier matching is case-sensitive."""
    # "Premium" (capital P) should be treated as regular
    assert apply_discount(100.0, "Premium") == 100.0
    assert apply_discount(100.0, "PREMIUM") == 100.0


def test_apply_discount_rejects_negative_subtotal_premium():
    """Test that negative subtotals raise ValueError for premium."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "premium")


def test_apply_discount_rejects_negative_subtotal_regular():
    """Test that negative subtotals raise ValueError for regular."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-10.0, "regular")


def test_apply_discount_rejects_large_negative():
    """Test with large negative values."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-999999.99, "premium")


# ============================================================================
# Additional comprehensive tests for compute_subtotal
# ============================================================================

def test_compute_subtotal_empty_list():
    """Test that empty cart returns 0."""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_single_item():
    """Test with a single item."""
    items = [{"sku": "x", "qty": 1, "unit_price": 5.99}]
    assert compute_subtotal(items) == 5.99


def test_compute_subtotal_multiple_same_items():
    """Test quantity multiplication."""
    items = [{"sku": "a", "qty": 5, "unit_price": 10.0}]
    assert compute_subtotal(items) == 50.0


def test_compute_subtotal_rounds_to_two_decimals():
    """Test that subtotal is rounded to 2 decimal places."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 3.333},  # 9.999
    ]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_precision_with_multiple_items():
    """Test rounding with multiple items that accumulate decimals."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 1.115},  # 2.23
        {"sku": "b", "qty": 3, "unit_price": 2.226},  # 6.678
    ]
    # Total: 2.23 + 6.678 = 8.908 -> rounds to 8.91
    assert compute_subtotal(items) == 8.91


def test_compute_subtotal_zero_price_items():
    """Test items with zero price (e.g., free items)."""
    items = [
        {"sku": "a", "qty": 1, "unit_price": 10.0},
        {"sku": "free", "qty": 2, "unit_price": 0.0},
    ]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_large_quantities():
    """Test with large quantity values."""
    items = [{"sku": "bulk", "qty": 1000, "unit_price": 0.50}]
    assert compute_subtotal(items) == 500.0


def test_compute_subtotal_large_prices():
    """Test with expensive items."""
    items = [{"sku": "expensive", "qty": 1, "unit_price": 9999.99}]
    assert compute_subtotal(items) == 9999.99


def test_compute_subtotal_many_items():
    """Test with many different items."""
    items = [
        {"sku": f"item_{i}", "qty": 1, "unit_price": 1.0}
        for i in range(50)
    ]
    assert compute_subtotal(items) == 50.0


def test_compute_subtotal_rejects_negative_qty():
    """Test that negative quantities raise ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 10.0}])


def test_compute_subtotal_rejects_zero_qty():
    """Test that zero quantity raises ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 10.0}])


def test_compute_subtotal_rejects_negative_price():
    """Test that negative prices raise ValueError."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -5.0}])


def test_compute_subtotal_handles_string_numbers():
    """Test that string representations of numbers are converted."""
    items = [
        {"sku": "a", "qty": "2", "unit_price": "5.50"},
    ]
    # Function converts to int/float, so this should work
    assert compute_subtotal(items) == 11.0


def test_compute_subtotal_mixed_valid_items():
    """Test complex cart with various item types."""
    items = [
        {"sku": "widget", "qty": 3, "unit_price": 12.99},      # 38.97
        {"sku": "gadget", "qty": 1, "unit_price": 99.99},      # 99.99
        {"sku": "trinket", "qty": 10, "unit_price": 0.50},     # 5.00
        {"sku": "bonus", "qty": 1, "unit_price": 0.0},         # 0.00
    ]
    # Total: 38.97 + 99.99 + 5.00 + 0.00 = 143.96
    assert compute_subtotal(items) == 143.96


def test_compute_subtotal_fractional_cents():
    """Test items with prices that have many decimal places."""
    items = [
        {"sku": "a", "qty": 7, "unit_price": 1.4285714},  # 9.9999998
    ]
    # Should round to 10.0
    assert compute_subtotal(items) == 10.0


# ============================================================================
# Integration tests: compute_subtotal + apply_discount
# ============================================================================

def test_integration_premium_discount_on_computed_subtotal():
    """Test complete flow: compute subtotal then apply premium discount."""
    items = [
        {"sku": "a", "qty": 2, "unit_price": 25.0},   # 50.0
        {"sku": "b", "qty": 1, "unit_price": 50.0},   # 50.0
    ]
    subtotal = compute_subtotal(items)
    assert subtotal == 100.0
    
    final = apply_discount(subtotal, "premium")
    # 100.0 * 0.9 = 90.0 -> int = 90
    assert final == 90


def test_integration_regular_discount_on_computed_subtotal():
    """Test complete flow: compute subtotal then apply regular discount."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 15.99},  # 47.97
    ]
    subtotal = compute_subtotal(items)
    assert subtotal == 47.97
    
    final = apply_discount(subtotal, "regular")
    assert final == 47.97  # No discount


def test_integration_premium_loses_cents_due_to_truncation():
    """Test that premium users lose fractional cents due to int() truncation."""
    items = [
        {"sku": "a", "qty": 1, "unit_price": 99.99},  # 99.99
    ]
    subtotal = compute_subtotal(items)
    assert subtotal == 99.99
    
    final = apply_discount(subtotal, "premium")
    # 99.99 * 0.9 = 89.991 -> int() = 89 (loses $0.991)
    assert final == 89


def test_integration_small_cart_premium_discount_to_zero():
    """Test that very small carts can discount down to zero."""
    items = [
        {"sku": "cheap", "qty": 1, "unit_price": 1.00},
    ]
    subtotal = compute_subtotal(items)
    assert subtotal == 1.0
    
    final = apply_discount(subtotal, "premium")
    # 1.0 * 0.9 = 0.9 -> int() = 0
    assert final == 0
