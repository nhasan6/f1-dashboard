from pathlib import Path

# This file lives at  <repo>/f1data/config.py
#   Path(__file__)   -> ".../f1data/config.py"  (path to THIS file)
#   .resolve()       -> make it absolute, collapse ".." and symlinks
#   .parent          -> ".../f1data"
#   .parent          -> ".../"          <- the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent

# fastf1's on-disk response cache
CACHE_DIR = _REPO_ROOT / ".fastf1cache"

# committed Parquet season files (deployed app reads ONLY from here)
DATA_DIR = _REPO_ROOT / "data"

# earliest season the dashboard supports 
FIRST_SEASON = 2018