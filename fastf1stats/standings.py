import pandas as pd
from fastf1stats import load

def championships_progression(session_df: pd.DataFrame, group_col: str):

    output_colmns = ["round_number", "team_name", "points", "event_name", "team_color", "location", "entity_label", "total_points"]
    if group_col == "driver_id":
        output_colmns.append("driver_id")

    if session_df is None or session_df.empty:
        return pd.DataFrame(columns=output_colmns) 

    session_df = session_df[session_df["session_type"] != "Q"].copy() # include sprints and races

    basic_data = {
        "points": ("points", "sum"),
        "event_name": ("event_name", "first"),
        "location": ("location", "first"),
        "team_color": ("team_color", "first")
    }

    if group_col == "driver_id":
        basic_data["team_name"] = ("team_name", "first")
        label_src = "full_name"
    else:
        label_src = "team_name"

    basic_data["entity_label"] = (label_src, "first")
    grouped = session_df.groupby(["round_number", group_col], as_index=False).agg(**basic_data)
    grouped["total_points"] = grouped.groupby(group_col)["points"].cumsum()
    return grouped

def championship_positions(progression_df: pd.DataFrame):

    if progression_df is None or progression_df.empty:
        # should never be none bc fed directly from championships_progression
        output_cols = progression_df.columns.to_list()
        output_cols.append("position")
        return pd.DataFrame(columns=output_cols) 

    copy_df = progression_df.copy()

    copy_df["position"] = copy_df.groupby("round_number")["total_points"].rank(ascending=False, method="min")
    return copy_df