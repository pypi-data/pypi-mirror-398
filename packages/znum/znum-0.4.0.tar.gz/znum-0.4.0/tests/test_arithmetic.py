"""
Comprehensive E2E tests for Znum arithmetic operations.

These tests verify that all arithmetic operations produce correct results.
The expected values were generated from the current (ground truth) implementation.
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal
from znum import Znum


class TestZnumAddition:
    """Tests for Znum addition operations."""

    def test_addition_basic(self):
        """Test basic addition of two Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 + z2

        expected_A = [3.0, 5.0, 7.0, 9.0]
        expected_B = [0.395556, 0.441956, 0.460267, 0.496889]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_addition_with_smaller_values(self):
        """Test addition with smaller Z-number values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 + z3

        expected_A = [1.5, 3.0, 4.5, 6.0]
        expected_B = [0.439083, 0.457556, 0.4998, 0.5422]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_addition_with_zero_returns_self(self):
        """Test that adding zero returns the original Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 + 0

        assert_array_almost_equal(result.A, [1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(result.B, [0.1, 0.2, 0.3, 0.4])

    def test_radd_with_zero(self):
        """Test right addition with zero (for sum() support)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = 0 + z1

        assert_array_almost_equal(result.A, [1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(result.B, [0.1, 0.2, 0.3, 0.4])

    def test_sum_of_list(self):
        """Test using Python's sum() on a list of Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = sum([z1, z2, z3])

        expected_A = [3.5, 6.0, 8.5, 11.0]
        expected_B = [0.469711, 0.481018, 0.490962, 0.508389]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_addition_negative_numbers(self):
        """Test addition with negative Z-number values."""
        z_neg1 = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        z_neg2 = Znum(A=[-2, -1, 0, 1], B=[0.15, 0.25, 0.35, 0.45])
        result = z_neg1 + z_neg2

        expected_A = [-6.0, -4.0, -2.0, 0.0]
        expected_B = [0.365, 0.393819, 0.40625, 0.421667]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_addition_large_values(self):
        """Test addition with large Z-number values."""
        z_large1 = Znum(A=[100, 200, 300, 400], B=[0.1, 0.2, 0.3, 0.4])
        z_large2 = Znum(A=[50, 100, 150, 200], B=[0.2, 0.3, 0.4, 0.5])
        result = z_large1 + z_large2

        expected_A = [150.0, 300.0, 450.0, 600.0]
        expected_B = [0.475444, 0.513444, 0.552, 0.596778]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_addition_fractional_values(self):
        """Test addition with fractional Z-number values."""
        z_frac1 = Znum(A=[0.1, 0.2, 0.3, 0.4], B=[0.1, 0.2, 0.3, 0.4])
        z_frac2 = Znum(A=[0.2, 0.3, 0.4, 0.5], B=[0.2, 0.3, 0.4, 0.5])
        result = z_frac1 + z_frac2

        expected_A = [0.3, 0.5, 0.7, 0.9]
        expected_B = [0.395556, 0.441956, 0.482133, 0.496889]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumSubtraction:
    """Tests for Znum subtraction operations."""

    def test_subtraction_basic(self):
        """Test basic subtraction of two Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z2 - z1

        expected_A = [-2.0, 0.0, 2.0, 4.0]
        expected_B = [0.417778, 0.4944, 0.5356, 0.618]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=3)

    def test_subtraction_with_smaller_values(self):
        """Test subtraction with smaller Z-number values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 - z3

        expected_A = [-1.0, 0.5, 2.0, 3.5]
        expected_B = [0.35925, 0.367333, 0.394667, 0.427333]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_subtraction_negative_numbers(self):
        """Test subtraction with negative Z-number values."""
        z_neg1 = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        z_neg2 = Znum(A=[-2, -1, 0, 1], B=[0.15, 0.25, 0.35, 0.45])
        result = z_neg1 - z_neg2

        expected_A = [-5.0, -3.0, -1.0, 1.0]
        expected_B = [0.40375, 0.436458, 0.485833, 0.574375]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumMultiplication:
    """Tests for Znum multiplication operations."""

    def test_multiplication_znum_by_znum(self):
        """Test multiplication of two Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 * z2

        expected_A = [2.0, 6.0, 12.0, 20.0]
        expected_B = [0.115556, 0.189867, 0.2368, 0.310667]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_multiplication_znum_by_znum_smaller(self):
        """Test multiplication of Z-number with smaller Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 * z3

        expected_A = [0.5, 2.0, 4.5, 8.0]
        expected_B = [0.1914, 0.1938, 0.218444, 0.303889]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_multiplication_by_positive_scalar(self):
        """Test multiplication of Z-number by positive scalar."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 * 2

        expected_A = [2.0, 4.0, 6.0, 8.0]
        expected_B = [0.1, 0.2, 0.3, 0.4]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_multiplication_by_fractional_scalar(self):
        """Test multiplication of Z-number by fractional scalar."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 * 0.5

        expected_A = [0.5, 1.0, 1.5, 2.0]
        expected_B = [0.1, 0.2, 0.3, 0.4]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_multiplication_chained_scalars(self):
        """Test chained scalar multiplication."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 * 2 * 3

        expected_A = [6.0, 12.0, 18.0, 24.0]
        expected_B = [0.1, 0.2, 0.3, 0.4]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_multiplication_negative_numbers(self):
        """Test multiplication with negative Z-number values."""
        z_neg1 = Znum(A=[-4, -3, -2, -1], B=[0.1, 0.2, 0.3, 0.4])
        z_neg2 = Znum(A=[-2, -1, 0, 1], B=[0.15, 0.25, 0.35, 0.45])
        result = z_neg1 * z_neg2

        expected_A = [-4.0, -0.0, 3.0, 8.0]
        expected_B = [0.288958, 0.364583, 0.405417, 0.479375]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_multiplication_large_values(self):
        """Test multiplication with large Z-number values."""
        z_large1 = Znum(A=[100, 200, 300, 400], B=[0.1, 0.2, 0.3, 0.4])
        z_large2 = Znum(A=[50, 100, 150, 200], B=[0.2, 0.3, 0.4, 0.5])
        result = z_large1 * z_large2

        expected_A = [5000.0, 20000.0, 45000.0, 80000.0]
        expected_B = [0.244444, 0.279444, 0.3, 0.327778]

        assert_array_almost_equal(result.A, expected_A, decimal=1)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_multiplication_fractional_values(self):
        """Test multiplication with fractional Z-number values."""
        z_frac1 = Znum(A=[0.1, 0.2, 0.3, 0.4], B=[0.1, 0.2, 0.3, 0.4])
        z_frac2 = Znum(A=[0.2, 0.3, 0.4, 0.5], B=[0.2, 0.3, 0.4, 0.5])
        result = z_frac1 * z_frac2

        expected_A = [0.02, 0.06, 0.12, 0.2]
        expected_B = [0.0931, 0.1372, 0.1952, 0.296]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=3)


class TestZnumDivision:
    """Tests for Znum division operations."""

    def test_division_basic(self):
        """Test basic division of two Z-numbers."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z2 / z1

        expected_A = [0.5, 1.0, 2.0, 5.0]
        expected_B = [0.124444, 0.219911, 0.2704, 0.320444]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_division_with_smaller_values(self):
        """Test division with smaller Z-number values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 / z3

        expected_A = [0.5, 1.333333, 3.0, 8.0]
        expected_B = [0.284556, 0.402667, 0.496633, 0.5183]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=3)

    def test_division_large_values(self):
        """Test division with large Z-number values."""
        z_large1 = Znum(A=[100, 200, 300, 400], B=[0.1, 0.2, 0.3, 0.4])
        z_large2 = Znum(A=[50, 100, 150, 200], B=[0.2, 0.3, 0.4, 0.5])
        result = z_large1 / z_large2

        expected_A = [0.5, 1.333333, 3.0, 8.0]
        expected_B = [0.207222, 0.247333, 0.279667, 0.328889]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_division_fractional_values(self):
        """Test division with fractional Z-number values."""
        z_frac1 = Znum(A=[0.1, 0.2, 0.3, 0.4], B=[0.1, 0.2, 0.3, 0.4])
        z_frac2 = Znum(A=[0.2, 0.3, 0.4, 0.5], B=[0.2, 0.3, 0.4, 0.5])
        result = z_frac1 / z_frac2

        expected_A = [0.2, 0.5, 1.0, 2.0]
        expected_B = [0.124444, 0.206533, 0.264533, 0.320444]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumPower:
    """Tests for Znum power operations."""

    def test_power_squared(self):
        """Test squaring a Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 ** 2

        expected_A = [1.0, 4.0, 9.0, 16.0]
        expected_B = [0.1, 0.2, 0.3, 0.4]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_power_square_root(self):
        """Test square root of a Z-number."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1 ** 0.5

        expected_A = [1.0, 1.4142135623730951, 1.7320508075688772, 2.0]
        expected_B = [0.1, 0.2, 0.3, 0.4]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_power_cubed(self):
        """Test cubing a Z-number."""
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z2 ** 3

        expected_A = [8.0, 27.0, 64.0, 125.0]
        expected_B = [0.2, 0.3, 0.4, 0.5]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)

    def test_power_preserves_B_through_operations(self):
        """Test that power(x, 2) then power(result, 0.5) returns original A."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = (z1 ** 2) ** 0.5

        expected_A = [1.0, 2.0, 3.0, 4.0]
        expected_B = [0.1, 0.2, 0.3, 0.4]

        assert_array_almost_equal(result.A, expected_A, decimal=5)
        assert_array_almost_equal(result.B, expected_B, decimal=5)


class TestZnumChainedOperations:
    """Tests for chained arithmetic operations."""

    def test_add_then_multiply(self):
        """Test (z1 + z2) * z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 + z2) * z3

        expected_A = [1.5, 5.0, 10.5, 18.0]
        expected_B = [0.224769, 0.325815, 0.395221, 0.432431]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_multiply_then_add(self):
        """Test (z1 * z2) + z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 * z2) + z3

        expected_A = [2.5, 7.0, 13.5, 22.0]
        expected_B = [0.073046, 0.085513, 0.100062, 0.120017]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_subtract_then_multiply(self):
        """Test (z1 - z3) * z2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 - z3) * z2

        expected_A = [-5.0, 1.5, 8.0, 17.5]
        expected_B = [0.16353, 0.20816, 0.262605, 0.327911]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumTwoTermEquations:
    """Tests for 2-term complex equations."""

    def test_add_with_multiplication_precedence(self):
        """Test z1 + z2 * z3 (multiplication first)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 + z2 * z3

        expected_A = [2.0, 5.0, 9.0, 14.0]
        expected_B = [0.362886, 0.412573, 0.442973, 0.462611]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_bracketed_add_then_divide(self):
        """Test (z1 + z2) / z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 + z2) / z3

        expected_A = [1.5, 3.333333, 7.0, 18.0]
        expected_B = [0.284345, 0.302851, 0.317674, 0.325494]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_power_then_add(self):
        """Test z1 ** 2 + z2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 ** 2 + z2

        expected_A = [3.0, 7.0, 13.0, 21.0]
        expected_B = [0.197956, 0.2472, 0.3104, 0.387556]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_scalar_multiplications_then_add(self):
        """Test z1 * 2 + z2 * 3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 * 2 + z2 * 3

        expected_A = [8.0, 13.0, 18.0, 23.0]
        expected_B = [0.280648, 0.364, 0.409778, 0.478704]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_bracketed_subtract_then_divide(self):
        """Test (z1 - z3) / z2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 - z3) / z2

        expected_A = [-0.5, 0.125, 0.666667, 1.75]
        expected_B = [0.16353, 0.20816, 0.262605, 0.327911]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumThreeTermEquations:
    """Tests for 3-term complex equations."""

    def test_three_term_addition(self):
        """Test z1 + z2 + z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 + z2 + z3

        expected_A = [3.5, 6.0, 8.5, 11.0]
        expected_B = [0.469711, 0.481018, 0.490962, 0.508389]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_three_term_multiplication(self):
        """Test z1 * z2 * z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 * z2 * z3

        expected_A = [1.0, 6.0, 18.0, 40.0]
        expected_B = [0.238763, 0.281139, 0.310727, 0.359396]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_multiply_then_add_znum(self):
        """Test z1 * z2 + z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 * z2 + z3

        expected_A = [2.5, 7.0, 13.5, 22.0]
        expected_B = [0.073046, 0.085513, 0.100062, 0.120017]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_power_add_then_divide(self):
        """Test (z1 ** 2 + z2) / z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 ** 2 + z2) / z3

        expected_A = [1.5, 4.666667, 13.0, 42.0]
        expected_B = [0.148424, 0.19417, 0.230056, 0.259009]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_mixed_scalar_operations(self):
        """Test z1 * 2 + z2 - z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 * 2 + z2 - z3

        expected_A = [2.0, 5.5, 9.0, 12.5]
        expected_B = [0.033966, 0.07895, 0.12124, 0.162051]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_power_of_sum_then_multiply(self):
        """Test (z1 + z2) ** 0.5 * z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 + z2) ** 0.5 * z3

        expected_A = [0.866025, 2.236068, 3.968627, 6.0]
        expected_B = [0.0419, 0.088507, 0.132285, 0.173549]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumFourTermEquations:
    """Tests for 4-term complex equations."""

    def test_four_term_addition(self):
        """Test z1 + z2 + z3 + z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = z1 + z2 + z3 + z4

        expected_A = [6.5, 10.0, 13.5, 17.0]
        expected_B = [0.276973, 0.34503, 0.393386, 0.447018]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_product_pairs_addition(self):
        """Test z1 * z2 + z3 * z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = z1 * z2 + z3 * z4

        expected_A = [3.5, 10.0, 19.5, 32.0]
        expected_B = [0.112104, 0.174813, 0.218572, 0.265766]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_sum_pairs_multiplication(self):
        """Test (z1 + z2) * (z3 + z4)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 + z2) * (z3 + z4)

        expected_A = [10.5, 25.0, 45.5, 72.0]
        expected_B = [0.34207, 0.360483, 0.37951, 0.408891]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_product_divided_by_sum(self):
        """Test (z1 * z2) / (z3 + z4)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 * z2) / (z3 + z4)

        expected_A = [0.25, 0.923077, 2.4, 5.714286]
        expected_B = [0.055852, 0.097096, 0.134483, 0.19295]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_squares_sum_minus_znum(self):
        """Test z1 ** 2 + z2 ** 2 - z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 ** 2 + z2 ** 2 - z3

        expected_A = [3.0, 11.5, 24.0, 40.5]
        expected_B = [0.025359, 0.054921, 0.0892, 0.128711]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_three_sum_times_znum(self):
        """Test (z1 + z2 + z3) * z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 + z2 + z3) * z4

        expected_A = [10.5, 24.0, 42.5, 66.0]
        expected_B = [0.267274, 0.342907, 0.372364, 0.407767]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_mixed_scalar_multiplications(self):
        """Test z1 * 2 + z2 * 3 - z3 * 4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 * 2 + z2 * 3 - z3 * 4

        expected_A = [0.0, 7.0, 14.0, 21.0]
        expected_B = [0.118621, 0.154469, 0.172573, 0.188296]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumFiveTermEquations:
    """Tests for 5-term complex equations."""

    def test_five_term_addition(self):
        """Test z1 + z2 + z3 + z4 + z5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        z5 = Znum(A=[1.5, 2.5, 3.5, 4.5], B=[0.15, 0.25, 0.35, 0.45])
        result = z1 + z2 + z3 + z4 + z5

        expected_A = [8.0, 12.5, 17.0, 21.5]
        expected_B = [0.162676, 0.230751, 0.29368, 0.371999]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_complex_five_term_mixed(self):
        """Test (z1 + z2) * z3 + z4 - z5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        z5 = Znum(A=[1.5, 2.5, 3.5, 4.5], B=[0.15, 0.25, 0.35, 0.45])
        result = (z1 + z2) * z3 + z4 - z5

        expected_A = [0.0, 5.5, 13.0, 22.5]
        expected_B = [0.128614, 0.151571, 0.172417, 0.205936]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_product_pairs_minus_znum(self):
        """Test z1 * z2 + z3 * z4 - z5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        z5 = Znum(A=[1.5, 2.5, 3.5, 4.5], B=[0.15, 0.25, 0.35, 0.45])
        result = z1 * z2 + z3 * z4 - z5

        expected_A = [-1.0, 6.5, 17.0, 30.5]
        expected_B = [0.062778, 0.096389, 0.136151, 0.189737]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_complex_division_with_subtraction(self):
        """Test (z1 + z2) * (z3 - z4) / z5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        z5 = Znum(A=[1.5, 2.5, 3.5, 4.5], B=[0.15, 0.25, 0.35, 0.45])
        result = (z1 + z2) * (z3 - z4) / z5

        expected_A = [-33.0, -11.2, -3.571429, -0.666667]
        expected_B = [0.052072, 0.09264, 0.136687, 0.189999]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_nested_power_subtraction_division(self):
        """Test ((z1 + z2) ** 2 - z3) / z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = ((z1 + z2) ** 2 - z3) / z4

        expected_A = [1.166667, 4.7, 12.0, 26.833333]
        expected_B = [0.005933, 0.017678, 0.03452, 0.059627]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumEquationsWithFloats:
    """Tests for equations mixing Z-numbers with float scalars."""

    def test_mixed_float_scalars(self):
        """Test z1 * 2.5 + z2 * 1.5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 * 2.5 + z2 * 1.5

        expected_A = [5.5, 9.5, 13.5, 17.5]
        expected_B = [0.066, 0.1512, 0.263, 0.345833]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=3)

    def test_sum_times_half(self):
        """Test (z1 + z2) * 0.5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = (z1 + z2) * 0.5

        expected_A = [1.5, 2.5, 3.5, 4.5]
        expected_B = [0.395556, 0.441956, 0.460267, 0.496889]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_squared_scaled_plus_znum(self):
        """Test z1 ** 2 * 0.25 + z2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 ** 2 * 0.25 + z2

        expected_A = [2.25, 4.0, 6.25, 9.0]
        expected_B = [0.286613, 0.33864, 0.35856, 0.393167]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_scaled_sum_divided(self):
        """Test (z1 * 3 + z2 * 2) / z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 * 3 + z2 * 2) / z3

        expected_A = [3.5, 8.0, 17.0, 44.0]
        expected_B = [0.029187, 0.060228, 0.095982, 0.137955]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_average_of_two(self):
        """Test z1 * 0.5 + z2 * 0.5 (weighted average)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 * 0.5 + z2 * 0.5

        expected_A = [1.5, 2.5, 3.5, 4.5]
        expected_B = [0.464815, 0.5, 0.524167, 0.57037]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_sum_doubled(self):
        """Test (z1 + z2 + z3) * 2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 + z2 + z3) * 2

        expected_A = [7.0, 12.0, 17.0, 22.0]
        expected_B = [0.469711, 0.481018, 0.490962, 0.508389]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_powers_with_float_scalars(self):
        """Test z1 ** 3 * 0.1 + z2 ** 2 * 0.2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = z1 ** 3 * 0.1 + z2 ** 2 * 0.2

        expected_A = [0.9, 2.6, 5.9, 11.4]
        expected_B = [0.054286, 0.124286, 0.21, 0.311429]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_scaled_subtraction(self):
        """Test (z1 * 2 - z2) * 1.5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = (z1 * 2 - z2) * 1.5

        expected_A = [-4.5, 0.0, 4.5, 9.0]
        expected_B = [0.366267, 0.3852, 0.4048, 0.4435]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumNestedBrackets:
    """Tests for deeply nested bracket expressions."""

    def test_nested_add_multiply_add(self):
        """Test ((z1 + z2) * z3) + z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = ((z1 + z2) * z3) + z4

        expected_A = [4.5, 9.0, 15.5, 24.0]
        expected_B = [0.184729, 0.228114, 0.28329, 0.336685]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_nested_multiply_add_divide(self):
        """Test (z1 * (z2 + z3)) / z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 * (z2 + z3)) / z4

        expected_A = [0.416667, 1.6, 4.125, 9.333333]
        expected_B = [0.106181, 0.143701, 0.185464, 0.243265]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_nested_squares_multiply(self):
        """Test ((z1 ** 2) + (z2 ** 2)) * z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = ((z1 ** 2) + (z2 ** 2)) * z3

        expected_A = [2.5, 13.0, 37.5, 82.0]
        expected_B = [0.025359, 0.054921, 0.0892, 0.128711]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_nested_add_product_subtract(self):
        """Test (z1 + (z2 * z3)) - z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 + (z2 * z3)) - z4

        expected_A = [-4.0, 0.0, 5.0, 11.0]
        expected_B = [0.417859, 0.497975, 0.518487, 0.543057]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_nested_divide_multiply(self):
        """Test ((z1 + z2) / z3) * z4."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = ((z1 + z2) / z3) * z4

        expected_A = [4.5, 13.333332, 35.0, 108.0]
        expected_B = [0.189978, 0.254583, 0.277989, 0.296771]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_complex_triple_operation(self):
        """Test (z1 * z2) + (z3 * z4) - (z1 + z2)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 * z2) + (z3 * z4) - (z1 + z2)

        expected_A = [-5.5, 3.0, 14.5, 29.0]
        expected_B = [0.112104, 0.148377, 0.173329, 0.204055]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumPowerWithOperations:
    """Tests for power operations combined with other operations."""

    def test_sum_squared(self):
        """Test (z1 + z2) ** 2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = (z1 + z2) ** 2

        expected_A = [9.0, 25.0, 49.0, 81.0]
        expected_B = [0.395556, 0.441956, 0.460267, 0.496889]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_product_sqrt(self):
        """Test (z1 * z2) ** 0.5."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = (z1 * z2) ** 0.5

        expected_A = [1.4142135623730951, 2.449489742783178, 3.4641016151377544, 4.47213595499958]
        expected_B = [0.115556, 0.189867, 0.2368, 0.310667]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_three_squares_sum(self):
        """Test z1 ** 2 + z2 ** 2 + z3 ** 2."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 ** 2 + z2 ** 2 + z3 ** 2

        expected_A = [5.25, 14.0, 27.25, 45.0]
        expected_B = [0.171594, 0.206868, 0.239056, 0.27201]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_sqrt_sum_multiply(self):
        """Test (z1 ** 0.5 + z2 ** 0.5) * z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = (z1 ** 0.5 + z2 ** 0.5) * z3

        expected_A = [1.207107, 3.146264, 5.598076, 8.472136]
        expected_B = [0.02, 0.060624, 0.101548, 0.139506]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_sqrt_then_square_identity(self):
        """Test ((z1 + z2) ** 0.5) ** 2 returns original sum."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        result = ((z1 + z2) ** 0.5) ** 2

        expected_A = [3.0, 5.0, 7.0, 9.0]
        expected_B = [0.395556, 0.441956, 0.460267, 0.496889]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumDivisionHeavy:
    """Tests for division-heavy expressions."""

    def test_chained_division(self):
        """Test z1 / z2 / z3."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 / z2 / z3

        expected_A = [0.1, 0.333333, 1.0, 4.0]
        expected_B = [0.021859, 0.055153, 0.091882, 0.133025]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_division_sum(self):
        """Test (z1 / z2) + (z3 / z4)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 / z2) + (z3 / z4)

        expected_A = [0.283333, 0.7, 1.375, 2.666667]
        expected_B = [0.064781, 0.104072, 0.155007, 0.208574]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_divide_by_sum(self):
        """Test z1 / (z2 + z3)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        result = z1 / (z2 + z3)

        expected_A = [0.142857, 0.363636, 0.75, 1.6]
        expected_B = [0.1, 0.171689, 0.234535, 0.304622]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)

    def test_sum_divided_by_product(self):
        """Test (z1 + z2) / (z3 * z4)."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z2 = Znum(A=[2, 3, 4, 5], B=[0.2, 0.3, 0.4, 0.5])
        z3 = Znum(A=[0.5, 1, 1.5, 2], B=[0.05, 0.1, 0.15, 0.2])
        z4 = Znum(A=[3, 4, 5, 6], B=[0.3, 0.4, 0.5, 0.6])
        result = (z1 + z2) / (z3 * z4)

        expected_A = [0.25, 0.666667, 1.75, 6.0]
        expected_B = [0.155669, 0.178177, 0.21135, 0.257993]

        assert_array_almost_equal(result.A, expected_A, decimal=4)
        assert_array_almost_equal(result.B, expected_B, decimal=4)


class TestZnumUtilityMethods:
    """Tests for Znum utility methods."""

    def test_str_representation(self):
        """Test string representation."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = str(z1)
        assert result == "Znum(A=[1.0, 2.0, 3.0, 4.0], B=[0.1, 0.2, 0.3, 0.4])"

    def test_repr_representation(self):
        """Test repr representation."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = repr(z1)
        assert result == "Znum(A=[1.0, 2.0, 3.0, 4.0], B=[0.1, 0.2, 0.3, 0.4])"

    def test_dimension_property(self):
        """Test dimension property."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        assert z1.dimension == 4

    def test_copy_returns_same_values(self):
        """Test that copy returns same values."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z_copy = z1.copy()

        assert_array_almost_equal(z_copy.A, [1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(z_copy.B, [0.1, 0.2, 0.3, 0.4])

    def test_copy_returns_different_object(self):
        """Test that copy returns a different object."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z_copy = z1.copy()
        assert z_copy is not z1

    def test_copy_is_independent(self):
        """Test that modifying copy doesn't affect original."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z_copy = z1.copy()
        z_copy.A = [5, 6, 7, 8]

        assert_array_almost_equal(z1.A, [1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(z_copy.A, [5.0, 6.0, 7.0, 8.0])

    def test_to_json(self):
        """Test JSON conversion."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1.to_json()

        expected = {"A": [1.0, 2.0, 3.0, 4.0], "B": [0.1, 0.2, 0.3, 0.4]}
        assert result == expected

    def test_to_array(self):
        """Test array conversion."""
        z1 = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        result = z1.to_array()

        expected = [1.0, 2.0, 3.0, 4.0, 0.1, 0.2, 0.3, 0.4]
        assert_array_almost_equal(result, expected)


class TestZnumConstruction:
    """Tests for Znum construction."""

    def test_default_constructor(self):
        """Test default constructor values."""
        z_default = Znum()

        assert_array_almost_equal(z_default.A, [1.0, 2.0, 3.0, 4.0])
        assert_array_almost_equal(z_default.B, [0.1, 0.2, 0.3, 0.4])
        assert_array_almost_equal(z_default.C, [0.0, 1.0, 1.0, 0.0])

    def test_get_default_A(self):
        """Test get_default_A static method."""
        result = Znum.get_default_A()
        assert_array_almost_equal(result, [1.0, 2.0, 3.0, 4.0])

    def test_get_default_B(self):
        """Test get_default_B static method."""
        result = Znum.get_default_B()
        assert_array_almost_equal(result, [0.1, 0.2, 0.3, 0.4])

    def test_get_default_C(self):
        """Test get_default_C static method."""
        result = Znum.get_default_C()
        assert_array_almost_equal(result, [0.0, 1.0, 1.0, 0.0])

    def test_custom_C_part(self):
        """Test construction with custom C part."""
        z_with_c = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4], C=[0.1, 0.5, 0.5, 0.1])
        assert_array_almost_equal(z_with_c.C, [0.1, 0.5, 0.5, 0.1])

    def test_exact_number_C_part(self):
        """Test that when all A values are equal, C becomes all ones."""
        z_exact = Znum(A=[5, 5, 5, 5], B=[0.1, 0.2, 0.3, 0.4])
        assert_array_almost_equal(z_exact.C, [1.0, 1.0, 1.0, 1.0])

    def test_A_setter(self):
        """Test A property setter."""
        z = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z.A = [5, 6, 7, 8]
        assert_array_almost_equal(z.A, [5.0, 6.0, 7.0, 8.0])

    def test_B_setter(self):
        """Test B property setter."""
        z = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z.B = [0.5, 0.6, 0.7, 0.8]
        assert_array_almost_equal(z.B, [0.5, 0.6, 0.7, 0.8])

    def test_C_setter(self):
        """Test C property setter."""
        z = Znum(A=[1, 2, 3, 4], B=[0.1, 0.2, 0.3, 0.4])
        z.C = [0.2, 0.8, 0.8, 0.2]
        assert_array_almost_equal(z.C, [0.2, 0.8, 0.8, 0.2])
