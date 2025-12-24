from typing import List

from daterangeparser import parse as drp
from datetime import datetime, timedelta
import dateutil.parser as parser

from model.algorithms import Algorithms
from predictor.linear_regression import PredictLinearRegression
from shared.constants.json import JSON as Keys
from shared.execution_context import ExecutionContext
from shared.logging_config import LoggingConfig
from shared.utility import Utility as utl

logger = LoggingConfig.get_logger(__name__)
execution_context = ExecutionContext()

class Predictor:
    """Class to manage prediction operations.
    """
    
    def predict_by_date(
        algorithm: Algorithms,
        date: str = None,
        date_range: str = None,
    ) -> None:
        """Start a prediction based on a date or dates.

        Args:
            algorithm (Algorithms): Which ML algorithm to use.
            date (str, optional): Single date filter. Defaults to None.
            date_range (str, optional): Date range filter. Defaults to None.
        """
        games = Predictor._get_games(date, date_range)
        Predictor._predict(algorithm, games)
    
    @staticmethod
    def predict_single_game(
        algorithm: Algorithms,
        game_id: str
    ) -> None:
        """Starts a prediction based on a specific game ID.

        Args:
            algorithm (Algorithms): Which ML algorithm to use.
            game_id (str): The ID of the game to predict.
        """
        game = Predictor._get_game_by_id(game_id)
        Predictor._predict(algorithm, [game])
    
    @staticmethod
    def _predict(
        algorithm: Algorithms,
        games: List[int]
    ) -> None:
        """Core predict method

        Args:
            algorithm (Algorithms): Which ML algorithm to use.
            games (List[int]): List of game IDs to predict for.
        """
        match algorithm:
            case Algorithms.linear_regression:
                PredictLinearRegression.predict(games)
            case _:
                logger.error("Invalid algorithm provided to predict.")
    
    @staticmethod
    def list_games(
        date: str,
        date_range: str
    ) -> None:
        """Print out a report of games on a given date or during a given date range.

        Args:
            date (str): Single date filter.
            date_range (str): Date range filter.
        """
        table = []
        games = Predictor._get_games(date, date_range)
        table.append([Keys.game_id, Keys.away_team, Keys.home_team, Keys.game_state])
        for game in games:
            table.append([
                str(utl.json_value_or_default(game, Keys.id)),
                str(utl.json_value_or_default(game, Keys.away_team, Keys.common_name, Keys.default)),
                str(utl.json_value_or_default(game, Keys.home_team, Keys.common_name, Keys.default)),
                str(utl.json_value_or_default(game, Keys.game_state))
            ])
        utl.print_table(table, hasHeader=True)

    @staticmethod
    def _parse_date_range(
        date_range: str
    ) -> tuple[datetime, datetime]:
        """Parse a date range string into starting and ending datetime instances.

        Args:
            date_range (str): Date range to be parsed.

        Returns:
            tuple[datetime, datetime] Tuple with start and end datetime instances.
        """
        date_range_start = date_range_end = None
        if date_range is not None:
            date_range_start, date_range_end = drp(date_range)
        return date_range_start, date_range_end
    
    @staticmethod
    def _get_games(
        date: str,
        date_range: str
    ) -> List[object]:
        """Get set of games schduled on a given date or during a given date range.

        Args:
            date (str): Single date filter.
            date_range (str): Date range filter.

        Returns:
            List[object]: List of games matching provided date filters.
        """
        date_range_start, date_range_end = Predictor._parse_date_range(date_range)
        if date is not None:
            date = parser.parse(date)
            return Predictor._get_games_for_date(date)
        elif date_range_start is not None and date_range_end is not None:
            return Predictor._get_games_for_date_range(date_range_start, date_range_end)
        else:
            # TODO: Throw?
            logger.error("No valid date option supplied")
            return

    @staticmethod
    def _get_games_for_date_range(
        date_range_start: datetime,
        date_range_end: datetime
    ) -> List[object]:
        """Get the set of games scheduled during a given date range.

        Args:
            date_range_start (datetime): Start of the date range filter.
            date_range_end (datetime): End of the date range filter.

        Returns:
            List[object]: List of game JSON.
        """
        games = []
        number_of_days = (date_range_end - date_range_start).days + 1
        date_list = [date_range_end - timedelta(days=x) for x in range(number_of_days)]
        for date in date_list:
            next_games = Predictor._get_games_for_date(date)
            games.extend(next_games)
        return games

    @staticmethod
    def _get_games_for_date(date: datetime) -> List[object]:
        """Get the set of games scheduled on the given date.

        Args:
            date (datetime): Date filter for games.

        Returns:
            List[object]: List of game JSON.
        """
        schedule = execution_context.client.schedule.daily_schedule(str(date)[:10])
        return schedule["games"]
    
    @staticmethod
    def _get_game_by_id(id: int) -> List[object]:
        """Get game by game ID

        Args:
            id (int): The game ID for the desired game.

        Returns:
            List[object]: List of game JSON.
        """
        return execution_context.client.game_center.boxscore(id)