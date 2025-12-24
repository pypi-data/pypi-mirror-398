from enum import Enum

class HomeOrAway(Enum):
    """
    Designates a team as Home or Away.
    """
    AWAY = -1
    UNDECIDED = 0
    HOME = 1