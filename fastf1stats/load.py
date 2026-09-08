from fastf1stats.config import DATA_DIR, SEASON_COLS, PITSTOP_COLS
import pandas as pd

# printing doesnt do anything --> consider logging

def load_parquet(year: int, file_name):
    if file_name == "season":
        output_cols = SEASON_COLS
    elif file_name == "pitstops":
        output_cols = PITSTOP_COLS
    else:
        output_cols=[]

    try:
        df = pd.read_parquet(DATA_DIR / str(year) / f"{file_name}_{year}.parquet")
    except FileNotFoundError:
        print("File not found")
        return pd.DataFrame(columns=output_cols)
    except Exception as e:
        print(f"Error converting parquet to df: {e}")
        return pd.DataFrame(columns=output_cols)
    return df

def load_season(year: int):
    return load_parquet(year, "season")

# def load_driver_standings(year: int):
#     return load_parquet(year, "driver_standings")

# def load_constructor_standings(year: int): 
#     return load_parquet(year, "constructor_standings")

def load_pitstops(year: int):
    return load_parquet(year, "pitstops")