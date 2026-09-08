from pathlib import Path

# This file lives at  <repo>/fastf1stats/config.py
#   Path(__file__)   -> ".../fastf1stats/config.py"  (path to THIS file)
#   .resolve()       -> make it absolute, collapse ".." and symlinks
#   .parent          -> ".../fastf1stats"
#   .parent          -> ".../"          <- the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent

# fastf1's on-disk response cache
CACHE_DIR = _REPO_ROOT / ".fastf1cache"

# committed Parquet season files (deployed app reads ONLY from here)
DATA_DIR = _REPO_ROOT / "data"

# earliest season the dashboard supports 
FIRST_SEASON = 2018

# output columns for df 
SEASON_COLS = [ 
    "driver_number",
    "abbreviation",
    "driver_id",
    "full_name",
    "team_name",
    "country_code",
    "position",
    "grid_position",
    "status",
    "points",
    "laps",
    "team_color",
    "fastest_lap",
    "session_type",
    "event_date",
    "round_number",
    "country",
    "location",
    "event_name"
]

PITSTOP_COLS = ["driver_id", "lap", "stop", "time", "duration", "round_number", "event_name"]