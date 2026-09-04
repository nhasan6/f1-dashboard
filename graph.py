import pandas as pd
import numpy as np
import random
import requests
import fastf1 as ff1
from fastf1 import plotting
from fastf1.ergast import Ergast


CACHE_DIR = "/Users/neeyahasan/repositories/fastf1-cache"
ff1.Cache.enable_cache(CACHE_DIR)

ergast = Ergast()

import seaborn as sns
import matplotlib.pyplot as plt



#1. get the data
rounds = 12
year = 2026


# colours don't change every race 
color_session = ff1.get_session(year, 1, "R")
color_session.load()


all_championship_standings = pd.DataFrame()

driver_team_mapping = {} 

for i in range(1, rounds + 1):
    race = ergast.get_driver_standings(year, i)
    standings = race.content[0]
    # print(standings.columns.to_list())

    current_round = {"round": i}

    for _, standing in standings.iterrows():
        driver = standing["driverCode"]
        position = standing["position"]

        if pd.notna(position):
            current_round[driver] = int(position)
        else:
            current_round[driver] = np.nan #means unavialble 

    # append current round to our final database
    all_championship_standings = pd.concat([all_championship_standings, pd.DataFrame([current_round])], ignore_index=True)

all_championship_standings = all_championship_standings.set_index("round")


#2. clean the data

# convert from wide to long dataset
all_championship_standings_melted = pd.melt(all_championship_standings.reset_index(), ["round"])


#3. plot the data

# calibrate the colours
driver_team_mapping = dict(
    zip(
        standings["driverCode"],
        standings["constructorNames"].str[0]
    )
)

sns.set(rc={'figure.figsize':(11.7,8.27)})
fig, ax = plt.subplots()

ax.set_title(f"{year} Formula 1 Drivers Championship Standings")

for driver in pd.unique(all_championship_standings_melted["variable"]):
    sns.lineplot(
        x="round",
        y="value",
        data=all_championship_standings_melted.loc[all_championship_standings_melted["variable"]==driver],
        color=plotting.get_team_color(driver_team_mapping[driver], session=color_session)
    )

ax.invert_yaxis() 

ax.set_xticks(range(1, rounds))
ax.set_yticks(range(1,23))

ax.set_xlabel("Round")
ax.set_ylabel("Championship position")

ax.grid(False)

for line, name in zip(ax.lines, all_championship_standings.columns.to_list()):
    y = line.get_ydata()[-1]
    x = line.get_xdata()[-1]

    text = ax.annotate(
        name,
        xy=(x + 0.1, y),
        xytext=(0, 0),
        color=line.get_color(),
        xycoords=(
            ax.get_xaxis_transform(),
            ax.get_yaxis_transform()
        ),
        textcoords="offset points"
    )

# Save the plot
plt.savefig('img/championship_standings.png')