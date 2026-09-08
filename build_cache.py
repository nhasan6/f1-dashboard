from f1data import ingest, config
from datetime import timedelta
import fastf1
import pyarrow.parquet as pq
from fastf1.exceptions import RateLimitExceededError    
from pathlib import Path
import pandas as pd

config.CACHE_DIR.mkdir(exist_ok=True)
config.DATA_DIR.mkdir(exist_ok=True) # creates folder & stays quiet if folder already exists
fastf1.Cache.enable_cache(config.CACHE_DIR)

GRACE_PERIOD = timedelta(weeks=1.5)
RACE_DURATION_BUFFER = timedelta(hours=6)

def is_safe_to_write(new_df, path):
    if not path.exists():
        return True
    try:
        pf = pq.ParquetFile(path)
        old_row_count = pf.metadata.num_rows
        new_row_count = len(new_df)
        return new_row_count >= old_row_count
    except Exception as err:
        print(f"Error accessing old file: {err}")
        return True # if error accessing current file, just overwrite it 

def refresh_year(year: int, year_dir: Path):
    try:
        season_df = ingest.get_season(year)
    except RateLimitExceededError as err:
        print(f"Rate limit hit for season {year}: {err}")
    except Exception as err:
        print(f"Failed to refresh season for {year}: {err}")
    else: 
        if is_safe_to_write(season_df, year_dir / f"season_{year}.parquet"):
            season_df.to_parquet(year_dir / f"season_{year}.parquet")
            print(f"Refresh {year} season successful")
        else:
            print("Write skipped")

    try:    
        driver_df = ingest.get_drivers_standings(year)
    except RateLimitExceededError as err:
            print(f"Rate limit hit for driver standings {year}: {err}")
    except Exception as err:
        print(f"Failed to refresh driver standings for {year}: {err}")
    else: 
        if is_safe_to_write(driver_df, year_dir / f"driver_standings_{year}.parquet"):
            driver_df.to_parquet(year_dir / f"driver_standings_{year}.parquet")
            print(f"Refresh {year} driver standings successful")
        else:
            print("Write skipped")

    try:    
        constructor_df = ingest.get_constructors_standings(year)
    except RateLimitExceededError as err:
                print(f"Rate limit hit for constructor standings {year}: {err}")
    except Exception as err:
        print(f"Failed to refresh constructor standings for {year}: {err}")
    else: 
        if is_safe_to_write(constructor_df, year_dir / f"constructor_standings_{year}.parquet"):
            constructor_df.to_parquet(year_dir / f"constructor_standings_{year}.parquet")
            print(f"Refresh {year} constructor standings successful")
        else:
            print("Write skipped")

    try:    
        pitstop_df = ingest.get_pitstops(year)
    except RateLimitExceededError as err:
        print(f"Rate limit hit for pitstops {year}: {err}")
    except Exception as err:
        print(f"Failed to refresh pitstops for {year}: {err}")
    else: 
        if is_safe_to_write(pitstop_df, year_dir / f"pitstops_{year}.parquet"):
            pitstop_df.to_parquet(year_dir / f"pitstops_{year}.parquet")
            print(f"Refresh {year} pitstops successful")
        else:
            print("Write skipped")
        
current_year = pd.Timestamp.now().year
# for year in range(config.FIRST_SEASON, current_year + 1):
for year in range(2026, current_year + 1):
    year_dir = config.DATA_DIR / str(year)
    year_dir.mkdir(exist_ok=True, parents=True)    

    missing_parquet_files = (
        not (year_dir / f"season_{year}.parquet").exists() 
        or not (year_dir / f"driver_standings_{year}.parquet").exists() 
        or not (year_dir / f"constructor_standings_{year}.parquet").exists()
        or not (year_dir / f"pitstops_{year}.parquet").exists()
    )

    if missing_parquet_files:
        refresh_year(year, year_dir)
        continue

    schedule = fastf1.get_event_schedule(year, include_testing=False).copy()
    schedule["Session5Date"] = pd.to_datetime(schedule["Session5Date"], utc=True)
    schedule = schedule[schedule["Session5Date"].notna()] # drop rows with no known race date
    current_date = pd.Timestamp.now(tz="UTC")

    if schedule.empty:
        continue

    completed_rounds = schedule[schedule["Session5Date"] + RACE_DURATION_BUFFER < current_date]
    if completed_rounds.empty:
        continue

    last_round_date = completed_rounds["Session5Date"].max()
    if current_date > last_round_date + GRACE_PERIOD:
        print("no new data")
        continue

    refresh_year(year, year_dir)