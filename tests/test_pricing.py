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
# Additional comprehensive tests for apply_discount
# ============================================================================

def test_apply_discount_premium_with_decimal_truncation():
    """Test that premium discount uses int() truncation, not rounding."""
    # 99.99 * 0.90 = 89.991, which rounds to 89.99 but truncates to 89
    assert apply_discount(99.99, "premium") == 89


def test_apply_discount_premium_truncates_down_not_round():
    """Verify truncation behavior: 105.55 * 0.90 = 94.995 -> 94, not 95."""
    assert apply_discount(105.55, "premium") == 94


def test_apply_discount_premium_small_amount():
    """Test premium discount with small amounts."""
    # 5.0 * 0.90 = 4.5 -> truncates to 4
    assert apply_discount(5.0, "premium") == 4


def test_apply_discount_premium_zero():
    """Test premium discount with zero subtotal."""
    assert apply_discount(0.0, "premium") == 0


def test_apply_discount_premium_very_small_decimal():
    """Test premium discount with very small decimal values."""
    # 1.11 * 0.90 = 0.999 -> truncates to 0
    assert apply_discount(1.11, "premium") == 0


def test_apply_discount_premium_large_amount():
    """Test premium discount with large amounts."""
    # 10000.0 * 0.90 = 9000.0
    assert apply_discount(10000.0, "premium") == 9000


def test_apply_discount_premium_cents_edge_case():
    """Test cases where cents after discount would be truncated."""
    # 111.11 * 0.90 = 99.999 -> 99
    assert apply_discount(111.11, "premium") == 99
    # 222.22 * 0.90 = 199.998 -> 199
    assert apply_discount(222.22, "premium") == 199


def test_apply_discount_premium_exact_dollar():
    """Test premium discount with exact dollar amounts."""
    assert apply_discount(50.0, "premium") == 45
    assert apply_discount(200.0, "premium") == 180


def test_apply_discount_regular_with_decimals():
    """Test regular tier rounds to 2 decimal places."""
    assert apply_discount(99.999, "regular") == 100.0
    assert apply_discount(50.555, "regular") == 50.56
    assert apply_discount(25.444, "regular") == 25.44


def test_apply_discount_regular_zero():
    """Test regular discount with zero subtotal."""
    assert apply_discount(0.0, "regular") == 0.0


def test_apply_discount_regular_small_decimal():
    """Test regular tier with small decimal values."""
    assert apply_discount(0.01, "regular") == 0.01
    assert apply_discount(0.001, "regular") == 0.0


def test_apply_discount_regular_large_amount():
    """Test regular tier with large amounts."""
    assert apply_discount(99999.99, "regular") == 99999.99


def test_apply_discount_unknown_tier():
    """Test with unknown user tier (should act like regular)."""
    assert apply_discount(100.0, "gold") == 100.0
    assert apply_discount(50.0, "silver") == 50.0
    assert apply_discount(75.0, "") == 75.0


def test_apply_discount_case_sensitivity():
    """Test that user_tier comparison is case-sensitive."""
    # "Premium" (capitalized) should not match "premium"
    assert apply_discount(100.0, "Premium") == 100.0
    assert apply_discount(100.0, "PREMIUM") == 100.0


def test_apply_discount_premium_fractional_cents():
    """Test premium discount behavior with various fractional cents."""
    # 33.33 * 0.90 = 29.997 -> 29
    assert apply_discount(33.33, "premium") == 29
    # 66.67 * 0.90 = 60.003 -> 60
    assert apply_discount(66.67, "premium") == 60
    # 123.45 * 0.90 = 111.105 -> 111
    assert apply_discount(123.45, "premium") == 111


def test_apply_discount_negative_subtotal_with_regular():
    """Test that negative subtotal raises ValueError for regular tier too."""
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-0.01, "regular")
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        apply_discount(-100.0, "regular")


def test_apply_discount_boundary_near_zero():
    """Test boundary conditions near zero."""
    assert apply_discount(0.0, "premium") == 0
    assert apply_discount(0.0, "regular") == 0.0
    # Very small positive value
    assert apply_discount(0.001, "premium") == 0


# ============================================================================
# Additional comprehensive tests for compute_subtotal
# ============================================================================

def test_compute_subtotal_single_item():
    """Test subtotal calculation with a single item."""
    items = [{"sku": "x", "qty": 1, "unit_price": 9.99}]
    assert compute_subtotal(items) == 9.99


def test_compute_subtotal_multiple_items_with_decimals():
    """Test subtotal with multiple items having decimal prices."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 1.11},
        {"sku": "b", "qty": 2, "unit_price": 2.22},
        {"sku": "c", "qty": 1, "unit_price": 5.55},
    ]
    # 3*1.11 + 2*2.22 + 1*5.55 = 3.33 + 4.44 + 5.55 = 13.32
    assert compute_subtotal(items) == 13.32


def test_compute_subtotal_empty_list():
    """Test subtotal with empty items list."""
    assert compute_subtotal([]) == 0.0


def test_compute_subtotal_zero_price():
    """Test subtotal with zero unit price (free items)."""
    items = [{"sku": "free", "qty": 5, "unit_price": 0.0}]
    assert compute_subtotal(items) == 0.0


def test_compute_subtotal_mixed_zero_and_paid():
    """Test subtotal with mix of free and paid items."""
    items = [
        {"sku": "paid", "qty": 2, "unit_price": 10.0},
        {"sku": "free", "qty": 3, "unit_price": 0.0},
    ]
    assert compute_subtotal(items) == 20.0


def test_compute_subtotal_large_quantity():
    """Test subtotal with large quantities."""
    items = [{"sku": "bulk", "qty": 1000, "unit_price": 0.99}]
    assert compute_subtotal(items) == 990.0


def test_compute_subtotal_large_price():
    """Test subtotal with large unit prices."""
    items = [{"sku": "expensive", "qty": 1, "unit_price": 9999.99}]
    assert compute_subtotal(items) == 9999.99


def test_compute_subtotal_rounding_precision():
    """Test that subtotal is rounded to 2 decimal places."""
    items = [{"sku": "a", "qty": 3, "unit_price": 0.333}]
    # 3 * 0.333 = 0.999, should round to 1.00
    assert compute_subtotal(items) == 1.0


def test_compute_subtotal_string_convertible_qty():
    """Test that qty is converted from string if possible."""
    items = [{"sku": "a", "qty": "5", "unit_price": 2.0}]
    assert compute_subtotal(items) == 10.0


def test_compute_subtotal_string_convertible_price():
    """Test that unit_price is converted from string if possible."""
    items = [{"sku": "a", "qty": 2, "unit_price": "7.50"}]
    assert compute_subtotal(items) == 15.0


def test_compute_subtotal_negative_qty():
    """Test that negative quantity raises ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 5.0}])


def test_compute_subtotal_negative_price():
    """Test that negative unit_price raises ValueError."""
    with pytest.raises(ValueError, match="unit_price must be non-negative"):
        compute_subtotal([{"sku": "a", "qty": 2, "unit_price": -1.0}])


def test_compute_subtotal_zero_qty():
    """Test that zero quantity raises ValueError."""
    with pytest.raises(ValueError, match="qty must be positive"):
        compute_subtotal([{"sku": "a", "qty": 0, "unit_price": 10.0}])


def test_compute_subtotal_float_qty():
    """Test that float quantities are converted to int (truncated)."""
    items = [{"sku": "a", "qty": 3.9, "unit_price": 2.0}]
    # qty is cast to int, so 3.9 -> 3
    assert compute_subtotal(items) == 6.0


def test_compute_subtotal_multiple_skus():
    """Test subtotal with diverse SKUs and values."""
    items = [
        {"sku": "WIDGET-001", "qty": 10, "unit_price": 1.99},
        {"sku": "GADGET-002", "qty": 5, "unit_price": 3.49},
        {"sku": "DOOHICKEY-003", "qty": 1, "unit_price": 25.00},
    ]
    # 10*1.99 + 5*3.49 + 1*25.00 = 19.90 + 17.45 + 25.00 = 62.35
    assert compute_subtotal(items) == 62.35


def test_compute_subtotal_precision_edge_case():
    """Test floating point precision edge cases."""
    items = [
        {"sku": "a", "qty": 3, "unit_price": 0.1},
    ]
    # 3 * 0.1 might be 0.30000000000000004 in floating point
    # but should round to 0.30
    assert compute_subtotal(items) == 0.30


def test_compute_subtotal_invalid_qty_type():
    """Test that non-numeric qty raises appropriate error."""
    with pytest.raises((ValueError, TypeError)):
        compute_subtotal([{"sku": "a", "qty": "invalid", "unit_price": 5.0}])


def test_compute_subtotal_invalid_price_type():
    """Test that non-numeric unit_price raises appropriate error."""
    with pytest.raises((ValueError, TypeError)):
        compute_subtotal([{"sku": "a", "qty": 2, "unit_price": "invalid"}])


def test_compute_subtotal_missing_keys():
    """Test that missing required keys raise KeyError."""
    with pytest.raises(KeyError):
        compute_subtotal([{"sku": "a", "qty": 2}])  # missing unit_price
    with pytest.raises(KeyError):
        compute_subtotal([{"sku": "a", "unit_price": 5.0}])  # missing qty


def test_compute_subtotal_very_small_values():
    """Test computation with very small decimal values."""
    items = [{"sku": "tiny", "qty": 1, "unit_price": 0.01}]
    assert compute_subtotal(items) == 0.01


def test_compute_subtotal_accumulation_accuracy():
    """Test that multiple items accumulate correctly with proper rounding."""
    items = [
        {"sku": "a", "qty": 1, "unit_price": 0.01},
        {"sku": "b", "qty": 1, "unit_price": 0.02},
        {"sku": "c", "qty": 1, "unit_price": 0.03},
    ]
    assert compute_subtotal(items) == 0.06
