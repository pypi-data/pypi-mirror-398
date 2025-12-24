from .utils import Beast
from .dist import Dist
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from znum.core import Znum


class Topsis:
    class DataType:
        ALTERNATIVE = "A"
        CRITERIA = "C"
        TYPE = "TYPE"

    class DistanceMethod:
        SIMPLE = 1
        HELLINGER = 2

    def __init__(self, table: list[list], shouldNormalizeWeight=False, distanceType=None):
        """
        Initialize Topsis solver.

        table[0] -> weights
        table[1:-1] -> main part (alternatives)
        table[-1] -> criteria types

        :param table: The decision matrix
        :param shouldNormalizeWeight: Whether to normalize weights
        :param distanceType: Distance method (SIMPLE or HELLINGER). Defaults to HELLINGER.
        """
        self.weights: list[Znum] = table[0]
        self.table_main_part: list[list[Znum]] = table[1:-1]
        self.criteria_types: list[str] = table[-1]
        self.shouldNormalizeWeight = shouldNormalizeWeight
        self.distanceType = distanceType if distanceType is not None else Topsis.DistanceMethod.HELLINGER
        self._result: list[float] | None = None

    def solve(self) -> list[float]:
        """
        Solve the TOPSIS problem and return closeness coefficients.

        :return: List of closeness coefficients for each alternative
        """
        main_table_part_transpose = tuple(zip(*self.table_main_part))

        for column_number, column in enumerate(main_table_part_transpose):
            Beast.normalize(column, self.criteria_types[column_number])

        if self.shouldNormalizeWeight:
            Beast.normalize_weight(self.weights)

        Topsis.weightage(self.table_main_part, self.weights)

        if self.distanceType == Topsis.DistanceMethod.SIMPLE:
            table_1 = Topsis.get_table_n(self.table_main_part, lambda znum: Dist.Simple.calculate(znum, 1))
            table_0 = Topsis.get_table_n(self.table_main_part, lambda znum: Dist.Simple.calculate(znum, 0))
        else:
            table_1 = Topsis.get_table_n(self.table_main_part, lambda znum: Dist.Hellinger.calculate(znum,
                                                                                                Dist.Hellinger.get_ideal_from_znum(
                                                                                                    znum, 1)))
            table_0 = Topsis.get_table_n(self.table_main_part, lambda znum: Dist.Hellinger.calculate(znum,
                                                                                                Dist.Hellinger.get_ideal_from_znum(
                                                                                                    znum, 0)))

        s_best = Topsis.find_extremum(table_1)
        s_worst = Topsis.find_extremum(table_0)
        self._result = Topsis.find_distance(s_best, s_worst)

        return self._result

    @property
    def result(self) -> list[float]:
        """Return the closeness coefficients (must call solve() first)."""
        if self._result is None:
            raise ValueError("Must call solve() before accessing result")
        return self._result

    @property
    def ordered_indices(self) -> list[int]:
        """Return alternative indices sorted by closeness coefficient (best first)."""
        if self._result is None:
            raise ValueError("Must call solve() before accessing ordered_indices")
        return sorted(range(len(self._result)), key=lambda i: self._result[i], reverse=False)

    @property
    def index_of_best_alternative(self) -> int:
        """Return the index of the best alternative."""
        return self.ordered_indices[0]

    @property
    def index_of_worst_alternative(self) -> int:
        """Return the index of the worst alternative."""
        return self.ordered_indices[-1]

    @staticmethod
    def solver_main(table: list[list], shouldNormalizeWeight=False, distanceType=None):
        """
        Static method for backward compatibility.

        table[0] -> weights
        table[1:-1] -> main part
        table[-1] -> criteria types
        :param table:
        :param shouldNormalizeWeight:
        :param distanceType:
        :return:
        """
        if distanceType is None:
            distanceType = Topsis.DistanceMethod.HELLINGER
        topsis = Topsis(table, shouldNormalizeWeight, distanceType)
        return topsis.solve()

    @staticmethod
    def weightage(table_main_part, weights):
        for row in table_main_part:
            for i, (znum, weight) in enumerate(zip(row, weights)):
                row[i] = znum * weight

    @staticmethod
    def get_table_n(table_main_part: list[list['Znum']], distanceSolver):
        table_n = []
        for row in table_main_part:
            row_n = []
            for znum in row:
                number = distanceSolver(znum)
                row_n.append(number)
            table_n.append(row_n)
        return table_n

    @staticmethod
    def find_extremum(table_n: list[list[int]]):
        return [sum(row) for row in table_n]

    @staticmethod
    def find_distance(s_best, s_worst):
        return [worst / (best + worst) for best, worst in zip(s_best, s_worst)]
