from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from znum.core import Znum
from .exceptions import *


class Valid:
    class Decorator:
        @staticmethod
        def filter_znums(args, callback, exception):
            from znum.core import Znum

            for arg in args:
                if type(arg) is Znum:
                    arg: Znum
                    if callback(arg):
                        raise exception

        @staticmethod
        def check_if_znums_are_even(func):
            def wrapper(*args):
                Valid.Decorator.filter_znums(
                    args, lambda znum: not znum.type.isEven, ZnumMustBeEvenException
                )
                return func(*args)

            return wrapper

        @staticmethod
        def check_if_znums_are_in_same_dimension(func):
            def wrapper(*args):
                from znum.core import Znum

                dimension = None
                for arg in args:
                    if type(arg) is Znum:
                        arg: Znum
                        if not dimension:
                            dimension = arg.dimension
                        else:
                            if dimension != arg.dimension:
                                raise ZnumsMustBeInSameDimensionException()
                return func(*args)

            return wrapper

    def __init__(self, root):
        self.root: Znum = root
        self.validate_A()
        self.validate_B()

    def validate_A(self):
        A = self.root.A
        if not np.all(A[:-1] <= A[1:]):
            raise InvalidAPartOfZnumException()

    def validate_B(self):
        B = self.root.B
        if not np.all(B[:-1] <= B[1:]) or B[-1] > 1 or B[0] < 0:
            raise InvalidBPartOfZnumException()

    def validate(self):
        A, B, C = self.root.A, self.root.B, self.root.C

        if len(A) != len(B):
            raise InvalidZnumDimensionException()

        if len(A) == len(B) != len(C):
            raise InvalidZnumCPartDimensionException()
