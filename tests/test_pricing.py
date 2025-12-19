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
# Comprehensive tests for apply_discount with int() truncation behavior
# Testing the change from round(subtotal * 0.90, 2) to int(subtotal * 0.90)
# ============================================================================


class TestApplyDiscountPremiumTruncation:
    """Test suite for premium discount truncation behavior using int()"""

    def test_premium_discount_truncates_not_rounds_down(self):
        """Premium discount should truncate (90.99 -> 90), not round (90.99 -> 91)"""
        # 101.10 * 0.90 = 90.99
        # With int(): 90.99 -> 90 (truncate)
        # With round(): 90.99 -> 90.99 (keep decimals)
        assert apply_discount(101.10, "premium") == 90

    def test_premium_discount_truncates_small_decimals(self):
        """Small decimal fractions should be truncated"""
        # 100.11 * 0.90 = 90.099
        assert apply_discount(100.11, "premium") == 90

    def test_premium_discount_truncates_large_decimals(self):
        """Large decimal fractions (.99) should be truncated, not rounded up"""
        # 111.11 * 0.90 = 99.999
        # int() truncates to 99, not 100
        assert apply_discount(111.11, "premium") == 99

    def test_premium_discount_exact_integer_result(self):
        """When result is exact integer, no truncation effect"""
        # 100.0 * 0.90 = 90.0
        assert apply_discount(100.0, "premium") == 90

    def test_premium_discount_zero_subtotal(self):
        """Zero subtotal should return 0"""
        assert apply_discount(0.0, "premium") == 0

    def test_premium_discount_very_small_amount(self):
        """Very small amounts should truncate to 0"""
        # 0.50 * 0.90 = 0.45 -> truncates to 0
        assert apply_discount(0.50, "premium") == 0

    def test_premium_discount_one_dollar(self):
        """One dollar with discount"""
        # 1.00 * 0.90 = 0.90 -> truncates to 0
        assert apply_discount(1.00, "premium") == 0

    def test_premium_discount_just_over_one_dollar(self):
        """Amount that results in > 1 after discount"""
        # 1.12 * 0.90 = 1.008 -> truncates to 1
        assert apply_discount(1.12, "premium") == 1

    def test_premium_discount_large_amount(self):
        """Large amounts should truncate properly"""
        # 10000.00 * 0.90 = 9000.0
        assert apply_discount(10000.00, "premium") == 9000

    def test_premium_discount_large_amount_with_decimals(self):
        """Large amounts with decimals"""
        # 9999.99 * 0.90 = 8999.991 -> truncates to 8999
        assert apply_discount(9999.99, "premium") == 8999

    def test_premium_discount_edge_case_rounds_vs_truncates(self):
        """Demonstrate difference between round() and int()"""
        # 100.56 * 0.90 = 90.504
        # round(90.504, 2) would give 90.5
        # int(90.504) gives 90
        assert apply_discount(100.56, "premium") == 90

    def test_premium_discount_many_decimal_places(self):
        """Input with many decimal places"""
        # 123.456789 * 0.90 = 111.1111101 -> truncates to 111
        assert apply_discount(123.456789, "premium") == 111

    def test_premium_discount_cents_precision(self):
        """Common retail prices ending in .99"""
        # 19.99 * 0.90 = 17.991 -> truncates to 17
        assert apply_discount(19.99, "premium") == 17
        # 29.99 * 0.90 = 26.991 -> truncates to 26
        assert apply_discount(29.99, "premium") == 26
        # 99.99 * 0.90 = 89.991 -> truncates to 89
        assert apply_discount(99.99, "premium") == 89

    def test_premium_discount_loses_cents(self):
        """Demonstrates money loss due to truncation"""
        # Customer pays for 50.00, after 10% discount should be 45.00
        # But if calculated from 50.55: 50.55 * 0.90 = 45.495 -> truncates to 45
        # Lost: 0.495
        assert apply_discount(50.55, "premium") == 45


class TestApplyDiscountRegularUserBehavior:
    """Test suite for regular user discount (no discount, uses round())"""

    def test_regular_user_no_discount_rounds_to_2_decimals(self):
        """Regular users get no discount, amount rounded to 2 decimals"""
        assert apply_discount(100.0, "regular") == 100.0

    def test_regular_user_preserves_2_decimal_places(self):
        """Regular user amounts are rounded to 2 decimal places"""
        assert apply_discount(100.123, "regular") == 100.12

    def test_regular_user_rounds_up_properly(self):
        """Regular user amounts round up when appropriate"""
        assert apply_discount(100.126, "regular") == 100.13

    def test_regular_user_many_decimals(self):
        """Many decimal places should round to 2"""
        assert apply_discount(99.999, "regular") == 100.0

    def test_regular_user_zero(self):
        """Zero for regular user"""
        assert apply_discount(0.0, "regular") == 0.0

    def test_regular_user_small_amount(self):
        """Small amounts for regular users"""
        assert apply_discount(0.01, "regular") == 0.01


class TestApplyDiscountEdgeCasesAndErrors:
    """Test edge cases, error conditions, and boundary values"""

    def test_negative_subtotal_raises_error(self):
        """Negative subtotal should raise ValueError"""
        with pytest.raises(ValueError, match="subtotal must be non-negative"):
            apply_discount(-0.01, "premium")

    def test_negative_subtotal_regular_raises_error(self):
        """Negative subtotal for regular user should raise ValueError"""
        with pytest.raises(ValueError, match="subtotal must be non-negative"):
            apply_discount(-1.0, "regular")

    def test_negative_large_subtotal_raises_error(self):
        """Large negative subtotal should raise ValueError"""
        with pytest.raises(ValueError, match="subtotal must be non-negative"):
            apply_discount(-1000.0, "premium")

    def test_unknown_tier_no_discount(self):
        """Unknown tier should behave like regular (no discount)"""
        # Any tier that's not "premium" gets no discount
        assert apply_discount(100.0, "gold") == 100.0
        assert apply_discount(100.0, "basic") == 100.0
        assert apply_discount(100.0, "") == 100.0

    def test_case_sensitive_tier(self):
        """Tier matching is case-sensitive"""
        # "Premium" (capital P) is not "premium"
        assert apply_discount(100.0, "Premium") == 100.0
        assert apply_discount(100.0, "PREMIUM") == 100.0

    def test_float_precision_edge_cases(self):
        """Test floating point precision edge cases"""
        # 0.1 + 0.2 = 0.30000000000000004 in floating point
        subtotal = 0.1 + 0.2  # = 0.30000000000000004
        # For premium: 0.30000000000000004 * 0.90 = 0.27... -> truncates to 0
        assert apply_discount(subtotal, "premium") == 0
        # For regular: rounds to 0.3
        assert apply_discount(subtotal, "regular") == 0.3


class TestApplyDiscountReturnTypes:
    """Test return types and type consistency"""

    def test_premium_returns_int_type(self):
        """Premium discount returns int type"""
        result = apply_discount(100.0, "premium")
        assert isinstance(result, int)
        assert result == 90

    def test_regular_returns_float_type(self):
        """Regular user returns float type (from round())"""
        result = apply_discount(100.0, "regular")
        assert isinstance(result, float)
        assert result == 100.0

    def test_premium_always_integer_no_decimals(self):
        """Premium results are always whole numbers"""
        result = apply_discount(123.45, "premium")
        assert result == int(result)
        assert result == 111


class TestApplyDiscountComparisonWithOldBehavior:
    """Tests that highlight differences from old round() behavior"""

    def test_old_vs_new_behavior_documentation(self):
        """Document the behavior change from round() to int()"""
        # OLD BEHAVIOR: round(subtotal * 0.90, 2)
        # NEW BEHAVIOR: int(subtotal * 0.90)
        
        # Example 1: 100.00 * 0.90 = 90.00
        # OLD: round(90.00, 2) = 90.00
        # NEW: int(90.00) = 90
        assert apply_discount(100.00, "premium") == 90
        
        # Example 2: 100.55 * 0.90 = 90.495
        # OLD: round(90.495, 2) = 90.50  (would round to 2 decimals)
        # NEW: int(90.495) = 90  (truncates all decimals)
        assert apply_discount(100.55, "premium") == 90

    def test_monetary_loss_from_truncation(self):
        """Quantify potential money lost due to truncation"""
        # With 99.99 item:
        # Expected discount: 99.99 * 0.10 = 9.999
        # Discounted price should be: 99.99 - 9.999 = 89.991
        # OLD: round(89.991, 2) = 89.99
        # NEW: int(89.991) = 89
        # Customer "gains" 0.99 compared to proper rounding
        assert apply_discount(99.99, "premium") == 89

    def test_sub_dollar_amounts_truncate_to_zero(self):
        """Sub-dollar amounts after discount truncate to 0"""
        # Any amount < $1.12 will discount to < $1.00 and truncate to $0
        assert apply_discount(1.00, "premium") == 0  # 0.90 -> 0
        assert apply_discount(1.10, "premium") == 0  # 0.99 -> 0
        assert apply_discount(1.11, "premium") == 0  # 0.999 -> 0


class TestComputeSubtotalComprehensive:
    """Additional comprehensive tests for compute_subtotal"""

    def test_empty_items_list(self):
        """Empty items list should return 0.0"""
        assert compute_subtotal([]) == 0.0

    def test_single_item(self):
        """Single item calculation"""
        items = [{"sku": "x", "qty": 1, "unit_price": 5.50}]
        assert compute_subtotal(items) == 5.50

    def test_multiple_items_with_rounding(self):
        """Multiple items with proper rounding"""
        items = [
            {"sku": "a", "qty": 3, "unit_price": 1.11},  # 3.33
            {"sku": "b", "qty": 2, "unit_price": 2.22},  # 4.44
        ]
        # Total: 7.77
        assert compute_subtotal(items) == 7.77

    def test_large_quantities(self):
        """Large quantities"""
        items = [{"sku": "bulk", "qty": 1000, "unit_price": 0.99}]
        assert compute_subtotal(items) == 990.0

    def test_high_precision_prices(self):
        """High precision unit prices"""
        items = [{"sku": "a", "qty": 1, "unit_price": 10.12345}]
        # Should round to 10.12
        assert compute_subtotal(items) == 10.12

    def test_zero_price_valid(self):
        """Zero price is valid (free item)"""
        items = [{"sku": "free", "qty": 1, "unit_price": 0.0}]
        assert compute_subtotal(items) == 0.0

    def test_negative_quantity_raises_error(self):
        """Negative quantity should raise ValueError"""
        with pytest.raises(ValueError, match="qty must be positive"):
            compute_subtotal([{"sku": "a", "qty": -1, "unit_price": 5.0}])

    def test_negative_price_raises_error(self):
        """Negative price should raise ValueError"""
        with pytest.raises(ValueError, match="unit_price must be non-negative"):
            compute_subtotal([{"sku": "a", "qty": 1, "unit_price": -5.0}])

    def test_fractional_quantity_converted_to_int(self):
        """Fractional quantity is converted to int"""
        # qty is converted with int(), so 2.9 becomes 2
        items = [{"sku": "a", "qty": 2.9, "unit_price": 5.0}]
        # int(2.9) = 2, so 2 * 5.0 = 10.0
        assert compute_subtotal(items) == 10.0

    def test_string_quantity_and_price(self):
        """String values should be converted"""
        items = [{"sku": "a", "qty": "3", "unit_price": "4.50"}]
        # 3 * 4.50 = 13.50
        assert compute_subtotal(items) == 13.5

    def test_mixed_types_in_items(self):
        """Mixed int/float/string types"""
        items = [
            {"sku": "a", "qty": 2, "unit_price": 3.5},      # int, float
            {"sku": "b", "qty": "3", "unit_price": "2.0"},  # string, string
            {"sku": "c", "qty": 1.5, "unit_price": 10},     # float, int
        ]
        # 2*3.5 + 3*2.0 + 1*10 = 7.0 + 6.0 + 10.0 = 23.0
        assert compute_subtotal(items) == 23.0


class TestIntegrationWithCheckout:
    """Integration tests considering how apply_discount is used in checkout"""

    def test_premium_checkout_total_is_integer(self):
        """When used in checkout, premium total should be integer"""
        from app.cart import checkout
        
        result = checkout(
            authorization_header="Bearer user_premium",
            items=[{"sku": "item", "qty": 1, "unit_price": 100.0}],
            user_tier="premium"
        )
        assert result.authorized is True
        assert result.subtotal == 100.0
        assert result.total == 90  # int, not 90.0
        assert isinstance(result.total, int)

    def test_premium_checkout_with_decimal_loss(self):
        """Premium checkout loses decimal cents"""
        from app.cart import checkout
        
        result = checkout(
            authorization_header="Bearer user_123",
            items=[{"sku": "item", "qty": 1, "unit_price": 19.99}],
            user_tier="premium"
        )
        assert result.authorized is True
        assert result.subtotal == 19.99
        # 19.99 * 0.90 = 17.991 -> truncates to 17
        assert result.total == 17

    def test_regular_checkout_preserves_decimals(self):
        """Regular user checkout preserves decimal precision"""
        from app.cart import checkout
        
        result = checkout(
            authorization_header="Bearer user_regular",
            items=[{"sku": "item", "qty": 1, "unit_price": 19.99}],
            user_tier="regular"
        )
        assert result.authorized is True
        assert result.subtotal == 19.99
        assert result.total == 19.99
        assert isinstance(result.total, float)
