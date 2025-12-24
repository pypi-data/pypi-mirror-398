import os
from pickle import load
from typing import Dict, List

import numpy as np
import pandas as pd

from model.home_or_away import HomeOrAway
from model.summarizers.summarizer import Summarizer
from model.summarizer_manager import SummarizerTypes
from shared.constants.database import Database as DB
from shared.execution_context import ExecutionContext
from shared.logging_config import LoggingConfig
from shared.constants.json import JSON as Keys
from shared.utility import Utility as utl

logger = LoggingConfig.get_logger(__name__)
execution_context = ExecutionContext()
_summarizer = None
_model = None
_model_filename_part = "LinearRegression"

class PredictLinearRegression:

    @staticmethod
    def predict(
        games: List[int],
    ):
        """Predict the provided games.

        Args:
            games (List[int]): List of game IDs for the games to be predicted.
        """
        game_stats = pd.DataFrame()
        data = utl.get_pandas_tables(
            DB.players_table_name,
            DB.skater_stats_table_name,
            DB.goalie_stats_table_name,
            DB.games_table_name,
            path=execution_context.app_dir,
        )
        results_table = [["Away", "Home", "Predicted", "Raw"]]
        PredictLinearRegression._ensure_summarizer()
        PredictLinearRegression._ensure_model()

        if not games:
            # TODO: Check as precondition?
            logger.warning("No games on the schedule for chosen date(s).")
            return
        games = sorted(games, key=lambda item: item[Keys.id])
        game_stats = _summarizer.summarize_historical(games, data)
        if game_stats.empty:
            logger.warning("None of the specified games have released rosters yet.")
            # TODO: Probably need something here for usability.  Maybe print out
            # a message, an empty results table or even update logging to send
            # warnings to the console?
            print("None of the specified games have released rosters yet.")
            return
        data_pred = _model.predict(
            game_stats
            .sort_values(by=Keys.game_id)
            .drop(columns=Keys.game_id)
        )
        for i in range(len(data_pred)):
            home_team = utl.json_value_or_default(
                games[i],
                Keys.home_team,
                Keys.common_name,
                Keys.default
            )
            away_team = utl.json_value_or_default(
                games[i],
                Keys.away_team,
                Keys.common_name,
                Keys.default
            )
            prediction = HomeOrAway(np.rint(data_pred[i]).astype(int)).name
            results_table.append([away_team, home_team, prediction, str(data_pred[i])])

        utl.print_table(results_table, hasHeader=True)
    
    @staticmethod
    def _ensure_summarizer() -> None:
        """Ensures that the summarizer instance was created.
        """
        global _summarizer
        if _summarizer:
            pass
        else:
            _summarizer = SummarizerTypes.get_summarizer(
                execution_context.summarizer_type
            )
    
    @staticmethod
    def _ensure_model() -> None:
        """Make sure that the model has been loaded.
        
        TODO: Add some error checking here.
        """
        global _model
        if _model:
            pass
        if execution_context.model:
            model_filename = execution_context.model
        else:
            model_filename = f"{_summarizer.get_filename_prefix()}_{_model_filename_part}.pkl"
        with open(os.path.join(execution_context.app_dir, model_filename), "rb") as file:
            _model = load(file)