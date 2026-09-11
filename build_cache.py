from fastf1stats import ingest, config
from datetime import timedelta
import time
import fastf1
import pyarrow.parquet as pq
from fastf1.exceptions import RateLimitExceededError    
from pathlib import Path
import pandas as pd
import sys
import argparse

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
    except Exception as e:
        print(f"Error accessing old file: {e}")
        return True # if error accessing current file, just overwrite it 
    
def refresh_season(year: int, year_dir: Path) -> bool:
    try:
        season_df = ingest.get_season(year)
    except RateLimitExceededError as e:
        print(f"Rate limit hit for season {year}: {e}")
        return False
    except Exception as e:
        print(f"Failed to refresh season for {year}: {e}")
        return False
    else: 
        # if is_safe_to_write(season_df, year_dir / f"season_{year}.parquet"):
        season_df.to_parquet(year_dir / f"season_{year}.parquet")
        print(f"Refresh {year} season successful")
        # else:
        #     print("Write skipped")
        return True 

def refresh_pitstops(year: int, year_dir: Path) -> bool:
    try:    
        pitstop_df = ingest.get_pitstops(year)
    except RateLimitExceededError as e:
        print(f"Rate limit hit for pitstops {year}: {e}")
        return False
    except Exception as e:
        print(f"Failed to refresh pitstops for {year}: {e}")
        return False
    else: 
        if is_safe_to_write(pitstop_df, year_dir / f"pitstops_{year}.parquet"):
            pitstop_df.to_parquet(year_dir / f"pitstops_{year}.parquet")
            print(f"Refresh {year} pitstops successful")
        else:
            print("Write skipped") # skipped isn't necessarily an api failure, so we'll return true for now
        return True 

def main():   
    parser = argparse.ArgumentParser(description="indicates if entire database or just a specific year needs to be loaded")
    group = parser.add_mutually_exclusive_group() # can't backfill and do --year at the same time (optional flags mean defaults to current year only)
    group.add_argument("--year", type=int) # None when omitted
    group.add_argument("--backfill", action="store_true") # defaults to False when omitted
    args = parser.parse_args()

    current_year = pd.Timestamp.now().year
    if args.backfill:
        years = range(config.FIRST_SEASON, current_year + 1)
    elif args.year is not None:
        if not (config.FIRST_SEASON <= args.year <= current_year):
            parser.error(f"--year must be between {config.FIRST_SEASON} and {current_year}")
        years = [args.year]
    else:
        years = [current_year]

    any_failed = False # any data fetching 
  
    for year in years:
        year_dir = config.DATA_DIR / str(year)
        year_dir.mkdir(exist_ok=True, parents=True)    

        season_path = year_dir / f"season_{year}.parquet"
        pitstops_path = year_dir / f"pitstops_{year}.parquet"
        
        backfilled = False

        if not season_path.exists():
            if not refresh_season(year, year_dir):
                any_failed = True
            time.sleep(15)
            backfilled = True

        if not pitstops_path.exists():
            if not refresh_pitstops(year, year_dir):
                any_failed = True
            time.sleep(15)
            backfilled = True

        if backfilled:
            continue

        schedule = fastf1.get_event_schedule(year, include_testing=False)
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

        if not refresh_season(year, year_dir):
            any_failed = True
        time.sleep(60) # wait a minute b4 querying for next pitstops
        if not refresh_pitstops(year, year_dir):
            any_failed = True

    if any_failed:
        sys.exit(1) # non-zero --> alerts GitHub Actions

if __name__ == "__main__":
    main()