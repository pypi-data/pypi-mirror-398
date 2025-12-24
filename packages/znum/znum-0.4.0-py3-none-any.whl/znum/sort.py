from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from znum.core import Znum


class Sort:
    """x -> anonymous"""

    NXF_OPTIONS = dict(nbF="nbF", neF="neF", nwF="nwF")

    NXF = {
        NXF_OPTIONS["nbF"]: (-1, -1, -0.3, -0.1),
        NXF_OPTIONS["neF"]: (-0.3, -0.1, 0.1, 0.3),
        NXF_OPTIONS["nwF"]: (0.1, 0.3, 1, 1),
    }

    @staticmethod
    def solver_main(znum1: "Znum", znum2: "Znum"):
        (normA1, normA2) = Sort.normalization(znum1.A, znum2.A)

        intermediateA = Sort.get_intermediate(normA1, normA2)
        intermediateB = Sort.get_intermediate(znum1.B, znum2.B)

        intermediates = {"A": intermediateA, "B": intermediateB}
        nxF_Qs_possibilities = {
            Q: {
                option: Sort.nxF_Q_possibility(intermediates[Q], option)
                for option in Sort.NXF_OPTIONS
            }
            for Q in intermediates
        }
        nxF_Qs = {
            Q: {
                option: Sort.nxF_Q(nxF_Qs_possibilities[Q], option)
                for option in Sort.NXF_OPTIONS
            }
            for Q in intermediates
        }

        d = Sort.final_sum(nxF_Qs)
        do = 1 - d

        return d, do

    @staticmethod
    def normalization(q1, q2):
        qs = [*q1, *q2]
        minQ, maxQ = min(qs), max(qs)

        # IMPORTANT: if minQ == maxQ, then all qs are the same, usual normalization will result in division by zero
        # return constant 0
        if minQ == maxQ:
            return [0] * len(q1), [0] * len(q2)

        normalized = [(q - minQ) / (maxQ - minQ) for q in qs]
        return normalized[: len(q1)], normalized[len(q1) :]

    @staticmethod
    def get_intermediate(normQ1, normQ2):
        return [
            q1 - normQ2[len(normQ2) - index - 1] for (index, q1) in enumerate(normQ1)
        ]

    @staticmethod
    def nxF_Q_possibility(
        intermediateA: tuple[float, float, float, float]
        | list[float, float, float, float],
        option,
    ):
        """
        only for 4 corner znum
        a1, a2, ... , b3, b4 may be not the part of znum.A?B
        """

        a1, a2, a3, a4 = intermediateA
        alpha_l, a1, a2, alpha_r = [a2 - a1, a2, a3, a4 - a3]

        b1, b2, b3, b4 = Sort.NXF[option]
        betta_l, b1, b2, betta_r = [b2 - b1, b2, b3, b4 - b3]

        nxF_Q_possibility = Sort.formula_nxF_Q_possibility(
            alpha_l, a1, a2, alpha_r, betta_l, b1, b2, betta_r
        )

        return nxF_Q_possibility

    @staticmethod
    def formula_nxF_Q_possibility(alpha_l, a1, a2, alpha_r, betta_l, b1, b2, betta_r):
        if 0 < a1 - b2 < alpha_l + betta_r:
            return 1 - (a1 - b2) / (alpha_l + betta_r)
        elif max(a1, b1) <= min(a2, b2):
            return 1
        elif 0 < b1 - a2 < alpha_r + betta_l:
            return 1 - (b1 - a2) / (alpha_r + betta_l)
        else:
            return 0

    @staticmethod
    def nxF_Q(nxF_Q_possibilities: dict, option):
        sum_of_nxF_Q_possibilities_except_option = sum(
            (
                nxF_Q_possibilities[_option]
                for _option in nxF_Q_possibilities
                if _option != option
            )
        )
        nxF_Q_possibility = nxF_Q_possibilities[option]
        return nxF_Q_possibility / (
            nxF_Q_possibility + sum_of_nxF_Q_possibilities_except_option
        )

    @staticmethod
    def final_sum(nxF_Qs: dict[dict]):
        nxF_Qs_sum = tuple(
            (a + b) for a, b in zip(*(Q.values() for Q in nxF_Qs.values()))
        )
        Nb, Ne = nxF_Qs_sum[:2]
        return 0 if (2 - Ne) / 2 >= Nb else (2 * Nb + Ne - 2) / Nb
