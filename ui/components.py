import streamlit as st
from datetime import timedelta

# st.metric's delta/chart colour only accepts a NAMED palette colour, not hex,
# so real team hex (Stat.team_color) can't drive it. Map each team to the
# nearest named colour instead - several teams collapse onto "blue", but the
# card is still team-tinted rather than uniformly grey.
_TEAM_ACCENT = {
    "ferrari": "red",
    "mclaren": "orange",          # guard against the common misspelling
    "mclaren": "orange",
    "mercedes": "primary",        # theme accent is teal - close enough
    "red bull": "blue",
    "racing bulls": "violet",
    "alphatauri": "violet",
    "rb": "violet",
    "williams": "blue",
    "alpine": "blue",
    "aston martin":  "green",
    "kick sauber": "green",
    "sauber": "green",
    "haas": "gray",
    "audi": "gray",
    "cadillac": "gray"
}


def _accent(team_name) -> str:
    """Named palette colour for a team, defaulting to the theme accent."""
    if not team_name:
        return "primary"
    key = str(team_name).lower()
    for fragment, colour in _TEAM_ACCENT.items():
        if fragment in key:
            return colour
    return "primary"


def _surname(full_name):
    """Last token of a name, or None. 'Lewis Hamilton' -> 'Hamilton'."""
    if not full_name:
        return None
    return full_name.split()[-1]


def _tidy(name):
    """Ergast ids arrive lower-case with underscores ('max_verstappen')."""
    if not name:
        return None
    name = str(name).replace("_", " ")
    return name.title() if name.islower() else name


def format_value(stat) -> str:
    """Headline string for a Stat, with the unit folded in beside the number
    ('12 wins', '3.7 average', '2.360s')."""
    if stat is None or stat.value is None:
        return "—"
    value, unit = stat.value, stat.unit
    if isinstance(value, timedelta):
        return f"{value.total_seconds():.3f}:small[s]"
    if isinstance(value, float):
        return f"{value:.1f} :small[{unit}]" if unit else f"{value:.1f}"
    if unit in {"wins", "podiums", "poles", "places", "points"}:
        return f"{value} :small[{unit}]"
    return str(value)


def _context(stat) -> str | None:
    """'Hamilton · British Grand Prix · R9' from whatever fields are set."""
    parts = []
    name = _tidy(_surname(stat.driver_name))
    if name:
        parts.append(name)
    if stat.event_name:
        parts.append(str(stat.event_name))
    if stat.round_number is not None:
        parts.append(f"R{stat.round_number}")
    return " · ".join(parts) or None


def _stat_metric(label, stat, sub_line):
    """A bare st.metric (no border of its own) for one half of a split card.
    `sub_line` is the coloured text under the number - a driver surname or team."""
    if stat is None:
        st.metric(label, "—")
        return
    st.metric(
        label=label,
        value=format_value(stat),
        delta=sub_line or None,
        delta_arrow="off",
        delta_color=_accent(stat.team_name),
    )


def split_stat_card(title, driver_stat, team_stat, icon=None):
    """A card with a Driver half and a Constructor half (e.g. 'Most wins')."""
    with st.container(border=True):
        heading = f"{icon} **{title}**" if icon else f"**{title}**"
        st.markdown(heading)
        row = st.container(horizontal=True)
        with row:
            driver_name = _tidy(_surname(driver_stat.driver_name)) if driver_stat else None
            team_name = team_stat.team_name if team_stat else None
            _stat_metric("Driver", driver_stat, driver_name)
            _stat_metric("Constructor", team_stat, team_name)


def single_stat_card(title, stat, icon):
    """A one-number card with an icon and a context line (e.g. 'Fastest pit stop')."""
    with st.container(border=True):
        heading = f"{icon} **{title}**" if icon else f"**{title}**"
        st.markdown(heading)

        if stat is None:
            st.metric(title, "—", label_visibility="collapsed")
            return

        st.metric(
            label=title,
            label_visibility="collapsed",  # shown as the bold heading above
            value=format_value(stat),
            delta=_context(stat),
            delta_arrow="off",
            delta_color=_accent(stat.team_name),
        )
