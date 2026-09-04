import fastf1
import pandas as pd

from fastf1.ergast import Ergast
ergast = Ergast(result_type="pandas", auto_cast=True)
CACHE_DIR = "/Users/neeyahasan/repositories/fastf1-cache"
fastf1.Cache.enable_cache(CACHE_DIR)

season = 2024
schedule = fastf1.get_event_schedule(season, include_testing=False)
num_rounds = schedule["RoundNumber"].max()
constructors_df = ergast.get_constructor_standings(season).content[0] 
drivers_df = ergast.get_driver_standings(season).content[0]
print(drivers_df.columns.to_list())


# logic to get best avg finish & highest climber

season_races_df = pd.DataFrame()

for index, event in schedule.iterrows():
    print(index)
    session = event.get_race()
    session.load()

    event_df = session.results[["DriverId", "FullName", "TeamName", "Position", "GridPosition", "Status", "Points"]].copy()
    event_df["RoundNumber"] = event.RoundNumber 
    event_df["EventName"] = event.EventName
    season_races_df = pd.concat([season_races_df, event_df], ignore_index=True)


# avg_finish = (season_races_df.groupby(["FullName", "TeamName"], as_index=False)["Position"]
#             .mean()
#             .sort_values("Position", ascending=True))

# best_avg_driver = avg_finish.iloc[0]
# print(best_avg_driver)

season_races_df.dropna(subset=["Position", "GridPosition"])

# season_races_df["PositionsGained"] = season_races_df["GridPosition"] - season_races_df["Position"]
# highest_climber = season_races_df.sort_values("PositionsGained", ascending=False).iloc[0]
# print(highest_climber)


pole_count = season_races_df.loc[season_races_df["GridPosition"] == 1].groupby(["FullName", "TeamName"], as_index=False)["GridPosition"].sum().sort_values("GridPosition", ascending=False)
print(pole_count)

# pole conversion count 
season_races_df["PoleConversions"] = ((season_races_df["GridPosition"] == 1) & (season_races_df["Position"] == 1)).astype(int)
pole_conversions = season_races_df.groupby(["FullName", "TeamName"], as_index=False)["PoleConversions"].sum().sort_values("PoleConversions", ascending=False)
print(pole_conversions.iloc[0])

# drivers_df = drivers_df[["position", "points", "wins", "driverNumber", "givenName", "familyName", "constructorNames", "driverCode"]].set_index("driverCode")
# constructors_df = constructors_df[["position", "points", "wins", "constructorName", "constructorId"]].set_index("constructorId")
# print(constructors_df)
# print(drivers_df)

# # get min pitstop
# best_stop_row = None
# best_stop_duration = None
# for i in range(1, num_rounds + 1):
#     pit_stops_df = ergast.get_pit_stops(season, i).content[0].set_index("driverId")
#     current_duration = pit_stops_df["duration"].min()
#     pit_stop = pit_stops_df[pit_stops_df["duration"] == current_duration].iloc[0]

#     if best_stop_duration is None or best_stop_row is None or current_duration < best_stop_duration:
#         best_stop_duration = current_duration
#         best_stop_row = pit_stop

# print(best_stop_row)

# # # iterrows() gives us an idx and row obj (as a pandas series)
# # # _ means we ignore the idx
# # for _, event in schedule.iterrows(): 

# report_items = [
#     {
#         "title": "Most Wins",
#         "df": "constructors",
#         "metric": "wins",
#         "label_fields": ["constructorName"],
#     },
#     {
#         "title": "Most Points",
#         "df": "constructors",
#         "metric": "points",
#         "label_fields": ["constructorName"],
#     },
#     {
#         "title": "Most Wins",
#         "df": "drivers",
#         "metric": "wins",
#         "label_fields": ["givenName", "familyName"],
#     },
#     {
#         "title": "Most Points",
#         "df": "drivers",
#         "metric": "points",
#         "label_fields": ["givenName", "familyName"],
#     }
# ]


# for report in report_items:
#     if report["df"] == "constructors":
#         df = constructors_df
#     else:
#         df = drivers_df
#     metric = report["metric"]
#     max_value = df[metric].max()
#     winner = df[df[metric] == max_value].iloc[0]

#     print(report["title"])
#     for label in report["label_fields"]:
#         print(winner[label])
#     print(winner[metric])


