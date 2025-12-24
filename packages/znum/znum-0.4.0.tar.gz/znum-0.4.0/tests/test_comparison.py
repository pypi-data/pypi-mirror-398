"""
Comprehensive E2E tests for Znum comparison operations.

These tests verify that all comparison operations produce correct results.
The expected values were generated from the current (ground truth) implementation.
"""

import pytest
from znum import Znum


class TestZnumEquality:
    """Tests for Znum equality comparison."""

    def test_equality_self(self):
        """Test that a Z-number equals itself."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 == z1

    def test_equality_identical_values(self):
        """Test that two Z-numbers with identical values are equal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 == z4

    def test_equality_different_A(self):
        """Test that Z-numbers with different A values are not equal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        assert not (z1 == z2)

    def test_equality_different_values(self):
        """Test that Z-numbers with different values are not equal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        assert not (z1 == z3)


class TestZnumGreaterThan:
    """Tests for Znum greater than comparison."""

    def test_greater_than_self(self):
        """Test that a Z-number is not greater than itself."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert not (z1 > z1)

    def test_greater_than_larger_A(self):
        """Test comparison where second has larger A values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        assert z2 > z1
        assert not (z1 > z2)

    def test_greater_than_smaller_values(self):
        """Test comparison with smaller Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        assert z1 > z3
        assert not (z3 > z1)

    def test_greater_than_chain(self):
        """Test transitive greater than relationship."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        assert z2 > z3  # If z2 > z1 and z1 > z3, then z2 > z3


class TestZnumLessThan:
    """Tests for Znum less than comparison."""

    def test_less_than_self(self):
        """Test that a Z-number is not less than itself."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert not (z1 < z1)

    def test_less_than_larger_values(self):
        """Test comparison with larger Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        assert z1 < z2
        assert not (z2 < z1)

    def test_less_than_smaller_values(self):
        """Test comparison with smaller Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        assert z3 < z1
        assert not (z1 < z3)


class TestZnumGreaterThanOrEqual:
    """Tests for Znum greater than or equal comparison."""

    def test_greater_than_or_equal_self(self):
        """Test that a Z-number is >= itself."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 >= z1

    def test_greater_than_or_equal_identical(self):
        """Test >= with identical Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 >= z4

    def test_greater_than_or_equal_larger(self):
        """Test >= with larger Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        assert z2 >= z1
        assert not (z1 >= z2)

    def test_greater_than_or_equal_smaller(self):
        """Test >= with smaller Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        assert z1 >= z3


class TestZnumLessThanOrEqual:
    """Tests for Znum less than or equal comparison."""

    def test_less_than_or_equal_self(self):
        """Test that a Z-number is <= itself."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 <= z1

    def test_less_than_or_equal_identical(self):
        """Test <= with identical Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 <= z4

    def test_less_than_or_equal_larger(self):
        """Test <= with larger Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        assert z1 <= z2
        assert not (z2 <= z1)

    def test_less_than_or_equal_smaller(self):
        """Test <= with smaller Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        assert z3 <= z1


class TestZnumComplexComparisons:
    """Tests for more complex comparison scenarios."""

    def test_overlapping_znums(self):
        """Test comparison with overlapping Z-number ranges."""
        z5 = Znum(A=[1.5, 2.5, 3.5, 4.5], B=[0.15, 0.25, 0.35, 0.45])
        z6 = Znum(A=[1, 2.5, 3, 4.5], B=[0.1, 0.25, 0.3, 0.45])
        assert z5 > z6
        assert not (z5 < z6)
        assert not (z5 == z6)

    def test_negative_znum_comparisons(self):
        """Test comparisons with negative Z-numbers."""
        z_neg1 = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        z_neg2 = Znum(A=[-2, -1, 0, 1], B=[0.15, 0.25, 0.35, 0.45])
        assert not (z_neg1 > z_neg2)
        assert z_neg1 < z_neg2

    def test_negative_vs_positive(self):
        """Test comparison between negative and positive Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z_neg1 = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        z_neg2 = Znum(A=[-2, -1, 0, 1], B=[0.15, 0.25, 0.35, 0.45])

        assert not (z_neg2 > z1)
        assert z_neg1 < z1

    def test_comparison_consistency(self):
        """Test that comparisons are consistent (if a > b, then b < a)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        # If z2 > z1, then z1 < z2
        assert (z2 > z1) == (z1 < z2)
        # If z1 > z3, then z3 < z1
        assert (z1 > z3) == (z3 < z1)
        # If z2 > z3, then z3 < z2
        assert (z2 > z3) == (z3 < z2)

    def test_equality_consistency(self):
        """Test that equality is reflexive and symmetric."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        # Reflexive
        assert z1 == z1
        # Symmetric
        assert (z1 == z4) == (z4 == z1)


class TestZnumSortingWithComparisons:
    """Tests to verify sorting works correctly with Z-number comparisons."""

    def test_sort_znums_ascending(self):
        """Test that Z-numbers can be sorted in ascending order."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        znums = [z2, z1, z3]
        sorted_znums = sorted(znums)

        # Should be sorted as z3 < z1 < z2
        assert sorted_znums[0] == z3
        assert sorted_znums[1] == z1
        assert sorted_znums[2] == z2

    def test_sort_znums_descending(self):
        """Test that Z-numbers can be sorted in descending order."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        znums = [z3, z1, z2]
        sorted_znums = sorted(znums, reverse=True)

        # Should be sorted as z2 > z1 > z3
        assert sorted_znums[0] == z2
        assert sorted_znums[1] == z1
        assert sorted_znums[2] == z3

    def test_max_and_min(self):
        """Test that max() and min() work correctly with Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        znums = [z1, z2, z3]

        assert max(znums) == z2
        assert min(znums) == z3


class TestZnumLargeValueComparisons:
    """Tests for comparisons with large values."""

    def test_large_value_comparison(self):
        """Test comparison with large Z-number values."""
        z_large1 = Znum(A=[100, 200, 300, 400], B=[0.1, 0.2, 0.3, 0.4])
        z_large2 = Znum(A=[50, 100, 150, 200], B=[0.2, 0.3, 0.4, 0.5])

        assert z_large1 > z_large2
        assert z_large2 < z_large1

    def test_fractional_value_comparison(self):
        """Test comparison with fractional Z-number values."""
        z_frac1 = Znum(A=[0.1, 0.2, 0.3, 0.4], B=[0.1, 0.2, 0.3, 0.4])
        z_frac2 = Znum(A=[0.2, 0.3, 0.4, 0.5], B=[0.2, 0.3, 0.4, 0.5])

        assert z_frac2 > z_frac1
        assert z_frac1 < z_frac2


class TestZnumComparisonEdgeCases:
    """Tests for edge cases in comparisons."""

    def test_compare_result_of_operations(self):
        """Test comparing results of arithmetic operations."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        result1 = z1 + z2  # A: [3, 5, 7, 9]
        result2 = z1 * 2   # A: [2, 4, 6, 8]

        assert result1 > result2

    def test_compare_after_scalar_multiplication(self):
        """Test that z * 2 > z."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z1_doubled = z1 * 2

        assert z1_doubled > z1

    def test_compare_after_power(self):
        """Test comparison after power operation."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z1_squared = z1 ** 2

        assert z1_squared > z1


class TestZnumNotEqual:
    """Tests for Znum inequality (!=) comparison."""

    def test_not_equal_self(self):
        """Test that a Z-number is not unequal to itself."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert not (z1 != z1)

    def test_not_equal_identical_values(self):
        """Test that two Z-numbers with identical values are not unequal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert not (z1 != z4)

    def test_not_equal_different_A(self):
        """Test that Z-numbers with different A values are unequal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        assert z1 != z2

    def test_not_equal_different_B(self):
        """Test that Z-numbers with same A but different B are unequal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.2, 0.3, 0.4, 0.5])
        assert z1 != z2

    def test_not_equal_consistency_with_equal(self):
        """Test that != is the negation of ==."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        assert (z1 != z2) == (not (z1 == z2))
        assert (z1 != z3) == (not (z1 == z3))


class TestZnumSameADifferentB:
    """Tests for comparisons with same A but different reliability (B)."""

    def test_same_A_different_B_not_equal(self):
        """Test that Z-numbers with same A but different B are not equal."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.5, 0.6, 0.7, 0.8])
        assert not (z1 == z2)

    def test_same_A_higher_B_comparison(self):
        """Test comparison with same A but higher reliability."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.5, 0.6, 0.7, 0.8])
        # The comparison result depends on the dominance calculation
        # We just verify it doesn't crash and returns a consistent result
        result_gt = z1 > z2
        result_lt = z1 < z2
        # Should be consistent
        assert result_gt != result_lt or (not result_gt and not result_lt)

    def test_same_A_slightly_different_B(self):
        """Test comparison with same A and very similar B values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.11, 0.21, 0.31, 0.41])
        assert not (z1 == z2)


class TestZnumBoundaryValues:
    """Tests for boundary and edge case values."""

    def test_zero_A_values(self):
        """Test comparison with Z-numbers containing zero values."""
        z1 = Znum(A=[0, 0, 1, 2], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 < z2
        assert z2 > z1

    def test_very_small_A_values(self):
        """Test comparison with very small A values."""
        z1 = Znum(A=[0.001, 0.002, 0.003, 0.004], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[0.01, 0.02, 0.03, 0.04], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 < z2
        assert z2 > z1

    def test_very_large_A_values(self):
        """Test comparison with very large A values."""
        z1 = Znum(A=[1000, 2000, 3000, 4000], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[10000, 20000, 30000, 40000], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 < z2
        assert z2 > z1

    def test_very_small_B_values(self):
        """Test comparison with very small B (reliability) values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.001, 0.002, 0.003, 0.004])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.001, 0.002, 0.003, 0.004])
        assert z1 < z2
        assert z2 > z1

    def test_compare_near_equal_znums(self):
        """Test comparison of Z-numbers with very close values."""
        z1 = Znum(A=[1.0, 2.0, 3.0, 4.0], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1.001, 2.001, 3.001, 4.001], B=[0.1, 0.2, 0.3, 0.4])
        # Very close Z-numbers may be considered equal by fuzzy comparison
        # The comparison should still have a defined relationship
        assert z1 < z2 or z2 < z1 or z1 == z2


class TestZnumZeroCrossingRanges:
    """Tests for Z-numbers that cross zero (contain both negative and positive values)."""

    def test_zero_crossing_vs_positive(self):
        """Test comparison between zero-crossing and positive Z-numbers."""
        z_cross = Znum(A=[-1, 0, 1, 2], B=[0.1, 0.2, 0.3, 0.4])
        z_pos = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z_cross < z_pos
        assert z_pos > z_cross

    def test_zero_crossing_vs_negative(self):
        """Test comparison between zero-crossing and negative Z-numbers."""
        z_cross = Znum(A=[-1, 0, 1, 2], B=[0.1, 0.2, 0.3, 0.4])
        z_neg = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        assert z_cross > z_neg
        assert z_neg < z_cross

    def test_two_zero_crossing_znums(self):
        """Test comparison between two zero-crossing Z-numbers."""
        z1 = Znum(A=[-2, -1, 0, 1], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[-1, 0, 1, 2], B=[0.1, 0.2, 0.3, 0.4])
        assert z1 < z2
        assert z2 > z1

    def test_symmetric_zero_crossing(self):
        """Test symmetric zero-crossing Z-numbers."""
        z1 = Znum(A=[-2, -1, 1, 2], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[-1, 0, 0, 1], B=[0.1, 0.2, 0.3, 0.4])
        # z2 is centered around zero, z1 is more spread
        result = z1 > z2 or z1 < z2 or z1 == z2
        assert result  # Should have a defined relationship


class TestZnumTransitivity:
    """Comprehensive tests for transitivity of comparisons."""

    def test_transitivity_chain_five_elements(self):
        """Test transitivity across a chain of 5 Z-numbers."""
        z1 = Znum(A=[0, 1, 2, 3], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[2, 3, 4, 5], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.1, 0.2, 0.3, 0.4])
        z5 = Znum(A=[4, 5, 6, 7], B=[0.1, 0.2, 0.3, 0.4])

        # Direct comparisons
        assert z1 < z2 < z3 < z4 < z5
        assert z5 > z4 > z3 > z2 > z1

        # Transitivity
        assert z1 < z3  # z1 < z2 < z3
        assert z1 < z4  # z1 < z2 < z3 < z4
        assert z1 < z5  # z1 < z2 < z3 < z4 < z5
        assert z2 < z4  # z2 < z3 < z4
        assert z2 < z5  # z2 < z3 < z4 < z5
        assert z3 < z5  # z3 < z4 < z5

    def test_transitivity_with_varied_B(self):
        """Test transitivity with varied B values."""
        z1 = Znum(A=[0, 1, 2, 3], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[2, 3, 4, 5], B=[0.3, 0.4, 0.5, 0.6])

        assert z1 < z2
        assert z2 < z3
        assert z1 < z3  # Transitivity holds

    def test_transitivity_equality_chain(self):
        """Test that equal Z-numbers maintain transitivity."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        assert z1 == z2
        assert z2 == z3
        assert z1 == z3  # Transitivity of equality


class TestZnumComparisonWithOperations:
    """Tests for comparisons after various arithmetic operations."""

    def test_compare_after_subtraction(self):
        """Test comparison after subtraction operation."""
        z1 = Znum(A=[5, 6, 7, 8], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 - z2
        # Fuzzy subtraction produces interval arithmetic result
        # The result should be comparable (has a defined relationship)
        assert result > z2 or result < z2 or result == z2

    def test_compare_after_division(self):
        """Test comparison after division by Znum."""
        z1 = Znum(A=[4, 8, 12, 16], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 2, 2, 2], B=[0.1, 0.2, 0.3, 0.4])
        z1_divided = z1 / z2
        # Division result should be comparable
        assert z1 > z1_divided or z1 < z1_divided or z1 == z1_divided

    def test_compare_sum_vs_parts(self):
        """Test that z1 + z2 > z1 and z1 + z2 > z2 for positive Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z_sum = z1 + z2
        assert z_sum > z1
        assert z_sum > z2

    def test_compare_product_vs_factors(self):
        """Test comparison of product vs factors for values > 1."""
        z1 = Znum(A=[2, 3, 4, 5], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[3, 4, 5, 6], B=[0.2, 0.3, 0.4, 0.5])
        z_prod = z1 * z2
        assert z_prod > z1
        assert z_prod > z2

    def test_compare_after_sqrt(self):
        """Test comparison after square root operation."""
        z1 = Znum(A=[4, 9, 16, 25], B=[0.1, 0.2, 0.3, 0.4])
        z1_sqrt = z1 ** 0.5
        assert z1 > z1_sqrt

    def test_compare_chained_operations(self):
        """Test comparison after chained operations."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        result = (z1 + z2) * 2
        assert result > z1 + z2
        assert result > z1
        assert result > z2


class TestZnumSortingExtended:
    """Extended sorting tests with various scenarios."""

    def test_sort_with_duplicates(self):
        """Test sorting a list with duplicate Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z1_copy = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        znums = [z2, z1, z1_copy]
        sorted_znums = sorted(znums)

        assert sorted_znums[0] == z1
        assert sorted_znums[1] == z1_copy
        assert sorted_znums[2] == z2

    def test_sort_large_collection(self):
        """Test sorting a larger collection of Z-numbers."""
        znums = []
        for i in range(10):
            z = Znum(A=[i, i+1, i+2, i+3], B=[0.1, 0.2, 0.3, 0.4])
            znums.append(z)

        # Shuffle manually
        shuffled = [znums[5], znums[2], znums[8], znums[0], znums[9],
                    znums[3], znums[7], znums[1], znums[4], znums[6]]

        sorted_znums = sorted(shuffled)

        # Verify order
        for i in range(len(sorted_znums) - 1):
            assert sorted_znums[i] <= sorted_znums[i + 1]

    def test_sort_with_negatives(self):
        """Test sorting Z-numbers including negative values."""
        z_neg = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        z_cross = Znum(A=[-1, 0, 1, 2], B=[0.1, 0.2, 0.3, 0.4])
        z_pos = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        znums = [z_pos, z_neg, z_cross]
        sorted_znums = sorted(znums)

        assert sorted_znums[0] == z_neg
        assert sorted_znums[1] == z_cross
        assert sorted_znums[2] == z_pos

    def test_min_max_with_duplicates(self):
        """Test min and max with duplicate values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z1_copy = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        znums = [z1, z2, z1_copy]

        max_z = max(znums)
        min_z = min(znums)

        assert max_z == z2
        assert min_z == z1 or min_z == z1_copy


class TestZnumChainedComparisons:
    """Tests for Python's chained comparison syntax."""

    def test_chained_less_than(self):
        """Test chained less-than comparisons (a < b < c)."""
        z1 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        assert z1 < z2 < z3

    def test_chained_greater_than(self):
        """Test chained greater-than comparisons (a > b > c)."""
        z1 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        assert z3 > z2 > z1

    def test_chained_less_than_or_equal(self):
        """Test chained less-than-or-equal comparisons."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        assert z1 <= z2 <= z3

    def test_chained_mixed_comparisons(self):
        """Test mixed chained comparisons."""
        z1 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z2 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z4 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        assert z1 < z2 <= z3 < z4


class TestZnumUniformSpacing:
    """Tests for Z-numbers with uniform vs non-uniform spacing."""

    def test_uniform_spacing_comparison(self):
        """Test comparison of uniformly spaced Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])  # Uniform spacing of 1
        z2 = Znum(A=[2, 4, 6, 8], B=[0.1, 0.2, 0.3, 0.4])  # Uniform spacing of 2
        assert z1 < z2

    def test_non_uniform_spacing_comparison(self):
        """Test comparison of non-uniformly spaced Z-numbers."""
        z1 = Znum(A=[1, 1.5, 3, 4], B=[0.1, 0.2, 0.3, 0.4])  # Non-uniform
        z2 = Znum(A=[1, 2, 2.5, 4], B=[0.1, 0.2, 0.3, 0.4])  # Non-uniform
        # Both have same bounds but different internal structure
        result = z1 > z2 or z1 < z2 or z1 == z2
        assert result  # Should have a defined relationship

    def test_wide_vs_narrow_range(self):
        """Test comparison of wide vs narrow range Z-numbers."""
        z_wide = Znum(A=[0, 5, 10, 15], B=[0.1, 0.2, 0.3, 0.4])
        z_narrow = Znum(A=[6, 7, 8, 9], B=[0.1, 0.2, 0.3, 0.4])
        # z_narrow is centered within z_wide's range
        result = z_wide < z_narrow or z_wide > z_narrow
        assert result or z_wide == z_narrow


class TestZnumSpecialCases:
    """Tests for special edge cases."""

    def test_single_point_like_znum(self):
        """Test Z-number with very narrow range (almost a point)."""
        z_point = Znum(A=[5, 5.001, 5.002, 5.003], B=[0.1, 0.2, 0.3, 0.4])
        z_range = Znum(A=[4, 5, 6, 7], B=[0.1, 0.2, 0.3, 0.4])
        # Should still be comparable
        result = z_point < z_range or z_point > z_range or z_point == z_range
        assert result

    def test_comparison_symmetry(self):
        """Test that comparison is symmetric: (a > b) == (b < a)."""
        test_cases = [
            (Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4]),
             Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])),
            (Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4]),
             Znum(A=[-2, -1, 0, 1], B=[0.1, 0.2, 0.3, 0.4])),
            (Znum(A=[0.1, 0.2, 0.3, 0.4], B=[0.1, 0.2, 0.3, 0.4]),
             Znum(A=[0.5, 0.6, 0.7, 0.8], B=[0.5, 0.6, 0.7, 0.8])),
        ]

        for z1, z2 in test_cases:
            assert (z1 > z2) == (z2 < z1)
            assert (z1 < z2) == (z2 > z1)
            assert (z1 >= z2) == (z2 <= z1)
            assert (z1 <= z2) == (z2 >= z1)

    def test_comparison_antisymmetry(self):
        """Test antisymmetry: if a > b, then not b > a."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])

        if z1 > z2:
            assert not (z2 > z1)
        if z2 > z1:
            assert not (z1 > z2)

    def test_comparison_with_scaled_versions(self):
        """Test comparison of a Z-number with its scaled versions."""
        z = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])

        z_half = z * 0.5
        z_double = z * 2
        z_triple = z * 3

        assert z_half < z
        assert z < z_double
        assert z_double < z_triple
        assert z_half < z_double < z_triple

    def test_negative_znum_vs_positive(self):
        """Test comparison between negative and positive Z-numbers."""
        z_pos = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z_neg = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])

        assert z_neg < z_pos
        assert z_pos > z_neg


class TestZnumListOperations:
    """Tests for list operations that depend on comparisons."""

    def test_sorted_key_function(self):
        """Test that sorted() with key function works correctly."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        # Sort by the first element of A
        znums = [z2, z1, z3]
        sorted_znums = sorted(znums, key=lambda z: z.A[0])

        assert sorted_znums[0] == z3
        assert sorted_znums[1] == z1
        assert sorted_znums[2] == z2

    def test_index_of_max(self):
        """Test finding the index of the maximum Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        znums = [z1, z2, z3]
        max_index = znums.index(max(znums))
        assert max_index == 1  # z2 is the maximum

    def test_index_of_min(self):
        """Test finding the index of the minimum Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])

        znums = [z1, z2, z3]
        min_index = znums.index(min(znums))
        assert min_index == 2  # z3 is the minimum

    def test_filter_greater_than_threshold(self):
        """Test filtering Z-numbers greater than a threshold."""
        threshold = Znum(A=[1.5, 2.5, 3.5, 4.5], B=[0.15, 0.25, 0.35, 0.45])

        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])

        znums = [z1, z2, z3, z4]
        filtered = [z for z in znums if z > threshold]

        assert z2 in filtered
        assert z4 in filtered
        assert z1 not in filtered
        assert z3 not in filtered
