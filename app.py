import streamlit as st
from fastf1stats import load
from fastf1stats import metrics, standings, charts
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
def load_championships_progression(season_df: pd.DataFrame, group_col: str):
    return standings.championships_progression(season_df, group_col)

@st.cache_data()
def load_championships_positions(progression_df: pd.DataFrame):
    return standings.championship_positions(progression_df)

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

# dataframes
season_df = load_year(year)
pitstop_df = load_pitstops_in_year(year)

# computed data
headline_stats = headline_stats(season_df)

# consts 

# each spec: (title, driver stat, team stat) - row 1
split_specs = [
    ("Most Wins", headline_stats["driver_wins"], headline_stats["team_wins"]),
    ("Most Podiums", headline_stats["driver_podiums"], headline_stats["team_podiums"]),
    ("Most Poles", headline_stats["driver_poles"], headline_stats["team_poles"])
]

# each spec: (title, stat, icon) - row 2
single_specs = [
    ("Best Average Finish", metrics.get_best_avg_finish(season_df), ":material/target:"),
    ("Biggest Comeback", metrics.get_biggest_comeback(season_df), ":material/trending_up:"),
    ("Fastest Pit Stop", metrics.get_fastest_pit_stop(pitstop_df), ":material/timer:")
] 

# stats grid  
st.subheader(f"{year} Season Overview")

for col, (title, d, t) in zip(st.columns(3), split_specs):
    with col:
        components.split_stat_card(title, d, t)

for col, (title, s, icon) in zip(st.columns(3), single_specs):
    with col: 
        components.single_stat_card(title, s, icon)

# championship graphs
st.subheader("Championship Standings")
championship_options = {"Driver" : "driver_id", "Constructor" : "team_name"}
championship_type = st.selectbox("Type", championship_options.keys())

points_df = load_championships_progression(season_df, championship_options[championship_type])
positions_df = load_championships_positions(points_df)

points_fig = charts.get_points_evolution_graph(points_df, championship_options[championship_type])
st.plotly_chart(points_fig, width="stretch", theme="streamlit", key="points_graph")
positions_fig = charts.get_rankings_evolution_graph(positions_df, championship_options[championship_type])
st.plotly_chart(positions_fig, width="stretch", theme="streamlit", key="positions_graph")