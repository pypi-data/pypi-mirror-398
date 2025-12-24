class InvalidAPartOfZnumException(Exception):
    def __init__(self, message="A part of Znum is not valid"):
        super().__init__(message)

class InvalidBPartOfZnumException(Exception):
    def __init__(self, message="B part of Znum is not valid"):
        super().__init__(message)

class InvalidZnumDimensionException(Exception):
    def __init__(self, message="Dimensions of A and B parts should be the same"):
        super().__init__(message)

class InvalidZnumCPartDimensionException(Exception):
    def __init__(self, message="In case A, B are not trapezoid, C must be specified"):
        super().__init__(message)

class IncompatibleABPartsException(Exception):
    def __init__(self, message="Specified A and B are not compatible"):
        super().__init__(message)

class ZnumMustBeEvenException(Exception):
    def __init__(self, message="Znum() must have even number of values in A and B parts"):
        super().__init__(message)

class ZnumsMustBeInSameDimensionException(Exception):
    def __init__(self, message="Znum()s must have the same dimensions (len(A1) == len(A2) == ..."):
        super().__init__(message)
