import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def _to_hex(colour) -> str:
    # fastf1 stores team colours as bare hex ('3671c6') --> Plotly needs '#3671c6'
    if not isinstance(colour, str) or not colour.strip():
        return "#888888" # default
    return "#" + colour.lstrip("#") # incase they update fastf1 and start adding #s

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
# graph_type is either "position" or "points"
def get_line_graph(df: pd.DataFrame, group_col: str, graph_type: str) -> go.Figure:

    if df is None or df.empty:
            return _empty_figure("No data for this season yet.")

    entity_noun = "Driver" if group_col == "driver_id" else "Constructor"

    graph_labels = {
        "round_number": "Round",
        "entity_label": entity_noun,
    }

    position_graph_config = {
        "y_value" : "position",
        "y_label" : "Position",
        "order_ascending" : True,
        "reverse_y_axis" : True 
    }
    
    points_graph_config = {
        "y_value" : "total_points",
        "y_label" : "Points",
        "order_ascending" : False,
        "reverse_y_axis" : False
    }

    if graph_type == "position":
        graph_config = position_graph_config
    elif graph_type == "points":
        graph_config = points_graph_config
    else:
        raise ValueError("Unknown graph type")

    
    graph_labels[graph_config["y_value"]] = graph_config["y_label"]

    df = df.sort_values(["entity_label", "round_number"])

    # legend / draw order 
    # gets each entity(driver/team)'s OWN last round  (so anyone who dropped out before the finale is still placed)
    last_rows = ( 
        df.sort_values("round_number")
        .groupby("entity_label", sort=False)
        .tail(1)
    ) 
    entity_order = (
        last_rows.sort_values(
            graph_config["y_value"], 
            ascending=graph_config["order_ascending"])["entity_label"].to_list() 
    )

    # one stable colour per entity (fastf1's team_color drifts round to round)
    color_map = {}
    for entity_label, group in df.groupby("entity_label"):
        modes = group["team_color"].mode() # .mode() is the value that appears most often 
        color_map[entity_label] = _to_hex(modes.iat[0] if not modes.empty else None)

    fig = px.line(
        df,
        x="round_number",
        y=graph_config["y_value"], 
        color="entity_label", # how to group/separate the data
        color_discrete_map=color_map, # what colors to use 
        category_orders={"entity_label": entity_order}, 
        markers=True,
        labels=graph_labels,
        title=f"{entity_noun} {graph_config['y_label']}",
    )

    fig.update_traces(line=dict(width=2), marker=dict(size=8))

    if graph_config["reverse_y_axis"]:
        # reversed range puts P1 on top; the half-unit pad keeps the top and
        # bottom markers off the plot edge.
        lo, hi = df[graph_config["y_value"]].min(), df[graph_config["y_value"]].max()
        fig.update_yaxes(dtick=1, range=[hi + 0.5, lo - 0.5])

    fig.update_xaxes(dtick=1) # only whole #s 
    fig.update_layout(
        hovermode="x unified",
        legend_title_text=entity_noun,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig