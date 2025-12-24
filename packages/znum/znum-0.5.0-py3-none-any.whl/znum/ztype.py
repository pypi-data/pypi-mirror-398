from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from znum.core import Znum


class Type:
    TRIANGLE = 1
    TRAPEZOID = 2
    EVEN = 2
    ANY = 3
    IDEAL = 4

    def __init__(self, root: 'Znum'):
        self.root = root
        self.value = self.get_type()

    def get_type(self):
        A, B = self.root.A, self.root.B
        #  == len(B) is not required; added just for readability
        if len(A) == 4:
            # if A[1] == A[2] and B[1] == B[2]:
            #     return Type.TRIANGLE
            # else:
            return Type.TRAPEZOID
        else:
            return Type.ANY

    @property
    def isTrapezoid(self):
        return self.value == Type.TRAPEZOID

    @property
    def isTriangle(self):
        return self.value == Type.TRIANGLE

    @property
    def isIdeal(self):
        return self.value == Type.IDEAL

    @property
    def isEven(self):
        return len(self.root.A) % 2 == 0