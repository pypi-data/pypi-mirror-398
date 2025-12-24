import json
from datetime import datetime, timezone
from typing import Dict, List

import requests
from ansimarkup import ansiprint as print
from sqlitedict import SqliteDict

import shared.execution_context
from model.game_state import GameState, GameStatesForDataset
from model.game_type import GameType, SupportedGameTypes
from model.home_or_away import HomeOrAway
from model.seasons import Seasons
from model.team_map import TeamMap
from shared.constants.database import Database as DB
from shared.constants.json import JSON as Keys
from shared.logging_config import LoggingConfig
from shared.utility import Utility as utl

logger = LoggingConfig.get_logger(__name__)
execution_context = shared.execution_context.ExecutionContext()

class Builder:
    """Static class with API to fetch desired data from the public NHL API and
    save it in local databases.
    """
    
    @staticmethod
    def build(
        seasons: List[Seasons],
        all_seasons: bool = False
    ) -> None:
        """Main entry point for the builder.

        Args:
            seasons (List[Seasons]): List of seasons to include in the data set.
            all_seasons (bool, optional): Specify if all seasons should be included. Defaults to False.
        """
        logger.info("Call to build starting.")
        execution_context._ensure_app_dir()
        data = utl.get_sqlitedict_tables(
            DB.players_table_name,
            DB.skater_stats_table_name,
            DB.goalie_stats_table_name,
            DB.games_table_name,
            DB.meta_table_name,
            path=execution_context.app_dir,
            update_db=execution_context.allow_update
        )
        
        if all_seasons:
            Builder._build_stats_by_season(data)
        elif seasons is not None:
            Builder._build_stats_by_season(data, seasons)
        else:
            logger.error("Invalid season specification, cannot build data set.")
        Builder.populate_players(data)
        logger.info("Call to build is complete.")
    
    @staticmethod
    def report() -> None:
        """Prints a report on the current state of the raw data.
        """
        logger.info("Start dataset report.")
        execution_context._ensure_app_dir()
        data = utl.get_sqlitedict_tables(
            DB.players_table_name,
            DB.skater_stats_table_name,
            DB.goalie_stats_table_name,
            DB.games_table_name,
            DB.meta_table_name,
            path=execution_context.app_dir,
            read_only=True
        )
        games_db = data[DB.games_table_name]
        players_db = data[DB.players_table_name]
        skaters_db = data[DB.skater_stats_table_name]
        goalies_db = data[DB.goalie_stats_table_name]
        meta_db = data[DB.meta_table_name]

        # Summarize the games table
        games_summary_table = []
        games_summary_table.append(["Num. Rows", str(len(games_db))])
        games_summary_table.append([
            "Last Updated",
            str(meta_db[DB.games_table_name][Keys.last_update])
        ])

        # Summarize the players table
        players_summary_table = []
        players_summary_table.append(["Num. Rows", str(len(players_db))])
        players_summary_table.append([
            "Last Updated",
            str(meta_db[DB.players_table_name][Keys.last_update])
        ])

        # Summarize the skaters table
        skaters_summary_table = []
        skaters_summary_table.append(["Num. Rows", str(len(skaters_db))])
        skaters_summary_table.append([
            "Last Updated",
            str(meta_db[DB.skater_stats_table_name][Keys.last_update])
        ])

        # Summarize the goalies table
        goalies_summary_table = []
        goalies_summary_table.append(["Num. Rows", str(len(goalies_db))])
        goalies_summary_table.append([
            "Last Updated",
            str(meta_db[DB.goalie_stats_table_name][Keys.last_update])
        ])
        
        # Print all the tables
        print("\n<b><green>GAMES:</green></b>")
        print("<blue>The total number of historical games processed.</blue>")
        utl.print_table(games_summary_table)
        print("\n<b><green>PLAYERS:</green></b>")
        print("<blue>The number of unique players encountered during processing.</blue>")
        utl.print_table(players_summary_table)
        print("\n<b><green>SKATERS:</green></b>")
        print("<blue>The number of skater stat records.  This should be appx. <num_games> * 36</blue>")
        utl.print_table(skaters_summary_table)
        print("\n<b><green>GOALIES:</green></b>")
        print("<blue>The number of goalie stat records.  This should be appx. <num_games> * 4</blue>")
        utl.print_table(goalies_summary_table)
        print("\n")
        print(f"<magenta>Note: Current time UTC is: {datetime.now(timezone.utc)}</magenta>")
        print("\n")

        logger.info("Finished dataset report.")

    @staticmethod
    def _build_stats_by_season(
        data: Dict[str, SqliteDict],
        seasons: List[str] = [x.value for  x in Seasons.items()],
    ) -> None:
        """Iterates over the specified seasons and adds those seasons' data to
        the local database.

        Args:
            data (Dict[str, SqliteDict]): Dictionary of tables to store raw data in.
            seasons (List[str], optional): List of seasons to process. Defaults to all items in Seasons enumeration.
        """
        logger.info("Start building seasons.")
        for season in seasons:
            logger.info(f"Start of processing for season '{season}'.")
            for team in TeamMap:
                logger.info(f"Start processing for team '{team}' in season '{season}'.")
                try:
                    games_raw = execution_context.client.schedule.team_season_schedule(team, season)[Keys.games]
                    logger.info(f"Found '{len(games_raw)}' games for team '{team}' in season '{season}'.")
                    Builder._process_raw_games(games_raw, data)
                except Exception as e:
                    print("<red>Exception occured. Check logs.</red>")
                    logger.exception(
                        f"Exception processing team_season_schedule query. "
                        f"Games: '{json.dumps(games_raw, indent=4)}',"
                        f"Exception: '{str(e)}'.",
                        stack_info=True)
        logger.info("Finished building seasons.")
    
    @staticmethod
    def _process_raw_games(
        games_raw: Dict[str, object],
        data: Dict[str, SqliteDict]
    ) -> None:
        """Iterates over the provided raw game data and adds it to the local
        database.

        Args:
            games_raw (Dict[str, object]): Dictionary with raw game JSON.
            data (Dict[str, SqliteDict]): Dictionary of tables to store raw data
            in.
        """
        logger.info("Start processing game.")
        games_db = data[DB.games_table_name]
        meta_db = data[DB.meta_table_name]

        try:
            for game in games_raw:
                logger.info(f"Processing game: '{game}'.")
                try:
                    if (GameType(utl.json_value_or_default(game, Keys.game_type, default=GameType.Preseason))
                        not in SupportedGameTypes):
                        logger.info(
                            f"Skipping game '{game[Keys.id]}' which is not a "
                            f"supported game type. Type: '{game[Keys.game_type]}'."
                        )
                        continue
                    if (GameState(utl.json_value_or_default(game, Keys.game_state, default=GameState.Future))
                        not in GameStatesForDataset):
                        logger.info(
                            f"Skipping game '{game[Keys.id]}' which is not a "
                            f"supported game state. State: '{game[Keys.game_state]}'."
                        )
                        continue
                    if game[Keys.home_team][Keys.score] > game[Keys.away_team][Keys.score]:
                        winner = HomeOrAway.HOME.value
                    else:
                        winner = HomeOrAway.AWAY.value
                    # game ID is the primary key for the games DB
                    games_db[game[Keys.id]] = {
                        Keys.season: game[Keys.season],
                        Keys.game_type: game[Keys.game_type],
                        Keys.game_state: game[Keys.game_state],
                        Keys.home_team: game[Keys.home_team][Keys.id],
                        Keys.away_team: game[Keys.away_team][Keys.id],
                        Keys.winner: winner
                    }
                except Exception as e:
                    print("\033[31mException occured. Check logs.\033[0m")
                    logger.exception(
                        f"Exception adding game data to database. Exception: "
                        f"'{str(e)}'.",
                        stack_info=True
                    )

                try:
                    box_score = execution_context.client.game_center.boxscore(game[Keys.id])
                    Builder._process_box_score(box_score, data)
                except Exception as e:
                    print("\033[31mException occured. Check logs.\033[0m")
                    logger.exception(
                        f"Exception processing box_score query. Exception: "
                        f"'{str(e)}', box_score: '{json.dumps(box_score, indent=4)}'.",
                        stack_info=True
                    )

            meta_db[DB.games_table_name] = {
                Keys.last_update: datetime.now(timezone.utc)
            }
        except Exception as e:
            print("\033[31mException occured. Check logs.\033[0m")
            logger.exception(
                f"Exception processing team_season_schedule query. Exception: "
                f"'{str(e)}', games: '{json.dumps(games_raw, indent=4)}', "
                f"box_score: '{json.dumps(box_score, indent=4)}'.", stack_info=True
            )
        logger.info("Finished processing game.")

    @staticmethod
    def _process_box_score(
        box_score: Dict[str, object],
        data: Dict[str, SqliteDict]
    ) -> None:
        """Iterates of the provided raw box score data and adds it to the local
        database.

        Args:
            box_score (Dict[str, object]): Dictionary with raw box score JSON.
            data (Dict[str, SqliteDict]): Dictionary of tables to store raw data in.
        """
        logger.info("Processing box_score. BoxScore: '{box_score}'.")
        
        if Keys.player_by_game_stats not in box_score:
            logger.warning("Roster not published yet")
            return None
        
        home_team = utl.json_value_or_default(box_score, Keys.player_by_game_stats, Keys.home_team)
        away_team = utl.json_value_or_default(box_score, Keys.player_by_game_stats, Keys.away_team)

        Builder._process_skaters(
            home_team[Keys.forwards] + home_team[Keys.defense],
            data,
            utl.json_value_or_default(box_score, Keys.id),
            utl.json_value_or_default(box_score, Keys.home_team, Keys.id),
            HomeOrAway.HOME
        )
        Builder._process_goalies(
            home_team[Keys.goalies],
            data,
            utl.json_value_or_default(box_score, Keys.id),
            utl.json_value_or_default(box_score, Keys.home_team, Keys.id),
            HomeOrAway.HOME
        )
        Builder._process_skaters(
            away_team[Keys.forwards] + away_team[Keys.defense],
            data,
            utl.json_value_or_default(box_score, Keys.id),
            utl.json_value_or_default(box_score, Keys.away_team, Keys.id),
            HomeOrAway.AWAY
        )
        Builder._process_goalies(
            away_team[Keys.goalies],
            data,
            utl.json_value_or_default(box_score, Keys.id),
            utl.json_value_or_default(box_score, Keys.away_team, Keys.id),
            HomeOrAway.AWAY
        )

        logger.info("Box score processed.")

    @staticmethod
    def _process_skaters(
        skaters: Dict[str, object],
        data: Dict[str, SqliteDict],
        game_id: str,
        team_id: str,
        team_role: HomeOrAway
    ) -> None:
        """Process the skaters for a given game

        Args:
            skaters (Dict[str, object]): Skater JSON data.
            data (Dict[str, SqliteDict]): Dictionary of tables to store raw data in.
            game_id (str): Game ID for the game represented in the data.
            team_id (str): Team ID for the team represented in the data.
            team_role (HomeOrAway): Team role represented in the data.
        """
        logger.info("Started adding skaters to database.")
        skater_stats_db = data[DB.skater_stats_table_name]
        meta_db = data[DB.meta_table_name]

        for skater in skaters:
            logger.info(f"Processing skater. Skater:'{skater}'.")
            skater_stats_db[len(skater_stats_db)+1] = {
                Keys.game_id: game_id,
                Keys.player_id: utl.json_value_or_default(skater, Keys.player_id),
                Keys.goals: utl.json_value_or_default(skater, Keys.goals),
                Keys.assists: utl.json_value_or_default(skater, Keys.assists),
                Keys.points: utl.json_value_or_default(skater, Keys.points),
                Keys.plus_minus: utl.json_value_or_default(skater, Keys.plus_minus),
                Keys.pim: utl.json_value_or_default(skater, Keys.pim),
                Keys.hits: utl.json_value_or_default(skater, Keys.hits),
                Keys.power_play_goals: utl.json_value_or_default(skater, Keys.power_play_goals),
                Keys.sog : utl.json_value_or_default(skater, Keys.sog),
                Keys.faceoff_winning_pctg: utl.json_value_or_default(skater, Keys.faceoff_winning_pctg),
                Keys.toi: utl.json_value_or_default(skater, Keys.toi),
                Keys.blocked_shots: utl.json_value_or_default(skater, Keys.blocked_shots),
                Keys.shifts: utl.json_value_or_default(skater, Keys.shifts),
                Keys.giveaways: utl.json_value_or_default(skater, Keys.giveaways),
                Keys.takeaways: utl.json_value_or_default(skater, Keys.takeaways),
                Keys.team_id: team_id,
                Keys.team_role: team_role.value
            }

        meta_db[DB.skater_stats_table_name] = {
            Keys.last_update: datetime.now(timezone.utc)
        }
        logger.info("Finished adding skaters to database.")

    @staticmethod
    def _process_goalies(
        goalies: Dict[str, object],
        data: Dict[str, SqliteDict],
        game_id: str,
        team_id: str,
        team_role: HomeOrAway
    ) -> None:
        """Process the goalies in the provided data.

        Args:
            goalies (Dict[str, object]): Goalie JSON data.
            data (Dict[str, SqliteDict]): Dictionary of tables to store raw data in.
            game_id (str): Game ID for the game represented in the data.
            team_id (str): Team ID for the team represented in the data.
            team_role (HomeOrAway): Team role represented in the data.
        """
        logger.info("Started adding goalies to database.")
        goalie_stats_db = data[DB.goalie_stats_table_name]
        meta_db = data[DB.meta_table_name]

        for goalie in goalies:
            logger.info(f"Processing goalie. Goalie:'{goalie}'.")
            goalie_stats_db[len(goalie_stats_db)+1] = {
                Keys.game_id: game_id,
                Keys.player_id: utl.json_value_or_default(goalie, Keys.player_id),
                Keys.even_strength_shots_against: utl.json_value_or_default(goalie, Keys.even_strength_shots_against),
                Keys.power_play_shots_against: utl.json_value_or_default(goalie, Keys.power_play_shots_against),
                Keys.shorthanded_shots_against: utl.json_value_or_default(goalie, Keys.power_play_shots_against),
                Keys.save_shots_against: utl.json_value_or_default(goalie, Keys.save_shots_against),
                Keys.save_pctg: utl.json_value_or_default(goalie, Keys.save_pctg),
                Keys.even_strength_goals_against: utl.json_value_or_default(goalie, Keys.even_strength_goals_against),
                Keys.power_play_goals_against: utl.json_value_or_default(goalie, Keys.power_play_goals_against),
                Keys.shorthanded_goals_against: utl.json_value_or_default(goalie, Keys.shorthanded_goals_against),
                Keys.pim: utl.json_value_or_default(goalie, Keys.pim),
                Keys.goals_against: utl.json_value_or_default(goalie, Keys.goals_against),
                Keys.toi: utl.json_value_or_default(goalie, Keys.toi),
                Keys.starter: utl.json_value_or_default(goalie, Keys.starter),
                Keys.decision: utl.json_value_or_default(goalie, Keys.decision),
                Keys.shots_against: utl.json_value_or_default(goalie, Keys.shots_against),
                Keys.saves: utl.json_value_or_default(goalie, Keys.saves),
                Keys.team_id: team_id,
                Keys.team_role: team_role.value
            }

        meta_db[DB.goalie_stats_table_name] = {
            Keys.last_update: datetime.now(timezone.utc)
        }
        logger.info("Finished adding goalies to database.")

    @staticmethod
    def populate_players(
        data: Dict[str, SqliteDict]
    ) -> None:
        """Populate the players into the players table.

        Args:
            data (Dict[str, SqliteDict]): Dictionary of tables to store raw data in.
        """
        logger.info("Started adding players to database.")
        players_db = data[DB.players_table_name]
        meta_db = data[DB.meta_table_name]
        
        # I don't find this endpoint in the nhlpy APIs. Making a manual request
        # to get all active players.
        url = "https://search.d3.nhle.com/api/v1/search/player"
        params = dict(
            culture="en-us",
            limit="50000",
            q="*",
            active="true"
        )
        resp = requests.get(url=url, params=params)
        players_json = resp.json()

        if not players_json:
            logger.error("Unable to get JSON response content from players query.")
        else:
            for player in players_json:
                logger.info(f"Processing player: Player: '{player}'.")
                player_id = utl.json_value_or_default(player, Keys.player_id, default=None)
                stats = execution_context.client.stats.player_career_stats(player_id)
                first_name = utl.json_value_or_default(stats, Keys.first_name, Keys.default, default="")
                last_name = utl.json_value_or_default(stats, Keys.last_name, Keys.default, default="")
                players_db[player_id] = {
                    Keys.current_team_id: utl.json_value_or_default(stats, Keys.current_team_id),
                    Keys.first_name: first_name,
                    Keys.last_name: last_name,
                    Keys.height_in_cm: utl.json_value_or_default(stats, Keys.height_in_cm),
                    Keys.weight_in_kg: utl.json_value_or_default(stats, Keys.weight_in_kg)
                }
                logger.info(f"Added player '{last_name}, {first_name}' to players table.")

            meta_db[DB.players_table_name] = {
                Keys.last_update: datetime.now(timezone.utc)
            }
        logger.info("Finished adding players to database.")