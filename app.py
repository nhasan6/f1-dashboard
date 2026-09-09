import streamlit as st
from fastf1stats import load
from fastf1stats import metrics, standings, charts
from datetime import timedelta
import components
from fastf1stats.config import FIRST_SEASON
import pandas as pd

@st.cache_data()
def load_year(year: int):
    return load.load_season(year)

@st.cache_data()
def load_pitstops_in_year(year: int):
    return load.load_pitstops(year)

@st.cache_data()
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

st.set_page_config(page_title="Formula 1 Live Dashboard", layout="wide") # TODO add a favicon
st.title("Formula 1 Dashboard")
st.write("'The stopwatch never lies' - Toto Wolff")
year = st.selectbox("Year", [year for year in range(pd.Timestamp.now().year, FIRST_SEASON - 1, -1)]) # first option is selected by default (needs to be most recent year)
season_df = load_year(year)
pitstop_df = load_pitstops_in_year(year)
headline_stats = headline_stats(season_df)
st.subheader(f"{year} Season Overview")

# each spec: (title, driver stat, team stat)
split_specs = [
    ("Most Wins", headline_stats["driver_wins"], headline_stats["team_wins"]),
    ("Most Podiums", headline_stats["driver_podiums"], headline_stats["team_podiums"]),
    ("Most Poles", headline_stats["driver_poles"], headline_stats["team_poles"])
]

# each spec: (title, stat, icon)
single_specs = [
    ("Best Average Finish", metrics.get_best_avg_finish(season_df), ":material/target:"),
    ("Biggest Comeback", metrics.get_biggest_comeback(season_df), ":material/rocket_launch:"),
    ("Fastest Pit Stop", metrics.get_fastest_pit_stop(pitstop_df), ":material/timer:")
] 

for col, (title, d, t) in zip(st.columns(3), split_specs):
    with col:
        components.split_stat_card(title, d, t)

for col, (title, s, icon) in zip(st.columns(3), single_specs):
    with col: 
        components.single_stat_card(title, s, icon)

st.subheader("Championship Standings")
options_dict = {"Driver" : "driver_id", "Constructor" : "team_name"}
championship_type = st.selectbox("Type", options_dict.keys())

prog1 = standings.championships_progression(season_df, options_dict[championship_type])
# fig = charts.get_points_evolution_graph(prog, options_dict[championship_type])

prog = standings.championship_positions(prog1)
fig = charts.get_rankings_evolution_graph(prog, options_dict[championship_type])
st.plotly_chart(fig, width="stretch", theme="streamlit")