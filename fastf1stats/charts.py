import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _to_hex(colour) -> str:
    """fastf1 stores team colours as bare hex ('3671c6'); Plotly needs '#3671c6'."""
    if not isinstance(colour, str) or not colour.strip():
        return "#888888"
    return "#" + colour.lstrip("#")


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, showarrow=False,
        xref="paper", yref="paper", x=0.5, y=0.5, font=dict(size=14),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


# group_col is either "driver_id" or "team_name"
def get_points_evolution_graph(progression_df: pd.DataFrame, group_col: str) -> go.Figure:
    entity_noun = "Driver" if group_col == "driver_id" else "Constructor"

    if progression_df is None or progression_df.empty:
        return _empty_figure("No data for this season yet.")

    progression_df = progression_df.sort_values(["entity_label", "round_number"])

    # legend / draw order = standings order at the latest completed round
    final_round = progression_df["round_number"].max()
    entity_order = (
        progression_df[progression_df["round_number"] == final_round]
        .sort_values("total_points", ascending=False)["entity_label"]
        .to_list()
    )

    # one stable colour per entity (fastf1's team_color drifts round to round)
    color_map = {}
    for label, group in progression_df.groupby("entity_label"):
        modes = group["team_color"].mode()
        color_map[label] = _to_hex(modes.iat[0]) if not modes.empty else "#888888"

    fig = px.line(
        progression_df,
        x="round_number",
        y="total_points",
        color="entity_label",
        color_discrete_map=color_map,
        category_orders={"entity_label": entity_order},
        markers=True,
        labels={
            "round_number": "Round",
            "total_points": "Points",
            "entity_label": entity_noun,
        },
        title=f"{entity_noun} Points",
    )

    fig.update_traces(line=dict(width=2), marker=dict(size=8))
    fig.update_xaxes(dtick=1)
    fig.update_layout(
        hovermode="x unified",
        legend_title_text=entity_noun,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig

def get_rankings_evolution_graph(positions_df: pd.DataFrame, group_col: str) ->go.Figure:
    entity_noun = "Driver" if group_col == "driver_id" else "Constructor"
    
    if positions_df is None or positions_df.empty:
        return _empty_figure("No data for this season yet.")


    positions_df = positions_df.sort_values(["entity_label", "round_number"])

    # legend / draw order = standings order at the latest completed round
    final_round = positions_df["round_number"].max()
    entity_order = (
        positions_df[positions_df["round_number"] == final_round]
        .sort_values("position")["entity_label"]
        .to_list()
    )

    # one stable colour per entity (fastf1's team_color drifts round to round)
    color_map = {}
    for label, group in positions_df.groupby("entity_label"):
        modes = group["team_color"].mode()
        color_map[label] = _to_hex(modes.iat[0]) if not modes.empty else "#888888"

    fig = px.line(
        positions_df,
        x="round_number",
        y="position",
        color="entity_label",
        color_discrete_map=color_map,
        category_orders={"entity_label": entity_order},
        markers=True,
        labels={
            "round_number": "Round",
            "total_points": "Position",
            "entity_label": entity_noun,
        },
        title=f"{entity_noun} Rankings",
    )

    fig.update_traces(line=dict(width=2), marker=dict(size=8))
    fig.update_yaxes(autorange="reversed") # so 1st place is at the top 
    fig.update_xaxes(dtick=1)
    fig.update_layout(
        hovermode="x unified",
        legend_title_text=entity_noun,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig
    