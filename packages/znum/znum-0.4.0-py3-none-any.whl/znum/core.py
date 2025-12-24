import numpy as np
from .math_ops import Math
from .sort import Sort
from .topsis import Topsis
from .promethee import Promethee
from .utils import Beast
from .vikor import Vikor
from .valid import Valid
from .ztype import Type
from .dist import Dist


class Znum:
    Vikor = Vikor
    Topsis = Topsis
    Sort = Sort
    Promethee = Promethee
    Beast = Beast
    Math = Math
    Dist = Dist

    def __init__(self, A=None, B=None, left=4, right=4, C=None, A_int=None, B_int=None):
        self._A = np.array(A if A is not None else Znum.get_default_A(), dtype=float)
        self._B = np.array(B if B is not None else Znum.get_default_B(), dtype=float)
        if self._B[-1] < 0.001:
            for i in range(len(self._B)):
                self._B[i] += 1e-6 * (i + 1)
        self._C = np.array(C if C is not None else Znum.get_default_C(), dtype=float)

        # IMPORTANT: if all elements of A are equal, membership for all values is 1, number is "exact"
        if np.all(self._A == self._A[0]):
            self._C = np.ones(len(self._A))

        self._dimension = len(self._A)
        self.left, self.right = left, right
        self.math = Math(self)
        self.valid = Valid(self)
        self.type = Type(self)
        self.A_int = A_int or self.math.get_intermediate(self._A)
        self.B_int = B_int or self.math.get_intermediate(self._B)

    @property
    def A(self):
        return self._A

    @A.setter
    def A(self, A):
        self._A = np.array(A, dtype=float)
        self.A_int = self.math.get_intermediate(self._A)

    @property
    def B(self):
        return self._B

    @B.setter
    def B(self, B):
        self._B = np.array(B, dtype=float)
        self.B_int = self.math.get_intermediate(self._B)

    @property
    def C(self):
        return self._C

    @C.setter
    def C(self, C):
        self._C = np.array(C, dtype=float)

    @property
    def dimension(self):
        return len(self._A)

    @staticmethod
    def get_default_A():
        return np.array([1, 2, 3, 4], dtype=float)

    @staticmethod
    def get_default_B():
        return np.array([0.1, 0.2, 0.3, 0.4], dtype=float)

    @staticmethod
    def get_default_C():
        return np.array([0, 1, 1, 0], dtype=float)

    def __str__(self):
        return "Znum(A=" + str(self.A.tolist()) + ", B=" + str(self.B.tolist()) + ")"

    def __repr__(self) -> str:
        return self.__str__()

    def __add__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        return self.math.z_solver_main(self, other, Math.Operations.ADDITION)

    def __mul__(self, other):
        """
        :type other: Union[Znum, int, float]
        """
        if isinstance(other, Znum):
            return self.math.z_solver_main(self, other, Math.Operations.MULTIPLICATION)
        if isinstance(other, (float, int)):
            return Znum(A=self.A * other, B=self.B.copy())
        else:
            raise Exception(f"Znum cannot multiplied by a data type {type(other)}")

    def __sub__(self, other):
        return self.math.z_solver_main(self, other, Math.Operations.SUBTRACTION)

    def __truediv__(self, other):
        return self.math.z_solver_main(self, other, Math.Operations.DIVISION)

    def __pow__(self, power, modulo=None):
        return Znum(A=self.A**power, B=self.B.copy())

    def __gt__(self, o: "Znum"):
        d, do = Znum.Sort.solver_main(self, o)
        _d, _do = Znum.Sort.solver_main(o, self)
        return do > _do

    def __lt__(self, o: "Znum"):
        d, do = Znum.Sort.solver_main(self, o)
        _d, _do = Znum.Sort.solver_main(o, self)
        return do < _do

    def __eq__(self, o):
        d, do = Znum.Sort.solver_main(self, o)
        _d, _do = Znum.Sort.solver_main(o, self)
        return do == 1 and _do == 1

    def __ge__(self, o: "Znum"):
        d, do = Znum.Sort.solver_main(self, o)
        _d, _do = Znum.Sort.solver_main(o, self)
        return do >= _do

    def __le__(self, o: "Znum"):
        d, do = Znum.Sort.solver_main(self, o)
        _d, _do = Znum.Sort.solver_main(o, self)
        return do <= _do

    def copy(self):
        return Znum(A=self.A.copy(), B=self.B.copy())

    def to_json(self):
        return {"A": self.A.tolist(), "B": self.B.tolist()}

    def to_array(self):
        return np.concatenate([self._A, self._B])

    def __radd__(self, other):
        if isinstance(other, (int, float)) and other == 0:
            return self
        return self + other
