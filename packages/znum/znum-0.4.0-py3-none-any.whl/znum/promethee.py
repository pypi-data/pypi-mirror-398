from .utils import Beast
from .sort import Sort
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from znum.core import Znum


class Promethee:
    def __init__(self, table: list[list], shouldNormalizeWeight=False):
        self.weights: list[Znum] = table[0]
        self.table_main_part: list[list[Znum]] = table[1:-1]
        self.criteria_types: list[str] = table[-1]
        self.sorted_table = None

        if shouldNormalizeWeight:
            Beast.normalize_weight(self.weights)

    @staticmethod
    def calculate_preference_table(table_main_part: list[list["Znum"]]):
        preference_table = []
        for indexAlternative, alternative in enumerate(table_main_part):
            alternativeRow = []
            for indexOtherAlternative, otherAlternative in enumerate(table_main_part):
                if indexAlternative != indexOtherAlternative:
                    otherAlternativeRow = []
                    for criteria, otherCriteria in zip(alternative, otherAlternative):
                        (d1, do1) = Sort.solver_main(criteria, otherCriteria)
                        (d2, do2) = Sort.solver_main(otherCriteria, criteria)
                        d = do1 - do2
                        d = d if d > 0 else 0
                        otherAlternativeRow.append(d)
                    alternativeRow.append(otherAlternativeRow)
                else:
                    alternativeRow.append([])

            preference_table.append(alternativeRow)
        return preference_table

    @staticmethod
    def weightage(preference_table, weights):
        for preferenceByCategoriesByAlternatives in preference_table:
            for preferenceByCategories in preferenceByCategoriesByAlternatives:
                for index, (preferenceByCategory, weight) in enumerate(
                    zip(preferenceByCategories, weights)
                ):
                    preferenceByCategories[index] = (
                        weight * preferenceByCategory
                    )  # order is Znum() * Number()

    @staticmethod
    def sum_preferences_of_same_category_pair(preference_table):
        for preferenceByCategoriesByAlternatives in preference_table:
            for index, preferenceByCategories in enumerate(
                preferenceByCategoriesByAlternatives
            ):
                preferenceByCategoriesByAlternatives[index] = sum(
                    preferenceByCategories
                )

    @staticmethod
    def vertical_alternative_sum(preference_table):
        return [sum(column) for column in zip(*preference_table)]

    @staticmethod
    def horizontal_alternative_sum(preference_table):
        return [sum(row) for row in preference_table]

    @staticmethod
    def numerate(single_column_table: list["Znum"]):
        return list(enumerate(single_column_table, 0))

    @staticmethod
    def sort_numerated_single_column_table(single_column_table: list["Znum"]):
        sorted_table = tuple(
            sorted(single_column_table, reverse=True, key=lambda x: x[1])
        )
        return sorted_table

    def solve(self):
        table_main_part_transpose = tuple(zip(*self.table_main_part))
        for column_number, column in enumerate(table_main_part_transpose):
            Beast.normalize(column, self.criteria_types[column_number])

        preference_table = Promethee.calculate_preference_table(self.table_main_part)

        Promethee.weightage(preference_table, self.weights)
        Promethee.sum_preferences_of_same_category_pair(preference_table)

        vertical_sum = Promethee.vertical_alternative_sum(preference_table)
        horizontal_sum = Promethee.horizontal_alternative_sum(preference_table)

        # horizontal_sum - vertical_sum
        table_to_sort = Beast.subtract_matrix(horizontal_sum, vertical_sum)

        numerated_table_to_sort = Promethee.numerate(table_to_sort)
        sorted_table = Promethee.sort_numerated_single_column_table(
            numerated_table_to_sort
        )

        self.sorted_table = sorted_table
        return sorted_table

    @property
    def ordered_indices(self):
        return [r[0] for r in self.sorted_table]

    @property
    def index_of_best_alternative(self):
        return self.ordered_indices[0]

    @property
    def index_of_worst_alternative(self):
        return self.ordered_indices[-1]
