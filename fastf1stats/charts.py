import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# group_col is either "driver_id" or "team_name"
# graph_type is either "points" or "position"
_GRAPH_CONFIGS = {
    "points": {
        "y_value": "total_points",
        "y_label": "Points",
        "chart_noun": "points evolution",
        "order_ascending": False,   # standings order = most points first
        "reverse_y_axis": False,
        "hover_template": "%{fullData.name}: %{y:.0f}<extra></extra>",
    },
    "position": {
        "y_value": "position",
        "y_label": "Position",
        "chart_noun": "ranking evolution",
        "order_ascending": True,    # standings order = P1 first
        "reverse_y_axis": True,     # so P1 sits at the top
        "hover_template": "%{fullData.name}: P%{y:.0f}<extra></extra>",
    },
}


def _to_hex(colour) -> str:
    # fastf1 stores team colours as bare hex ('3671c6') --> Plotly needs '#3671c6'
    if not isinstance(colour, str) or not colour.strip():
        return "#888888"  # default
    return "#" + colour.lstrip("#")  # incase they update fastf1 and start adding #s


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


def get_line_graph(df: pd.DataFrame, group_col: str, graph_type: str) -> go.Figure:
    if df is None or df.empty:
        return _empty_figure("No data for this season yet.")

    try:
        cfg = _GRAPH_CONFIGS[graph_type]
    except KeyError:
        raise ValueError(f"Unknown graph type: {graph_type!r}")

    y_value = cfg["y_value"]
    entity_noun = "Driver" if group_col == "driver_id" else "Constructor"

    df = df.sort_values(["entity_label", "round_number"])

    # legend / draw order: each entity ranked by its standing at its OWN last
    # round, so anyone who dropped out before the finale is still placed.
    last_rows = (
        df.sort_values("round_number")
        .groupby("entity_label", sort=False)
        .tail(1)
    )
    entity_order = (
        last_rows.sort_values(y_value, ascending=cfg["order_ascending"])
        ["entity_label"].to_list()
    )

    # one stable colour per entity (fastf1's team_color drifts round to round)
    color_map = {}
    for entity_label, group in df.groupby("entity_label"):
        modes = group["team_color"].mode()  # value that appears most often
        color_map[entity_label] = _to_hex(modes.iat[0] if not modes.empty else None)

    fig = px.line(
        df,
        x="round_number",
        y=y_value,
        color="entity_label",
        color_discrete_map=color_map,
        category_orders={"entity_label": entity_order},
        line_shape="spline",
        markers=True,
        labels={"round_number": "Round", "entity_label": entity_noun, y_value: cfg["y_label"]},
        title=f"{entity_noun} {cfg['chart_noun']}",
    )

    fig.update_traces(
        line=dict(width=2),
        marker=dict(size=8),
        hovertemplate=cfg["hover_template"],
    )

    # faint horizontal gridlines only; no heavy axis lines 
    fig.update_xaxes(dtick=1, showgrid=False, showline=False, zeroline=False,
                     ticks="outside", ticklen=4)
    fig.update_yaxes(showgrid=True, showline=False, zeroline=False)

    if cfg["reverse_y_axis"]:
        # reversed range puts P1 on top; the half-unit pad keeps the top and
        # bottom markers off the plot edge.
        lo, hi = df[y_value].min(), df[y_value].max()
        fig.update_yaxes(dtick=1, range=[hi + 0.5, lo - 0.5])

    fig.update_layout(
        hovermode="x unified",
        legend_title_text=entity_noun,
        margin=dict(l=20, r=20, t=50, b=30),
    )
    return fig
