import math
import numpy as np
from scipy import optimize
from numpy import array
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from znum.core import Znum


class Math:
    METHOD = "highs-ds"
    PRECISION = 6

    class Operations:
        ADDITION = 1
        SUBTRACTION = 2
        DIVISION = 3
        MULTIPLICATION = 4

    class QIntermediate:
        VALUE = "value"
        MEMBERSHIP = "memb"

    operationFunctions = {
        Operations.ADDITION: lambda x, y: x + y,
        Operations.SUBTRACTION: lambda x, y: x - y,
        Operations.MULTIPLICATION: lambda x, y: x * y,
        Operations.DIVISION: lambda x, y: x / y,
    }

    def __init__(self, root: "Znum"):
        self.root = root

    @staticmethod
    def get_default_membership(size):
        half = math.ceil(size / 2)
        arr = [i * (1 / (half - 1)) for i in range(half)]
        return (arr if size % 2 == 0 else arr[:-1]) + list(reversed(arr))

    def get_membership(self, Q, n):
        return self.get_y(n, Q, self.root.C)

    def get_y(self, x, xs, ys):
        result = [
            [x1, x2, y1, y2]
            for [x1, x2, y1, y2] in zip(xs[1:], xs[:-1], ys[1:], ys[:-1])
        ]
        # k * x1 + b = y1
        # k * x2 + b = y2
        # k = (y2 - y1) / (x2 - x1)
        # b = y1 - k * x1
        # y = k * x + b
        for x1, x2, y1, y2 in result:
            if x1 <= x <= x2 or x1 >= x >= x2:
                if y1 == y2:
                    return y1
                k = (y2 - y1) / (x2 - x1)
                b = y1 - k * x1
                y = k * x + b
                return y
        return 0

    def get_intermediate(self, Q):
        left_part = (Q[1] - Q[0]) / self.root.left
        right_part = (Q[3] - Q[2]) / self.root.right

        Q_int_value = np.concatenate(
            (
                [round(Q[0] + i * left_part, 13) for i in range(self.root.left + 1)],
                [round(Q[2] + i * right_part, 13) for i in range(self.root.right + 1)],
                # [1 if self.root.type.isTriangle else 0:]
            )
        )
        Q_int_memb = np.array([self.get_membership(Q, i) for i in Q_int_value])
        return {"value": Q_int_value, "memb": Q_int_memb}

    def get_matrix(self):
        d = 10000

        i37, size = self.get_i37(self.root.A_int), len(self.root.A_int["value"])
        c = np.concatenate([np.zeros(size), (d, d)], axis=0)
        bounds = np.full((size + 2, 2), (0, 1))

        A_eq = array(
            [
                np.concatenate((self.root.A_int["memb"], (-d, d))),
                np.concatenate(([1] * size, (0, 0))),
                np.concatenate((self.root.A_int["value"], (0, 0))),
            ]
        )

        return np.array(
            [
                optimize.linprog(
                    c,
                    A_eq=A_eq,
                    b_eq=array((b20, 1, i37)),
                    bounds=bounds,
                    method=Math.METHOD,
                ).x[:-2]
                for b20 in self.root.B_int["value"]
            ]
        ).T

    @staticmethod
    def get_i37(Q_int):
        return np.dot(Q_int["value"], Q_int["memb"]) / np.sum(Q_int["memb"])

    @staticmethod
    def get_Q_from_matrix(matrix):
        Q = np.empty(4)

        Q[0] = min(matrix, key=lambda x: x[0])[0]
        Q[3] = max(matrix, key=lambda x: x[0])[0]

        matrix = list(filter(lambda x: round(x[1], Math.PRECISION) == 1, matrix))

        Q[1] = min(matrix, key=lambda x: x[0])[0]
        Q[2] = max(matrix, key=lambda x: x[0])[0]

        Q = [round(i, Math.PRECISION) for i in Q]
        return Q

    @staticmethod
    def get_matrix_main(number_z1: "Znum", number_z2: "Znum", operation: int):
        """
        option
        1 - add,
        2 - sub,
        3 - mul,
        4 - div,
        """
        matrix, matrix1, matrix2 = (
            [],
            number_z1.math.get_matrix(),
            number_z2.math.get_matrix(),
        )
        for i, (A1_int_element_value, A1_int_element_memb) in enumerate(
            zip(number_z1.A_int["value"], number_z1.A_int["memb"])
        ):
            for j, (A2_int_element_value, A2_int_element_memb) in enumerate(
                zip(number_z2.A_int["value"], number_z2.A_int["memb"])
            ):
                row = [
                    Math.operationFunctions[operation](
                        A1_int_element_value, A2_int_element_value
                    ),
                    min(A1_int_element_memb, A2_int_element_memb),
                ]
                # element1 * element2 for element1 in matrix1[i] for element2 in matrix2[j]
                matrix.append(row + np.outer(matrix1[i], matrix2[j]).flatten().tolist())
        return matrix

    @staticmethod
    def get_minimized_matrix(matrix):
        minimized_matrix = {}
        for row in matrix:
            if row[0] in minimized_matrix:
                # find max of col2
                minimized_matrix[row[0]][0] = max(minimized_matrix[row[0]][0], row[1])

                # add respective probabilities
                for i, n in enumerate(row[2:]):
                    minimized_matrix[row[0]][i + 1] += n
            else:
                minimized_matrix[row[0]] = row[1:]
        minimized_matrix = [[key] + minimized_matrix[key] for key in minimized_matrix]
        return minimized_matrix

    @staticmethod
    def get_prob_pos(matrix, Number_z1, Number_z2):
        matrix_by_column = list(zip(*matrix))
        column1 = matrix_by_column[1]
        matrix_by_column = matrix_by_column[2:]

        final_matrix = []

        size1 = len(Number_z1.B_int["memb"])
        size2 = len(Number_z2.B_int["memb"])

        for i, column in enumerate(matrix_by_column):
            row = [
                sum([i * j for i, j in zip(column1, column)]),
                min(
                    Number_z1.B_int["memb"][i // size1],
                    Number_z2.B_int["memb"][i % size2],
                ),
            ]
            final_matrix.append(row)
        return final_matrix

    @staticmethod
    def z_solver_main(number_z1, number_z2, operation):
        from znum.core import Znum

        matrix = Math.get_matrix_main(number_z1, number_z2, operation)
        matrix = Math.get_minimized_matrix(matrix)
        A = Math.get_Q_from_matrix(matrix)
        matrix = Math.get_prob_pos(matrix, number_z1, number_z2)
        B = Math.get_Q_from_matrix(matrix)

        return Znum(A, B)
