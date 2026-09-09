from dataclasses import dataclass
from datetime import timedelta

@dataclass
class Stat:
    value: float | int | timedelta
    unit: str | None = None
    driver_name: str | None = None
    driver_abbrv: str | None = None
    team_name: str | None = None

    # presentation extras
    team_color: str | None = None          # "#rrggbb" - for charts / future badges
    trend: list[float] | None = None       # sparkline series (st.metric chart_data)

    # if applicable
    round_number: int | None = None
    event_name: str | None = None
    context: str | None = None