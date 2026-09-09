import streamlit as st
from fastf1stats import load
from fastf1stats import metrics, standings, charts
import ui.components as components
from fastf1stats.config import FIRST_SEASON
import pandas as pd

@st.cache_data()
def load_year(year: int):
    return load.load_season(year)

@st.cache_data()
def load_pitstops_in_year(year: int):
    return load.load_pitstops(year)

def headline_stats(season_df: pd.DataFrame):
    quick_stats = {}
    funcs = { "driver_wins" : metrics.get_driver_with_most_wins, 
             "team_wins" : metrics.get_team_with_most_wins,
             "driver_podiums" : metrics.get_driver_with_most_podiums,
             "team_podiums" : metrics.get_team_with_most_podiums,
             "driver_poles" : metrics.get_driver_with_most_poles,
             "team_poles": metrics.get_team_with_most_poles
             }

    for key, val in funcs.items():
        quick_stats[key] = val(season_df)
    return quick_stats

st.set_page_config(
    page_title="Formula 1 Live Dashboard",
    page_icon=":material/sports_motorsports:",
    layout="wide",
)
st.logo("ui/logo.svg")
st.title("Formula 1 Dashboard")
st.caption("“The stopwatch never lies.” — Toto Wolff")
year = st.selectbox("Year", list(range(pd.Timestamp.now().year, FIRST_SEASON - 1, -1))) # first option is selected by default (needs to be most recent year)

# dataframes
season_df = load_year(year)
pitstop_df = load_pitstops_in_year(year)

# computed data
stats = headline_stats(season_df)

# consts 

# each spec: (title, driver stat, team stat, icon) - row 1
split_specs = [
    ("Most Wins", stats["driver_wins"], stats["team_wins"], ":material/trophy:"),
    ("Most Podiums", stats["driver_podiums"], stats["team_podiums"], ":material/workspace_premium:"),
    ("Most Poles", stats["driver_poles"], stats["team_poles"], ":material/bolt:"),
]

# each spec: (title, stat, icon) - row 2
single_specs = [
    ("Best Average Finish", metrics.get_best_avg_finish(season_df), ":material/target:"),
    ("Biggest Comeback", metrics.get_biggest_comeback(season_df), ":material/trending_up:"),
    ("Fastest Pit Stop", metrics.get_fastest_pit_stop(pitstop_df), ":material/timer:")
] 

# stats grid
st.subheader(f"{year} Season Overview", divider="gray")

for col, (title, d, t, icon) in zip(st.columns(3), split_specs):
    with col:
        components.split_stat_card(title, d, t, icon)

for col, (title, s, icon) in zip(st.columns(3), single_specs):
    with col:
        components.single_stat_card(title, s, icon)

# championship graphs
st.subheader("Championship Standings", divider="gray")
championship_options = {"Driver" : "driver_id", "Constructor" : "team_name"}
with st.container(horizontal=True, horizontal_alignment="right"):
    championship_type = st.segmented_control(
        "Championship", list(championship_options), default="Driver",
        label_visibility="collapsed",
    ) or "Driver"

points_df = standings.championships_progression(season_df, championship_options[championship_type])
positions_df = standings.championship_positions(points_df)

points_fig = charts.get_line_graph(points_df, championship_options[championship_type], "points")
st.plotly_chart(points_fig, width="stretch", key="points_graph")
positions_fig = charts.get_line_graph(positions_df, championship_options[championship_type], "position")
st.plotly_chart(positions_fig, width="stretch", key="positions_graph")