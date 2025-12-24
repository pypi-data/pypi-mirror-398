from .valid import Valid
from .utils import Beast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from znum.core import Znum

# QIntermediate = zn.Math.Math.QIntermediate


class Dist:
    class Simple:
        _COEF = 0.5

        @staticmethod
        def calculate(znum, n):
            """
            :type znum: zn.Znum.Znum
            :param n:
            :return:
            """
            return sum([abs(n - p) for p in znum.A + znum.B]) * Dist.Simple._COEF

    class Hellinger:
        _COEF_A = 0.5
        _COEF_B = 0.25
        _COEF_H = 0.25

        @staticmethod
        @Valid.Decorator.check_if_znums_are_even
        @Valid.Decorator.check_if_znums_are_in_same_dimension
        def calculate(znum1: "Znum", znum2: "Znum"):
            """
            :type znum1: zn.Znum.Znum
            :type znum2: zn.Znum.Znum
            """
            H = Dist.Hellinger._calculate_H(znum1, znum2)
            results = Dist.Hellinger._calculate_AB(znum1, znum2)
            A, B = results["A"], results["B"]
            result = (
                A * Dist.Hellinger._COEF_A
                + B * Dist.Hellinger._COEF_B
                + H * Dist.Hellinger._COEF_H
            )
            return result

        @staticmethod
        def _calculate_H(znum1: "Znum", znum2: "Znum"):
            """
            :type znum1: zn.Znum.Znum
            :type znum2: zn.Znum.Znum
            """
            znum1_optimization_matrix, znum2_optimization_matrix = (
                znum1.math.get_matrix(),
                znum2.math.get_matrix(),
            )
            znum1_optimization_matrix_transpose, znum2_optimization_matrix_transpose = (
                Beast.transpose_matrix(znum1_optimization_matrix),
                Beast.transpose_matrix(znum2_optimization_matrix),
            )
            result = min(
                [
                    Dist.Hellinger._formula_hellinger(znum1_column, znum2_column)
                    for znum1_column, znum2_column in zip(
                        znum1_optimization_matrix_transpose,
                        znum2_optimization_matrix_transpose,
                    )
                ]
            )
            return result

        @staticmethod
        def _calculate_AB(znum1: "Znum", znum2: "Znum"):
            """
            :type znum1: zn.Znum.Znum
            :type znum2: zn.Znum.Znum
            """
            dimension = znum1.dimension
            halfDimension = dimension // 2
            znums = {"A": [znum1.A, znum2.A], "B": [znum1.B, znum2.B]}
            results = {"A": [], "B": []}
            for key, (Q1, Q2) in znums.items():
                znum1_half1, znum1_half2, znum2_half1, znum2_half2 = (
                    Q1[:halfDimension],
                    reversed(Q1[halfDimension:]),
                    Q2[:halfDimension],
                    reversed(Q2[halfDimension:]),
                )
                for znum1_half1_q, znum1_half2_q, znum2_half1_q, znum2_half2_q in zip(
                    znum1_half1, znum1_half2, znum2_half1, znum2_half2
                ):
                    result = Dist.Hellinger._formula_q(
                        znum1_half1_q, znum2_half1_q, znum1_half2_q, znum2_half2_q
                    )
                    results[key].append(result)

            for key, result in results.items():
                results[key] = max(result)

            return results

        @staticmethod
        def _formula_hellinger(P, Q):
            """
            :type P: list or tuple
            :type Q: list or tuple
            """
            H = ((sum([((p**0.5) - (q**0.5)) ** 2 for p, q in zip(P, Q)])) ** 0.5) / (
                2**0.5
            )
            return H

        @staticmethod
        def _formula_q(znum1_half1_q, znum2_half1_q, znum1_half2_q, znum2_half2_q):
            """
            :type znum1_half1_q: int or float
            :type znum2_half1_q: int or float
            :type znum1_half2_q: int or float
            :type znum2_half2_q: int or float
            """
            Q = abs(
                (znum1_half1_q + znum1_half2_q) / 2
                - (znum2_half1_q + znum2_half2_q) / 2
            )
            return Q

        @staticmethod
        def get_ideal_from_znum(znum, value=0):
            from .math_ops import Math
            from .core import Znum

            """
            :type znum: zn.Znum.Znum
            :type value: int
            """
            znum_A_int = znum.A_int
            dimension = znum.dimension
            size = len(znum_A_int[Math.QIntermediate.VALUE])

            A_int = {
                Math.QIntermediate.VALUE: [value] * size,
                Math.QIntermediate.MEMBERSHIP: Math.get_default_membership(size),
            }

            B_int = {
                Math.QIntermediate.VALUE: A_int[Math.QIntermediate.VALUE].copy(),
                Math.QIntermediate.MEMBERSHIP: A_int[
                    Math.QIntermediate.MEMBERSHIP
                ].copy(),
            }

            znum_ideal = Znum(
                [value] * dimension, [value] * dimension, A_int=A_int, B_int=B_int
            )
            return znum_ideal

    # @staticmethod
    # def calculate_with_ideal(znum, value=0):
    #     """
    #     :param value:
    #     :type znum: zn.Znum.Znum
    #     """
    #     znum_A_int = znum.A_int
    #     optimization_matrix_znum = znum.math.get_matrix()
    #     size = len(znum_A_int[QIntermediate.VALUE])
    #
    #     A_int = {
    #         QIntermediate.VALUE: [value] * size,
    #         QIntermediate.MEMBERSHIP: xusun.Math.get_default_membership(size)
    #     }
    #
    #     B_int = {
    #         QIntermediate.VALUE: A_int[QIntermediate.VALUE].copy(),
    #         QIntermediate.MEMBERSHIP: A_int[QIntermediate.MEMBERSHIP].copy(),
    #     }
    #
    #     znum_ideal = zn.Znum.Znum([value] * 4, [value] * 4, A_int=A_int, B_int=B_int)
    #     optimization_matrix_znum_ideal = znum_ideal.math.get_matrix()
    #
    #     optimization_matrix_znum_transpose = zip(*optimization_matrix_znum)
    #     optimization_matrix_znum_ideal_transpose = zip(*optimization_matrix_znum_ideal)
    #     result = min([Dist.formula_hellinger(column_znum, column_ideal_znum) for column_znum, column_ideal_znum in zip(optimization_matrix_znum_transpose, optimization_matrix_znum_ideal_transpose)])
    #     return result
