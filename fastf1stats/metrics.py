from fastf1stats.models import Stat
import pandas as pd

# NOTE FIX/TO-DO --> creaye a mapping from driver_id --> full name or driver code bc pitstops doesn't have it!!!
# NOTE Fix/to-do in V2 --> this logic ignores ties. choosing first row for all options
# NOTE fix later, sprint vs race filter (boolean parameter)


def _rounds(season_df: pd.DataFrame, session_type: str = "R") -> list[int]:
    """Every round number that holds a session of this type, ascending."""
    col = season_df.loc[season_df["session_type"] == session_type, "round_number"]
    return sorted(col.dropna().unique().tolist())


def _cumulative_trend(event_rows: pd.DataFrame, rounds: list[int]) -> list[float]:
    """Running count of `event_rows` (e.g. one driver's wins) across `rounds`.
    Rounds with no matching row contribute 0, so the line steps up only on the
    rounds the thing actually happened."""
    if not rounds:
        return []
    per_round = event_rows.groupby("round_number").size().reindex(rounds, fill_value=0)
    return per_round.cumsum().astype(float).tolist()


def _team_hex(rows: pd.DataFrame) -> str | None:
    """First non-null team_color in `rows`, normalised to '#rrggbb'. Q rows carry
    no colour, so this returns None for pole stats."""
    if "team_color" not in rows.columns:
        return None
    vals = rows["team_color"].dropna()
    if vals.empty:
        return None
    val = str(vals.iloc[0]).strip()
    return "#" + val.lstrip("#") if val else None


def get_best_avg_finish(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    gp_df = season_df[season_df["session_type"] == "R"]
    if gp_df.empty:
        return None

    num_completed_rounds = season_df["round_number"].max()
    MIN_ROUNDS_FOR_AVG = num_completed_rounds / 2

    per_driver = gp_df.groupby("driver_id").agg(
           avg_finish=("position", "mean"), 
           num_races=("position", "count"), # count excludes null values for position

           # carry these values through (first non nullable occurences)
           full_name=("full_name", "first"),
           abbreviation=("abbreviation", "first"),
           team_name=("team_name", "first"))

    candidates = per_driver[per_driver["num_races"] >= MIN_ROUNDS_FOR_AVG]
    if candidates.empty:
        return None

    # NOTE --> This ignores ties bc it selects the first row (fix in V2)
    winner_id = candidates["avg_finish"].idxmin() # min index is the driver id
    winner_row = candidates.loc[winner_id]

    drv_races = gp_df[gp_df["driver_id"] == winner_id].sort_values("round_number")

    return Stat(
        value=float(winner_row["avg_finish"]),
        unit="average",
        driver_name=winner_row["full_name"],
        driver_abbrv=winner_row["abbreviation"],
        team_name=winner_row["team_name"],
        team_color=_team_hex(drv_races),
        # raw finishing position per race - a dip = a good day
        trend=drv_races["position"].dropna().astype(float).tolist(),
    )
    
def get_fastest_pit_stop(pitstop_df: pd.DataFrame) -> Stat | None:
    # NOTE fix --> driving code id mapping  (right now returns driver_id in driver_name which is incorrect)
    if pitstop_df is None or pitstop_df.empty:
            return None
        
    fastest_id = pitstop_df["duration"].idxmin()
    fastest_row = pitstop_df.loc[fastest_id]

    drv_stops = (
        pitstop_df[pitstop_df["driver_id"] == fastest_row["driver_id"]]
        .sort_values("round_number")
    )

    return Stat(
        value=fastest_row["duration"],
        unit="s",
        driver_name=fastest_row["driver_id"],
        round_number=fastest_row["round_number"],
        event_name=fastest_row["event_name"],
        context=f"Lap {fastest_row['lap']}",
        # this driver's stop times across the season, in seconds
        trend=drv_stops["duration"].dt.total_seconds().tolist(),
    )

def get_team_with_most_podiums(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    races_df = season_df[season_df["session_type"] == "R"]
    podium_df = races_df[races_df["position"] <= 3]

    if podium_df.empty:
        return None

    team_podiums = podium_df.groupby("team_name").size()
    winner_team = team_podiums.idxmax()
    winner_rows = podium_df[podium_df["team_name"] == winner_team]

    return Stat(
        value=int(team_podiums.loc[winner_team]),
        unit="podiums",
        team_name=winner_team,
        team_color=_team_hex(winner_rows),
        trend=_cumulative_trend(winner_rows, _rounds(season_df, "R")),
    )

def get_driver_with_most_podiums(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    races_df = season_df[season_df["session_type"] == "R"]
    podium_df = races_df[races_df["position"] <= 3]

    if podium_df.empty:
        return None

    driver_podiums = podium_df.groupby("driver_id").agg(
        num_podiums=("position", "size"),

        # other context
        team_name=("team_name", "first"),
        abbreviation=("abbreviation", "first"),
        full_name=("full_name", "first"))

    winner_index = driver_podiums["num_podiums"].idxmax()
    winner_row = driver_podiums.loc[winner_index]
    winner_rows = podium_df[podium_df["driver_id"] == winner_index]

    return Stat(
        value=int(winner_row["num_podiums"]),
        unit="podiums",
        driver_name=winner_row["full_name"],
        driver_abbrv=winner_row["abbreviation"],
        team_name=winner_row["team_name"],
        team_color=_team_hex(winner_rows),
        trend=_cumulative_trend(winner_rows, _rounds(season_df, "R")),
    )

def get_team_with_most_points(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    results_df = season_df[season_df["session_type"] != "Q"] # takes points from sprints and races

    if results_df.empty:
        return None

    team_points = results_df.groupby("team_name").agg(
        points=("points", "sum"),
    )

    winner_team = team_points["points"].idxmax()

    return Stat(
        value=float(team_points.loc[winner_team, "points"]),
        unit="points",
        team_name=winner_team
    )

def get_driver_with_most_points(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
            return None
    
    results_df = season_df[season_df["session_type"] != "Q"] # takes points from sprints and races
    
    if results_df.empty:
        return None
    
    results_df = results_df.groupby("driver_id").agg(
        points=("points", "sum"),

        # context
        full_name=("full_name", "first"),
        abbreviation=("abbreviation", "first"),
        team_name=("team_name", "first"),
    )
    
    max_index = results_df["points"].idxmax()
    max_row = results_df.loc[max_index]
        
    return Stat(
        value=float(max_row["points"]),
        unit="points",
        driver_name=max_row["full_name"],
        driver_abbrv=max_row["abbreviation"],
        team_name=max_row["team_name"],
    )

def get_team_with_most_wins(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    results_df = season_df[season_df["session_type"] == "R"] # takes wins from only races
    if results_df.empty:
            return None
    
    wins_df = results_df[results_df["position"] == 1]
    if wins_df.empty:
            return None

    team_wins = wins_df.groupby("team_name").size()
    winner_team = team_wins.idxmax()
    winner_rows = wins_df[wins_df["team_name"] == winner_team]

    return Stat(
        value=int(team_wins.loc[winner_team]),
        unit="wins",
        team_name=winner_team,
        team_color=_team_hex(winner_rows),
        trend=_cumulative_trend(winner_rows, _rounds(season_df, "R")),
    )

def get_driver_with_most_wins(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    results_df = season_df[season_df["session_type"] == "R"] # takes wins from only races
    if results_df.empty:
        return None
    
    wins_df = results_df[results_df["position"] == 1]
    if wins_df.empty:
        return None

    driver_wins = wins_df.groupby("driver_id").agg(
        num_wins=("position", "size"),

        # context
        full_name=("full_name", "first"),
        abbreviation=("abbreviation", "first"),
        team_name=("team_name", "first"),
    )

    max_index = driver_wins["num_wins"].idxmax()
    max_row = driver_wins.loc[max_index]
    winner_rows = wins_df[wins_df["driver_id"] == max_index]

    return Stat(
        value=int(max_row["num_wins"]),
        unit="wins",
        driver_name=max_row["full_name"],
        driver_abbrv=max_row["abbreviation"],
        team_name=max_row["team_name"],
        team_color=_team_hex(winner_rows),
        trend=_cumulative_trend(winner_rows, _rounds(season_df, "R")),
    )

def get_biggest_comeback(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None
    
    results_df = season_df[season_df["session_type"] == "R"].copy() # only considering races
    if results_df.empty:
        return None

    results_df["positions_gained"] = results_df["grid_position"] - results_df["position"]
    highest_climber_index = results_df["positions_gained"].idxmax()
    highest_climber_row = results_df.loc[highest_climber_index]

    return Stat(
        value=int(highest_climber_row["positions_gained"]),
        unit="places",
        driver_name=highest_climber_row["full_name"],
        driver_abbrv=highest_climber_row["abbreviation"],
        team_name=highest_climber_row["team_name"],
        team_color=_team_hex(results_df.loc[[highest_climber_index]]),
        # single-race stat - no season series to plot
        round_number=highest_climber_row["round_number"],
        event_name=highest_climber_row["event_name"],
        context=f"final position: {highest_climber_row['position']}"
    )

def get_driver_with_most_poles(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    quali_df = season_df[season_df["session_type"] == "Q"] # only considers race qualifying
    if quali_df.empty:
            return None

    poles_df = quali_df[quali_df["position"] == 1]
    if poles_df.empty:
        return None

    driver_poles = poles_df.groupby("driver_id").agg(
        num_poles=("position", "size"),

        # context
        full_name=("full_name", "first"),
        abbreviation=("abbreviation", "first"),
        team_name=("team_name", "first"))

    winner_index = driver_poles["num_poles"].idxmax()
    winner_row = driver_poles.loc[winner_index]
    winner_rows = poles_df[poles_df["driver_id"] == winner_index]

    return Stat(
        value=int(winner_row["num_poles"]),
        unit="poles",
        driver_name=winner_row["full_name"],
        driver_abbrv=winner_row["abbreviation"],
        team_name=winner_row["team_name"],
        team_color=_team_hex(winner_rows),
        trend=_cumulative_trend(winner_rows, _rounds(season_df, "Q")),
    )

def get_team_with_most_poles(season_df: pd.DataFrame) -> Stat | None:
    if season_df is None or season_df.empty:
        return None

    quali_df = season_df[season_df["session_type"] == "Q"] # only considers race qualifying
    if quali_df.empty:
            return None

    poles_df = quali_df[quali_df["position"] == 1]
    if poles_df.empty:
        return None

    team_poles = poles_df.groupby("team_name").size()
    winner_team = team_poles.idxmax()
    winner_rows = poles_df[poles_df["team_name"] == winner_team]

    return Stat(
        value=int(team_poles.loc[winner_team]),
        unit="poles",
        team_name=winner_team,
        team_color=_team_hex(winner_rows),
        trend=_cumulative_trend(winner_rows, _rounds(season_df, "Q")),
    )
