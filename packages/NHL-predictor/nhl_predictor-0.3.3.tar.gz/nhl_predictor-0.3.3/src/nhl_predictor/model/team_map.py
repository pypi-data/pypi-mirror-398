# Some APIs require the team abbreviation, others require
# the franchise ID. The main API that we're using takes the
# abbreviation, so we use that as our key and iterate. When
# needed, we can use the map to find the franchise ID to use
# when calling subsequent APIs.
TeamMap = {
    "MTL": 1,               # Canadiens
    "TOR": 5,               # Maple Leafs
    "BOS": 6,               # Bruins
    "NYR": 10,              # Rangers
    "CHI": 11,              # Blackhawks
    "DET": 12,              # Red Wings
    "LAK": 14,              # Kings
    "DAL": 15,              # Stars
    "PHI": 16,              # Flyers
    "PIT": 17,              # Penguins
    "STL": 18,              # Blues
    "BUF": 19,              # Sabres
    "VAN": 20,              # Canucks
    "CGY": 21,              # Flames
    "NYI": 22,              # Islanders
    "NJD": 23,              # Jersey Devils
    "WSH": 24,              # Capitals
    "EDM": 25,              # Oilers
    "CAR": 26,              # Hurricanes
    "COL": 27,              # Avalanche
    "SJS": 29,              # Sharks
    "OTT": 30,              # Senators
    "TBL": 31,              # Lightning
    "ANA": 32,              # Ducks
    "FLA": 33,              # Panthers
    "NSH": 34,              # Predators
    "WPG": 35,              # Jets
    "CBJ": 36,              # Blue Jackets
    "MIN": 37,              # Wild
    "VGK": 38,              # Golden Knights
    "SEA": 55,              # Kraken
    "UTA": 40,              # Mammoth
    "ARI": 40,              # Arizona -- Back compat for Mammoth
}