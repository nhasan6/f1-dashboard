import time
import fastf1
from fastf1.exceptions import RateLimitExceededError
import pandas as pd

from fastf1.ergast import Ergast
RATE_LIMIT_DELAY = 1.0 # in seconds
ergast = Ergast(result_type="pandas", auto_cast=True)

def get_season(year: int):
    schedule = fastf1.get_event_schedule(year, include_testing=False)

    output_columns = [
        "DriverNumber",
        "Abbreviation",
        "DriverId",
        "FullName",
        "TeamName",
        "CountryCode",
        "Position",
        "GridPosition",
        "Status",
        "Points",
        "Laps",
        "TeamColor",
        "FastestLap",
        "SessionType",
        "EventDate",
        "RoundNumber",
        "Country",
        "Location",
        "EventName",
    ]
    
    if schedule.empty: # given year's schedule dne
        return pd.DataFrame(columns=output_columns)

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
        except Exception as error:
            print(f"Qualifying data failed for round {round_num}: {error}")

        try:
            gp = event.get_race()
            date = gp.date
            gp.load(laps=True, telemetry=False, weather=False, messages=False)
            race_df = gp.results
            if not race_df.empty:
                race_df = race_df[["DriverNumber", "Abbreviation", "DriverId", "FullName", "TeamName", "CountryCode", "Position", "GridPosition", "Status", "Points", "Laps", "TeamColor"]].copy()
                for idx, driver in race_df.iterrows():
                    try:
                        race_df.loc[idx, "FastestLap"] = gp.laps.pick_drivers(driver["Abbreviation"]).pick_fastest()["LapTime"]
                    except Exception: # need to update this to the NAT value whatever
                        race_df.loc[idx, "FastestLap"] = pd.NaT # if fastest lap throws an error or is not available
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
        except Exception as error:
            print(f"Race data failed for round {round_num}: {error}")

        try:
            sprint_sess = event.get_sprint()
        except ValueError:
            # event has no sprint
            sprint_sess = None
        except RateLimitExceededError:
            raise
        except Exception as error: # unexpected error
            print(f"Sprint data failed for round {round_num}: {error}")
            sprint_sess = None


        if sprint_sess is not None:
            try: 
                date = sprint_sess.date
                sprint_sess.load(laps=True, telemetry=False, weather=False, messages=False)
                sprint = sprint_sess.results
                if not sprint.empty:
                    sprint = sprint[["DriverNumber", "Abbreviation", "DriverId", "FullName", "TeamName", "CountryCode", "Position", "GridPosition", "Status", "Points", "Laps", "TeamColor"]].copy()
                    for idx, driver in sprint.iterrows():
                        try:
                            sprint.loc[idx, "FastestLap"] = sprint_sess.laps.pick_drivers(driver["Abbreviation"]).pick_fastest()["LapTime"]
                        except Exception: # change to deal with timing value error NaTs
                            sprint.loc[idx, "FastestLap"] = pd.NaT # if fastest lap throws an error or is not available
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
            except Exception as error:
                # A sprint exists, but loading or processing failed
                print(
                    f"Sprint data failed for round "
                    f"{round_num}: {error}"
                )

        time.sleep(RATE_LIMIT_DELAY)

        
    if not session_dfs:
        return pd.DataFrame(columns=output_columns)
    
    season_df = pd.concat(session_dfs, ignore_index=True)

    session_order = ["Q", "S", "R"]
    season_df["SessionType"] = pd.Categorical(
        season_df["SessionType"],
        categories=session_order,
        ordered=True
    )
    return season_df.sort_values(["EventDate", "SessionType"]).reset_index(drop=True)

def get_constructors_standings(year: int):
    output_columns = ["position", "points", "wins", "constructorName", "constructorId"]
    response = ergast.get_constructor_standings(year)
    if not response.content or response.content[0].empty:
        return pd.DataFrame(columns=output_columns)
    df = response.content[0] 
    return df.drop(columns=["constructorUrl"], errors="ignore") # errors = ignore means skip column if dne instead of raising an error

def get_drivers_standings(year: int):
    output_columns = [
        "position", "points", "wins", "driverNumber", "driverCode",
        "givenName", "familyName", "dateOfBirth", "nationality",
        "constructorNames", "driverId",
    ]
    response = ergast.get_driver_standings(year)
    if not response.content or response.content[0].empty:
        return pd.DataFrame(columns=output_columns)
    df = response.content[0]
    return df.drop(columns=["constructorUrls", "driverUrl"], errors="ignore")

def get_pitstops(year: int):
    output_columns = ["driverId", "lap", "stop", "time", "duration", "RoundNumber", "EventName"]
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    if schedule.empty: # given year's schedule dne
        return pd.DataFrame(columns=output_columns)

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
        except Exception as error:
            print(f"Couldn't load pit stops for round {round_num}: {error}")

        time.sleep(RATE_LIMIT_DELAY)
    if not session_dfs:
        return pd.DataFrame(columns=output_columns)
    return pd.concat(session_dfs, ignore_index=True)
