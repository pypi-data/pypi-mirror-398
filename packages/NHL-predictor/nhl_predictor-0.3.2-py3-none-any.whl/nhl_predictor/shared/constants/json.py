class JSON:
    """Constants related to JSON
    """
    
    default = "default"
    last_update = "lastUpdate"

    # Game related keys.
    games = "games"
    id = "id"
    season = "season"
    game_type = "gameType"
    game_state = "gameState"
    player_by_game_stats = "playerByGameStats"
    home_team = "homeTeam"
    away_team = "awayTeam"
    forwards = "forwards"
    defense = "defense"
    goalies = "goalies"
    
    # Team related keys
    common_name = "commonName"

    # Stat related keys
    goals = "goals"
    assists = "assists"
    points = "points"
    plus_minus = "plusMinus"
    pim = "pim"
    hits = "hits"
    power_play_goals = "powerPlayGoals"
    sog = "sog"
    faceoff_winning_pctg = "faceoffWinningPctg"
    toi = "toi"
    blocked_shots = "blockedShots"
    shifts = "shifts"
    giveaways = "giveaways"
    takeaways = "takeaways"
    even_strength_saves_against = "evenStrengthSavesAgainst"
    even_strength_shots_against = "evenStrengthShotsAgainst"
    power_play_saves_against = "powerPlaySavesAgainst"
    power_play_shots_against = "powerPlayShotsAgainst"
    shorthanded_saves_against = "shorthandedSavesAgainst"
    shorthanded_shots_against = "shorthandedShotsAgainst"
    save_saves_against = "saveSavesAgainst"
    save_shots_against = "saveShotsAgainst"
    save_pctg = "savePctg"
    even_strength_goals_against = "evenStrengthGoalsAgainst"
    power_play_goals_against = "powerPlayGoalsAgainst"
    shorthanded_goals_against = "shorthandedGoalsAgainst"
    goals_against = "goalsAgainst"
    starter = "starter"
    decision = "decision"
    shots_against = "shotsAgainst"
    saves = "saves"

    # Player related keys
    player_id = "playerId"
    game_id = "gameId"
    is_Active = "isActive"
    first_name = "firstName"
    last_name = "lastName"
    current_team_id = "currentTeamId"
    height_in_cm = "heightInCentimeters"
    weight_in_kg = "weightInKilograms"

    # Custom keys. 
    # These are typically key names for the DB that don't exist in
    # the API JSON response formats.
    winner = "winner"
    home_team = "homeTeam"
    away_team= "awayTeam"
    score = "score"
    team_id = "teamId"
    team_role = "teamRole"
    skater_prefix = "skater_"
    goalie_prefix = "goalie_"
    home_suffix = "_home"
    away_suffix = "_away"