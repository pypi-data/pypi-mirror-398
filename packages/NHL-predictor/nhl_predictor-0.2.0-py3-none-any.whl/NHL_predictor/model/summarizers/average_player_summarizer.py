from typing import Dict

import pandas as pd
from sqlitedict import SqliteDict

from model.home_or_away import HomeOrAway
from model.summarizers.summarizer import Summarizer
from shared.constants.database import Database as DB
from shared.constants.json import JSON as Keys
from shared.execution_context import ExecutionContext
from shared.logging_config import LoggingConfig
from shared.utility import Utility as utl

logger = LoggingConfig.get_logger(__name__)
execution_context = ExecutionContext()

class AveragePlayerSummarizer(Summarizer):
    """Summarizer that simply averages or sums, as appropriate, each statistic
    across a game roster.
    """

    def get_filename_prefix() -> str:
        """Returns a prefix for naming the model save file with.

        Returns:
            str: File name prefix.
        """
        return "AverageSummarizer"
    
    def summarize(
        self,
        data: Dict[str, SqliteDict]
    ) -> pd.DataFrame:
        """Creates a single DataFrame containing the summarized data set.

        Args:
            data (Dict[str, SqliteDict]): Collection of raw data.

        Returns:
            pd.DataFrame: DataFrame with one row per game of summarized statistics.
        """
        self._cleanup_data(data)
        return self._reduce_data(data)
    
    def summarize_historical(
        self,
        games: Dict[str, object],
        data: Dict[str, SqliteDict]
    ) -> pd.DataFrame:
        """Summarize the historical player data for players participating in the
        provided games.

        Args:
            games (Dict[str, object]): Set of games to process.
            data (Dict[str, SqliteDict]): Collection of raw data.

        Returns:
            pd.DataFrame: Dataframe with one row per game of summarized statistics.
        """
        
        self._cleanup_data(data)
        # TODO: Can/should we do this in the cleanup method?
        data[DB.skater_stats_table_name] = data[DB.skater_stats_table_name].set_index(Keys.game_id)
        data[DB.goalie_stats_table_name] = data[DB.goalie_stats_table_name].set_index(Keys.game_id)
        
        game_stats = None
        
        for game in games:
            logger.info(f"Processing game. ID: '{utl.json_value_or_default(game, Keys.id)}'.")
            box_score = execution_context.client.game_center.boxscore(
                utl.json_value_or_default(game, Keys.id)
            )
            home_skater_ids = set(
                [item[Keys.player_id] for item in box_score[Keys.player_by_game_stats][Keys.home_team][Keys.forwards]]
                + [item[Keys.player_id] for item in box_score[Keys.player_by_game_stats][Keys.home_team][Keys.defense]]
            )
            away_skater_ids = set(
                [item[Keys.player_id] for item in box_score[Keys.player_by_game_stats][Keys.away_team][Keys.forwards]]
                + [item[Keys.player_id] for item in box_score[Keys.player_by_game_stats][Keys.away_team][Keys.defense]]
            )
            home_goalie_ids = set(
                [item[Keys.player_id] for item in box_score[Keys.player_by_game_stats][Keys.home_team][Keys.goalies]]
            )
            away_goalie_ids = set(
                [item[Keys.player_id] for item in box_score[Keys.player_by_game_stats][Keys.away_team][Keys.goalies]]
            )
            
            new_row = self._flatten_game_players(
                data,
                home_skater_ids,
                home_goalie_ids,
                away_skater_ids,
                away_goalie_ids
            )#.astype(object)
            new_row[Keys.game_id] = (utl.json_value_or_default(game, Keys.id))
            
            if game_stats is None:
                game_stats = pd.DataFrame([new_row])
            else:
                game_stats.loc[len(game_stats)] = new_row
        
        return game_stats.astype({Keys.game_id: 'int64'})

    def _cleanup_data(
        self,
        data: Dict[str, SqliteDict]
    ) -> None:
        """Cleans up the data to prepare for processing.

        Args:
            data (Dict[str, SqliteDict]): Collection of raw data.
        """
        skaters_db = data[DB.skater_stats_table_name]
        goalies_db = data[DB.goalie_stats_table_name]

        # TODO: Fix build-stage bug introducing duplicates then remove this.
        skaters_db = skaters_db.groupby([Keys.game_id, Keys.player_id]).first().reset_index()
        goalies_db = goalies_db.groupby([Keys.game_id, Keys.player_id]).first().reset_index()
        
        skaters_db = self._fix_skater_column_dtypes(skaters_db)
        self._split_compound_goalie_stats(goalies_db)
        goalies_db = self._fix_goalie_column_dtypes(goalies_db)

        data[DB.skater_stats_table_name] = skaters_db
        data[DB.goalie_stats_table_name] = goalies_db

    def _fix_skater_column_dtypes(
        self,
        skaters: pd.DataFrame
    ) -> pd.DataFrame:
        """Corrects the column dtypes for skater data.

        Args:
            skaters (pd.DataFrame): Raw skater data.

        Returns:
            pd.DataFrame: DataFrame with corrected column dtypes.
        """
        return skaters.astype({
            Keys.toi: "string",
        })
    
    def _fix_goalie_column_dtypes(
        self,
        goalies: pd.DataFrame
    ) -> pd.DataFrame:
        """Corrects the column dtypes for goalie data.

        Args:
            goalies (pd.DataFrame): Raw goalie data.

        Returns:
            pd.DataFrame: DataFrame with corrected column dtypes.
        """
        return goalies.astype({
            Keys.even_strength_shots_against: int,
            Keys.power_play_shots_against: int,
            Keys.shorthanded_shots_against: int,
            Keys.save_shots_against: int,
            Keys.toi: "string",
            Keys.decision: "string",
            Keys.even_strength_saves_against: int,
            Keys.power_play_saves_against: int,
            Keys.shorthanded_saves_against: int,
            Keys.save_saves_against: int
        })
    
    # The shot columns provide us with shots againsts, saves against and goals
    # against. Since saves + goals = shots, this may be too much information.
    # There are several columns like this that may be introducing duplicates
    # when split.
    # TODO: Need to unpack if these relationships are bad for the model.
    def _split_compound_goalie_stats(
        self,
        goalies: pd.DataFrame
    ) -> None:
        """Splits columns with compound values into individual columns. Changes are made in place.

        Args:
            goalies (pd.DataFrame): Raw goalie data.
        """
        goalies[[Keys.even_strength_saves_against, Keys.even_strength_shots_against]] = \
            goalies[Keys.even_strength_shots_against].str.split('/', expand=True)
        goalies[[Keys.power_play_saves_against, Keys.power_play_shots_against]] = \
            goalies[Keys.power_play_shots_against].str.split('/', expand=True)
        goalies[[Keys.shorthanded_saves_against, Keys.shorthanded_shots_against]] = \
            goalies[Keys.shorthanded_shots_against].str.split('/', expand=True)
        goalies[[Keys.save_saves_against, Keys.save_shots_against]] = \
            goalies[Keys.save_shots_against].str.split('/', expand=True)

    def _reduce_data(
        self,
        data: Dict[str, SqliteDict]
    ) -> pd.DataFrame:
        """Reduce player stats down to roster stats.

        Args:
            data (Dict[str, SqliteDict]): Collection of raw data.

        Returns:
            pd.DataFrame: DataFrame containing the stats reduced to roster granularity.
        """
        game_stats = self._flatten_all_stats(data)
        game_stats = self._add_wins_column(data, game_stats)
        return game_stats
    
    def _flatten_all_stats(
        self,
        data: Dict[str, SqliteDict]
    ) -> pd.DataFrame:
        """Completely flatten player stats into roster summarized stats.

        Args:
            data (Dict[str, SqliteDict]): Collection of raw data.

        Returns:
            pd.DataFrame: DataFrame with fully flattened stats.
        """
        skaters_db = data[DB.skater_stats_table_name]
        skaters_reduced = self._group_and_flatten_skaters_by_game(skaters_db)
        skaters_reduced = self._flatten_home_and_away_by_game(skaters_reduced, Keys.skater_prefix)
        
        goalies_db = data[DB.goalie_stats_table_name]
        goalies_reduced = self._group_and_flatten_goalies_by_game(goalies_db)
        goalies_reduced = self._flatten_home_and_away_by_game(goalies_reduced, Keys.goalie_prefix)        

        return pd.merge(
            skaters_reduced,
            goalies_reduced,
            how='outer',
            on=Keys.game_id
        )
        
    def _flatten_game_players(
        self,
        data: Dict[str, pd.DataFrame],
        home_skater_ids: set[int],
        home_goalie_ids: set[int],
        away_skater_ids: set[int],
        away_goalie_ids: set[int]
    ) -> pd.Series:
        """Flatten player stats for the provided players.

        Args:
            data (Dict[str, pd.DataFrame]): Collection of raw data.
            home_skater_ids (set[int]): Home skater player IDs.
            home_goalie_ids (set[int]): Home goalie player IDs.
            away_skater_ids (set[int]): Away skater player IDs.
            away_goalie_ids (set[int]): Away goalie player IDs.

        Returns:
            pd.Series: Series containing the summarized stats for this game.
        """
        skater_db = data[DB.skater_stats_table_name]
        goalie_db = data[DB.goalie_stats_table_name]
        
        home_skater_df = self._group_and_flatten_skaters_by_player(skater_db[skater_db[Keys.player_id].isin(home_skater_ids)]).sum()
        away_skater_df = self._group_and_flatten_skaters_by_player(skater_db[skater_db[Keys.player_id].isin(away_skater_ids)]).sum()
        home_goalie_df = self._group_and_flatten_goalies_by_player(goalie_db[goalie_db[Keys.player_id].isin(home_goalie_ids)]).sum()
        away_goalie_df = self._group_and_flatten_goalies_by_player(goalie_db[goalie_db[Keys.player_id].isin(away_goalie_ids)]).sum()
        
        home_skater_df = home_skater_df.add_suffix(Keys.home_suffix).add_prefix(Keys.skater_prefix)
        away_skater_df = away_skater_df.add_suffix(Keys.away_suffix).add_prefix(Keys.skater_prefix)
        home_goalie_df = home_goalie_df.add_suffix(Keys.home_suffix).add_prefix(Keys.goalie_prefix)
        away_goalie_df = away_goalie_df.add_suffix(Keys.away_suffix).add_prefix(Keys.goalie_prefix)
        
        return pd.concat([
            home_skater_df,
            away_skater_df,
            home_goalie_df,
            away_goalie_df
        ])

    def _add_wins_column(
        self,
        data: Dict[str, SqliteDict],
        game_stats: pd.DataFrame
    ) -> pd.DataFrame:
        """Add winner column to the data set DataFrame

        Args:
            data (Dict[str, SqliteDict]): Collection of raw data.
            game_stats (pd.DataFrame): Data set DataFrame

        Returns:
            pd.DataFrame: DataFrame joining the data set DataFrame with the winner data.
        """
        games_db = data[DB.games_table_name]
        games_db.index.name = Keys.game_id # TODO: We should fix this on the build side
        wins = pd.DataFrame(games_db[Keys.winner])
        wins.index = wins.index.astype(int)
        return pd.merge(
            game_stats,
            wins,
            how='left',
            on=Keys.game_id
        )
    
    def _group_and_flatten_skaters_by_player(
        self,
        skaters_db: pd.DataFrame
    ) -> pd.DataFrame:
        """Groups stats entries by player and then flattens skater stats into a single stat line.

        Args:
            skaters_db (pd.DataFrame): Skater data.

        Returns:
            pd.DataFrame: DataFrame with skater stats summarized by game
        """
        skaters_grouped = skaters_db.groupby([Keys.player_id])
        return self._flatten_skater_stats(skaters_grouped, 'mean').set_index(Keys.player_id)
    
    def _group_and_flatten_skaters_by_game(
        self,
        skaters_db: pd.DataFrame
    ) -> pd.DataFrame:
        """Groups stats entries by game and then flattens skater stats into single stat line.

        Args:
            skaters_db (pd.DataFrame): Skater data.

        Returns:
            pd.DataFrame: DataFrame with skater stats summarized by game.
        """
        skaters_grouped = skaters_db.groupby([Keys.game_id, Keys.team_id, Keys.team_role])
        return self._flatten_skater_stats(skaters_grouped)
    
    def _flatten_skater_stats(
        self,
        skaters_db: pd.DataFrame,
        method: str = 'sum'
    ) -> pd.DataFrame:
        """Aggregate skater stats into a single DataFrame

        Args:
            skaters_db (pd.DataFrame): DataFrame to aggregate
            method (str, optional): Specifies the agg method. Defaults to 'sum'.

        Returns:
            pd.DataFrame: Aggregated skater stats.
        """
        return skaters_db.agg({
            Keys.goals: method,
            Keys.assists: method,
            Keys.points: method,
            Keys.plus_minus: method,
            # PIM TODO
            Keys.hits: method,
            Keys.power_play_goals: method,
            Keys.sog: method,
            # faceoffWinningPctg TODO
            # TOI TODO
            Keys.blocked_shots: method,
            Keys.shifts: method,
            Keys.giveaways: method,
            Keys.takeaways: method,
        }).reset_index()
        
    def _group_and_flatten_goalies_by_player(
        self,
        goalies_db: pd.DataFrame
    ) -> pd.DataFrame:
        """Groups stats entries by player and then flattens goalie stats into single stat line.

        Args:
            goalies_db (pd.DataFrame): Goalie data.

        Returns:
            pd.DataFrame: DataFrame with goalie stats summarized by game.
        """
        goalies_grouped = goalies_db.groupby([Keys.player_id])
        return self._flatten_goalie_stats(goalies_grouped, 'mean').set_index(Keys.player_id)
        
    def _group_and_flatten_goalies_by_game(
        self,
        goalies_db: pd.DataFrame
    ) -> pd.DataFrame:
        """Groups stats entries by game and then flattens goalie stats into single stat line.

        Args:
            goalies_db (pd.DataFrame): Goalie data.

        Returns:
            pd.DataFrame: DataFrame with goalie stats summarized by game.
        """
        goalies_grouped = goalies_db.groupby([Keys.game_id, Keys.team_id, Keys.team_role])
        return self._flatten_goalie_stats(goalies_grouped)
    
    def _flatten_goalie_stats(
        self,
        goalies_db: pd.DataFrame,
        method: str = 'sum'
    ) -> pd.DataFrame:
        """Aggregate goalie stats into a single DataFrame

        Args:
            goalies_db (pd.DataFrame): DataFrame to aggregate
            method (str, optional): Specifies the agg method. Defaults to 'sum'.

        Returns:
            pd.DataFrame: Aggregated goalie stats.
        """
        return goalies_db.agg({
            Keys.even_strength_shots_against: method,
            Keys.power_play_shots_against: method,
            Keys.shorthanded_shots_against: method,
            Keys.save_shots_against: method,
            #Keys.save_pctg: goalies_grouped.apply(lambda x: (x[Keys.saves]/x[Keys.shots_against])) TODO
            Keys.even_strength_goals_against: method,
            Keys.power_play_goals_against: method,
            Keys.shorthanded_goals_against: method,
            Keys.pim: method,
            Keys.goals_against: method,
            #TOI TODO
            #starter TODO
            #decision TODO
            Keys.shots_against: method,
            Keys.saves: method,
            Keys.even_strength_saves_against: method,
            Keys.power_play_saves_against: method,
            Keys.shorthanded_saves_against: method,
            Keys.save_saves_against: method,
        }).reset_index()
        
    def _flatten_home_and_away_by_player(
        self,
        home: pd.DataFrame,
        away: pd.DataFrame,
        prefix: str,
    ) -> pd.DataFrame:
        """Combines the HOME and AWAY stats into a single game stats line using the
        provided prefix.

        Args:
            home (pd.DataFrame): The home stats.
            away (pd.DataFrame): The away stats.
            prefix (str): Prefix to add to column names.

        Returns:
            pd.DataFrame: DataFrame with HOME and AWAY rows joined.
        """
        return pd.merge(
            home,
            away,
            how='outer',
            on=Keys.player_id,
            suffixes=(Keys.home_suffix, Keys.away_suffix)
        ).set_index(Keys.player_id).add_prefix(prefix)

    def _flatten_home_and_away_by_game(
        self,
        data: pd.DataFrame,
        prefix: str
    ) -> pd.DataFrame:
        """Splits provided data by HOME or AWAY designation and combines the stats
        into a single game line using provided prefix.

        Args:
            data (pd.DataFrame): DataFrame of data to be flattened.
            prefix (str): Stat type column name prefix.

        Returns:
            pd.DataFrame: DataFrame with HOME and AWAY rows joined.
        """
        home = (
            data[data[Keys.team_role] == HomeOrAway.HOME.value]
            .drop([Keys.team_role, Keys.team_id], axis=1)
        )
        away = (
            data[data[Keys.team_role] == HomeOrAway.AWAY.value]
            .drop([Keys.team_role, Keys.team_id], axis=1)
        )
        return pd.merge(
            home,
            away,
            how='outer',
            on=Keys.game_id,
            suffixes=(Keys.home_suffix, Keys.away_suffix)
        ).set_index(Keys.game_id).add_prefix(prefix)