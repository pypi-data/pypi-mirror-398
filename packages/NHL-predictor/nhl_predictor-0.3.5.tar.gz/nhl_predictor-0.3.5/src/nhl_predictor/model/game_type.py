from enum import Enum

class GameType(Enum):
    """
    Enum mapping game type labels to the numerical value used by the
    NHL API to indicate game type.

    Since the NHL doesn't document their API, value map was obtained
    from here:
    https://github.com/Zmalski/NHL-API-Reference/issues/23#issuecomment-2492925102
    """
    Preseason = 1
    RegularSeason = 2
    Playoff = 3

# The set of game types that are supported for prediction.
SupportedGameTypes = [
    GameType.RegularSeason,
    GameType.Playoff
]