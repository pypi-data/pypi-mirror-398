from .utils import Beast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from znum.core import Znum


class Vikor:
    # A_PLUS = zn.Znum.Znum([0.99, 0.993, 0.996, 0.999], [0.975, 0.981, 0.986, 0.991])
    # A_MINUS = zn.Znum.Znum([0.001, 0.002, 0.004, 0.005], [0.95, 0.96, 0.97, 0.98])

    @staticmethod
    def solver_main(table):

        weights: list[Znum]
        table_main_part: list[list[Znum]]
        criteria_types: list[str]

        weights, table_main_part, criteria_types = Beast.parse_table(table)

        regret_measurements = Vikor.regret_measure(weights, table_main_part)
        s_measurements = Vikor.s_measure(weights, table_main_part)
        index_q_measurements = Vikor.index_q_measure(regret_measurements, s_measurements)

        regret_measurements_numerated = Beast.numerate(regret_measurements)
        s_measurements_numerated = Beast.numerate(s_measurements)
        index_q_measurements_numerated = Beast.numerate(index_q_measurements)

        regret_measurements_numerated_sorted = Beast.sort_numerated_single_column_table(
            regret_measurements_numerated)
        s_measurements_numerated_sorted = Beast.sort_numerated_single_column_table(s_measurements_numerated)
        index_q_measurements_numerated_sorted = Beast.sort_numerated_single_column_table(
            index_q_measurements_numerated)

        print(regret_measurements_numerated_sorted)
        print(s_measurements_numerated_sorted)
        print(index_q_measurements_numerated_sorted)

        table = Vikor.build_info_table([regret_measurements_numerated_sorted, s_measurements_numerated_sorted,
                                        index_q_measurements_numerated_sorted])
        return regret_measurements

    @staticmethod
    def regret_measure(weights, table_main_part):
        from znum.core import Znum

        A_PLUS = Znum([0.99, 0.993, 0.996, 0.999], [0.975, 0.981, 0.986, 0.991])
        A_MINUS = Znum([0.001, 0.002, 0.004, 0.005], [0.95, 0.96, 0.97, 0.98])

        regret_measurements = []
        for criteriasOfAlternative in table_main_part:
            rs = []
            for (weight, criteriaOfAlternative) in zip(weights, criteriasOfAlternative):
                r = weight * (A_PLUS - criteriaOfAlternative) / (A_PLUS - A_MINUS)
                rs.append(r)
            r_max = max(rs)
            regret_measurements.append(r_max)
        return regret_measurements

    @staticmethod
    def s_measure(weights, table_main_part):
        from znum.core import Znum

        A_PLUS = Znum([0.99, 0.993, 0.996, 0.999], [0.975, 0.981, 0.986, 0.991])
        A_MINUS = Znum([0.001, 0.002, 0.004, 0.005], [0.95, 0.96, 0.97, 0.98])

        s_measurements = []
        for criteriasOfAlternative in table_main_part:
            ss = []
            for (weight, criteriaOfAlternative) in zip(weights, criteriasOfAlternative):
                s = weight * (A_PLUS - criteriaOfAlternative) / (A_PLUS - A_MINUS)
                ss.append(s)
            s_sum = Beast.accurate_sum(ss)
            s_measurements.append(s_sum)
        return s_measurements

    @staticmethod
    def index_q_measure(regret_measurements, s_measurements):
        v = 0.5
        s_min, s_max, r_min, r_max = min(s_measurements), max(s_measurements), min(regret_measurements), max(
            regret_measurements)
        index_q_measurements = []
        for s, r in zip(s_measurements, regret_measurements):
            index_q_measurement = (s - s_min) / (s_max - s_min) * v + (r - r_min) / (r_max - r_min) * (1 - v)
            index_q_measurements.append(index_q_measurement)
        return index_q_measurements

    @staticmethod
    def build_info_table(criterias):
        table = [[i for i in range(len(criterias))] for i in range(len(criterias[0]))]

        for columnIndex, criteria in enumerate(criterias):
            for rowIndex, c in enumerate(criteria):
                table[c[0] - 1][columnIndex] = rowIndex + 1

        return table

    # maganuriyev@gmail.com
