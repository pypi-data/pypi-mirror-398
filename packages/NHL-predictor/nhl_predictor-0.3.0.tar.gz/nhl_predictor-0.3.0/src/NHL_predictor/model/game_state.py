from enum import Enum


class GameState(str, Enum):
    """Enum mapping game type labels to the numerical value used by the
    NHL API to indicate game type.

    Since the NHL doesn't document their API, value map was obtained
    from here:
    https://github.com/Zmalski/NHL-API-Reference/issues/23#issuecomment-2492925102
    """
    Future = "FUT"
    Pregame = "PRE"
    Live = "LIVE"
    Final = "FINAL"
    Official = "OFF"

# These are the GameStates that indicate player stats are recorded.
GameStatesForDataset = [
    GameState.Official
]

# These are the GameStates where the roster has already been added.
GameStatesForPrediction = [
    GameState.Live,
    GameState.Final,
    GameState.Official
]