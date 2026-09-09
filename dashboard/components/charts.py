import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

FUEL_COLOR_MAP = {
    "Renewables & Biofuels Total": "#10b981", # Emerald
    "Hydro Power": "#3b82f6",                # Blue
    "Wind Power": "#06b6d4",                 # Cyan
    "Solar Photovoltaic": "#f59e0b",         # Amber
    "Solar Thermal": "#fbbf24",              # Yellow
    "Geothermal Energy": "#ec4899",          # Pink
    "Primary Solid Biofuels & Waste": "#84cc16", # Lime
    "Nuclear Power": "#8b5cf6",              # Purple
    "Solid Fossil Fuels (Coal)": "#475569",  # Slate
    "Natural Gas": "#ef4444",                # Red
    "Oil & Petroleum Products": "#94a3b8",   # Grey
    "Total Electricity Generation": "#6366f1" # Indigo
}

DARK_LAYOUT = {
    "paper_bgcolor": "rgba(15, 23, 42, 0.0)",
    "plot_bgcolor": "rgba(15, 23, 42, 0.0)",
    "font": {"color": "#e2e8f0", "family": "Inter, sans-serif"},
    "xaxis": {"gridcolor": "#334155", "showgrid": True},
    "yaxis": {"gridcolor": "#334155", "showgrid": True},
    "margin": {"l": 40, "r": 20, "t": 40, "b": 40}
}

def create_stacked_area_chart(df: pd.DataFrame, x_col: str, y_col: str, group_col: str, title: str) -> go.Figure:
    """Create stacked area chart for energy generation mix over time."""
    fig = px.area(
        df, x=x_col, y=y_col, color=group_col,
        title=title,
        color_discrete_map=FUEL_COLOR_MAP
    )
    fig.update_layout(**DARK_LAYOUT)
    fig.update_yaxes(title_text="Generation (GWh)")
    fig.update_xaxes(title_text="Year")
    return fig

def create_country_ranking_chart(df: pd.DataFrame, country_col: str, val_col: str, title: str, unit_label: str = "%") -> go.Figure:
    """Create horizontal bar chart ranking European countries."""
    sorted_df = df.sort_values(by=val_col, ascending=True)
    fig = px.bar(
        sorted_df, y=country_col, x=val_col, orientation="h",
        title=title,
        color=val_col,
        color_continuous_scale="Viridis",
        text_auto=".1f"
    )
    fig.update_layout(**DARK_LAYOUT)
    fig.update_xaxes(title_text=unit_label)
    fig.update_yaxes(title_text="")
    return fig

def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str, group_col: str, title: str, y_unit: str) -> go.Figure:
    """Create multi-line chart for prices, YoY trends, per capita metrics."""
    fig = px.line(
        df, x=x_col, y=y_col, color=group_col,
        title=title,
        markers=True
    )
    fig.update_layout(**DARK_LAYOUT)
    fig.update_yaxes(title_text=y_unit)
    return fig

def create_forecast_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Create transparent forecasting chart with confidence bounds and clear data_type distinction."""
    fig = go.Figure()

    hist_df = df[df["data_type"] == "Historical Fact (Official Source)"]
    fc_df = df[df["data_type"] == "Forecast / Model Projection (NOT Fact)"]

    # Historical Line
    fig.add_trace(go.Scatter(
        x=hist_df["year"], y=hist_df["value"],
        mode="lines+markers",
        name="Historical Fact (Eurostat)",
        line=dict(color="#10b981", width=3)
    ))

    # Forecast Line
    if not fc_df.empty:
        # Connect last historical point to first forecast point
        connect_x = [hist_df["year"].iloc[-1]] + list(fc_df["year"])
        connect_y = [hist_df["value"].iloc[-1]] + list(fc_df["value"])

        fig.add_trace(go.Scatter(
            x=connect_x, y=connect_y,
            mode="lines+markers",
            name="Forecast / Projection (Model)",
            line=dict(color="#f59e0b", width=3, dash="dash")
        ))

        # Upper & Lower Bounds
        fig.add_trace(go.Scatter(
            x=list(fc_df["year"]) + list(fc_df["year"])[::-1],
            y=list(fc_df["upper_bound"]) + list(fc_df["lower_bound"])[::-1],
            fill="toself",
            fillcolor="rgba(245, 158, 11, 0.2)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            showlegend=True,
            name="95% Confidence Interval"
        ))

    fig.update_layout(title=title, **DARK_LAYOUT)
    fig.update_yaxes(title_text="GWh")
    fig.update_xaxes(title_text="Year")
    return fig
