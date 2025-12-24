from enum import Enum


class Algorithms(str, Enum):
    """Enumerates the machine learning algorithms that have been implemented.
    """
    none = "none"
    linear_regression = "LinearRegression"