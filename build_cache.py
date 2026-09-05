from f1data import ingest, config
from datetime import datetime
import fastf1

config.CACHE_DIR.mkdir(exist_ok=True)
config.DATA_DIR.mkdir(exist_ok=True) # creates folder & stays quiet if folder already exists
fastf1.Cache.enable_cache(config.CACHE_DIR)

current_year = datetime.now().year

for year in range(config.FIRST_SEASON, current_year + 1):
    ingest.get_season(year).to_parquet(config.DATA_DIR / f"season_{year}.parquet")
    ingest.get_drivers_standings(year).to_parquet(config.DATA_DIR / f"driver_standings_{year}.parquet")
    ingest.get_constructors_standings(year).to_parquet(config.DATA_DIR / f"constructor_standings_{year}.parquet")
    ingest.get_pitstops(year).to_parquet(config.DATA_DIR / f"pitstops_{year}.parquet")