import time
import fastf1
from fastf1.exceptions import RateLimitExceededError
import pandas as pd
from fastf1stats.config import SEASON_COLS, PITSTOP_COLS

from fastf1.ergast import Ergast
RATE_LIMIT_DELAY = 1.0 # in seconds
ergast = Ergast(result_type="pandas", auto_cast=True)

def get_fastest_laps(session, results):
    fastest_laps = {}

    for abbreviation in results["Abbreviation"]:
        try:
            fastest_laps[abbreviation] = session.laps.pick_drivers(abbreviation).pick_fastest()["LapTime"]
        except RateLimitExceededError:
            raise
        except Exception:
            fastest_laps[abbreviation] = pd.NaT

    return results["Abbreviation"].map(fastest_laps)
            
def get_season(year: int):
    schedule = fastf1.get_event_schedule(year, include_testing=False)

    renamed_columns_mapping = {
            "DriverNumber" : "driver_number",
            "Abbreviation" : "abbreviation",
            "DriverId" : "driver_id",
            "FullName" : "full_name",
            "TeamName" : "team_name",
            "CountryCode" : "country_code",
            "Position" : "position",
            "GridPosition" : "grid_position",
            "Status" : "status",
            "Points" : "points",
            "Laps" : "laps",
            "TeamColor" : "team_color",
            "FastestLap" : "fastest_lap",
            "SessionType" : "session_type",
            "EventDate" : "event_date",
            "RoundNumber" : "round_number",
            "Country" : "country",
            "Location" : "location",
            "EventName" : "event_name"
    }

    if schedule.empty: # given year's schedule dne
        return pd.DataFrame(columns=SEASON_COLS)

    session_dfs = []
    for _, event in schedule.iterrows():
        round_num = event.RoundNumber
        country = event.Country
        location = event.Location
        event_name = event.EventName

        try:
            quali = event.get_qualifying()
            date = quali.date
            quali.load(laps=False, telemetry=False, weather=False, messages=False)
            quali = quali.results

            if not quali.empty:
                quali = quali[["DriverNumber", "Abbreviation", "DriverId", "FullName", "TeamName", "CountryCode", "Position"]].copy()
                quali["SessionType"] = "Q"
                quali["EventDate"] = date

                # general metadata 
                quali["RoundNumber"] = round_num
                quali["Country"] = country
                quali["Location"] = location
                quali["EventName"] = event_name

                # handle NaN values (will occur when pd.concat is run)
                quali["Points"] = 0 # no points are awarded during qualifying
                session_dfs.append(quali)
        except RateLimitExceededError:
            raise
        except Exception as e:
            print(f"Qualifying data failed for round {round_num}: {e}")

        try:
            gp = event.get_race()
            date = gp.date
            gp.load(laps=True, telemetry=False, weather=False, messages=False)
            race_df = gp.results
            if not race_df.empty:
                race_df = race_df[["DriverNumber", "Abbreviation", "DriverId", "FullName", "TeamName", "CountryCode", "Position", "GridPosition", "Status", "Points", "Laps", "TeamColor"]].copy()

                race_df["FastestLap"] = get_fastest_laps(gp, race_df)
                race_df["SessionType"] = "R"
                race_df["EventDate"] = date

                # general metadata 
                race_df["RoundNumber"] = round_num
                race_df["Country"] = country
                race_df["Location"] = location
                race_df["EventName"] = event_name
                session_dfs.append(race_df)
        except RateLimitExceededError:
            raise
        except Exception as e:
            print(f"Race data failed for round {round_num}: {e}")

        try:
            sprint_sess = event.get_sprint()
        except ValueError:
            # event has no sprint
            sprint_sess = None
        except RateLimitExceededError:
            raise
        except Exception as e: # unexpected error
            print(f"Sprint data failed for round {round_num}: {e}")
            sprint_sess = None


        if sprint_sess is not None:
            try: 
                date = sprint_sess.date
                sprint_sess.load(laps=True, telemetry=False, weather=False, messages=False)
                sprint = sprint_sess.results
                if not sprint.empty:
                    sprint = sprint[["DriverNumber", "Abbreviation", "DriverId", "FullName", "TeamName", "CountryCode", "Position", "GridPosition", "Status", "Points", "Laps", "TeamColor"]].copy()

                    sprint["FastestLap"] = get_fastest_laps(sprint_sess, sprint)
                    sprint["SessionType"] = "S"
                    sprint["EventDate"] = date

                    # general metadata 
                    sprint["RoundNumber"] = round_num
                    sprint["Country"] = country
                    sprint["Location"] = location
                    sprint["EventName"] = event_name

                    session_dfs.append(sprint)
            except RateLimitExceededError:
                raise
            except Exception as e:
                # A sprint exists, but loading or processing failed
                print(
                    f"Sprint data failed for round "
                    f"{round_num}: {e}"
                )

        time.sleep(RATE_LIMIT_DELAY)

    if not session_dfs:
        return pd.DataFrame(columns=SEASON_COLS)
    
    season_df = pd.concat(session_dfs, ignore_index=True)

    # clean df 
    season_df = season_df.rename(columns=renamed_columns_mapping)

    season_df["driver_number"] = pd.to_numeric(season_df["driver_number"], errors="coerce")
    season_df[["position", "grid_position", "laps"]] = season_df[["position", "grid_position", "laps"]].astype("Int64")
    season_df[["abbreviation", "driver_id", "full_name", "team_name", "country_code", "country", "location", "event_name", "status", "team_color"]] = season_df[["abbreviation", "driver_id", "full_name", "team_name", "country_code", "country", "location", "event_name", "status", "team_color"]].astype("string")
    season_df["points"] = season_df["points"].astype("float64")
    session_order = ["Q", "S", "R"]
    season_df["session_type"] = pd.Categorical(
        season_df["session_type"],
        categories=session_order,
        ordered=True
    )
    return season_df.sort_values(["event_date", "session_type"]).reset_index(drop=True)

def get_pitstops(year: int):
    renamed_columns_mapping = {"driverId" : "driver_id","RoundNumber" : "round_number", "EventName" : "event_name"}
    
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    if schedule.empty: # given year's schedule dne
        return pd.DataFrame(columns=PITSTOP_COLS)

    session_dfs = []
    for _, event in schedule.iterrows(): 
        round_num = event.RoundNumber
        try:
            response = ergast.get_pit_stops(year, round_num)
            if not response.content or response.content[0].empty:
                continue
            curr_round_stops = response.content[0].copy()
            curr_round_stops["RoundNumber"] = round_num
            curr_round_stops["EventName"] = event.EventName

            session_dfs.append(curr_round_stops)
        except RateLimitExceededError:
            raise
        except Exception as e:
            print(f"Couldn't load pit stops for round {round_num}: {e}")

        time.sleep(RATE_LIMIT_DELAY * 2)
    if not session_dfs:
        return pd.DataFrame(columns=PITSTOP_COLS)
    
    df = pd.concat(session_dfs, ignore_index=True)
    # clean df
    return df.rename(columns=renamed_columns_mapping)