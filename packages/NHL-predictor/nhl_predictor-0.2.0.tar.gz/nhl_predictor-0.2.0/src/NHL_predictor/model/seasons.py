from __future__ import annotations
from enum import Enum
from typing import List

class Seasons(str, Enum):
    """
    Seasons to use when fetching data from the API.  This is the data that we will
    be training and testing our model with.

    Since I only care about predicting Kraken performance so I only go back to their
    first year.  I might increase the scope in the future for better accuracy, but
    for now I value the smaller dataset for performance reasons.
    """
    _20222023 = "20222023"
    _20232024 = "20232024"
    _20242025 = "20242025"
    _20252026 = "20252026"

    @classmethod
    def items(cls) -> List[Seasons]:
        """Returns a list of all defined Seasons.

        Returns:
            List[Seasons]: The list of Seasons.
        """
        return [e for e in cls]