# charts.py
import math
from typing import Dict, List, Tuple

import numpy as np
import plotly.graph_objects as go
import plotly.express as px


def people_outcomes_chart(
    enrollment: int,
    immune_rate: float,
    infected: float,
    hosp_rate: float,
    death_rate: float,
    per_unit: float | None = None,
    style: str = "heads",          # circles (no emojis)
    show_background: bool = True,  # faint school backdrop
) -> Tuple[go.Figure, float]:
    """
    Visualizes students as small units with outcomes:
      - Immune (MMR-protected)
      - Susceptible (not infected)
      - Infected (no hospital stay)
      - Hospitalized
      - Death

    Returns (fig, per_unit).
    Style options: "heads" (circles) or "square" (waffle).
    """
    enrollment = max(0, int(round(enrollment or 0)))
    immune_count = float(enrollment * (immune_rate or 0))
    infected = float(max(0.0, infected or 0.0))
    hosp = float(max(0.0, min(hosp_rate or 0.0, 1.0)) * infected)
    death = float(max(0.0, min(death_rate or 0.0, 1.0)) * infected)
    infected_no_stay = max(0.0, infected - hosp - death)
    susceptible = max(0.0, enrollment - immune_count)
    not_infected = max(0.0, susceptible - infected)

    # Decide unit size (how many students each marker represents)
    def _bucket_size(e: int) -> int:
        if e <= 50:
            return 1
        if e <= 200:
            return 2
        if e <= 500:
            return 5
        if e <= 2000:
            return 10
        return 25

    if per_unit is None:
        per_unit = float(_bucket_size(enrollment))

    def _counts(e: int, immune_rate: float, infected: float, hosp_rate: float, death_rate: float):
        immune = immune_count
        susceptible = max(0.0, e - immune)
        infected_val = infected
        hosp_val = hosp
        death_val = death
        infected_no_stay_val = max(0.0, infected_val - hosp_val - death_val)
        not_infected_val = max(0.0, susceptible - infected_val)
        return dict(
            immune=immune,
            susceptible_not_infected=not_infected_val,
            infected_no_stay=infected_no_stay_val,
            hospitalized=hosp_val,
            death=death_val,
        )

    raw_counts = _counts(enrollment, immune_rate, infected, hosp_rate, death_rate)

    # Convert to units and remainder rounding
    def _grid(counts: Dict[str, float], unit: float):
        labels_order = [
            "Immune (MMR-protected)",
            "Susceptible (not infected)",
            "Infected (no hospital stay)",
            "Hospitalized",
            "Death",
        ]
        keys = ["immune", "susceptible_not_infected", "infected_no_stay", "hospitalized", "death"]
        colors = px.colors.qualitative.Plotly
        color_map = {
            "immune": colors[2],                  # green-ish
            "susceptible_not_infected": colors[0],# blue-ish
            "infected_no_stay": colors[1],        # orange-ish
            "hospitalized": colors[3],            # red-ish
            "death": colors[4],                   # purple-ish
        }

        # number of markers per category
        units = {k: int(round((counts[k] or 0) / unit)) for k in keys}
        # Build grid
        xs: List[float] = []
        ys: List[float] = []
        cols: List[str] = []
        texts: List[str] = []
        labels: List[str] = []

        # Waffle-like layout
        per_row = 20
        row = 0
        col = 0

        def _add(n: int, label_key: str, label_name: str):
            nonlocal row, col
            for _ in range(n):
                xs.append(col)
                ys.append(-row)  # top to bottom
                cols.append(color_map[label_key])
                labels.append(label_name)
                col += 1
                if col >= per_row:
                    col = 0
                    row += 1

        for key, label in zip(keys, labels_order):
            _add(units.get(key, 0), key, label)

        # text for hover
        counts_labels = {
            "Immune (MMR-protected)": raw_counts["immune"],
            "Susceptible (not infected)": raw_counts["susceptible_not_infected"],
            "Infected (no hospital stay)": raw_counts["infected_no_stay"],
            "Hospitalized": raw_counts["hospitalized"],
            "Death": raw_counts["death"],
        }
        texts = [f"{lab}<br>~{int(round(counts_labels[lab])):,} students" for lab in labels]
        return xs, ys, cols, labels, texts

    xs, ys, cols, labels, texts = _grid(raw_counts, per_unit)

    # Build traces
    mode = "markers"
    marker_kwargs = dict(
        size=12,
        line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
        symbol="circle" if style == "heads" else "square",
    )

    def traces_for(xs, ys, cols, labels, text_list=None):
        # group by label to control legend
        grouped: Dict[str, Dict[str, list]] = {}
        for x, y, c, lab in zip(xs, ys, cols, labels):
            grouped.setdefault(lab, {"x": [], "y": [], "color": c})
            grouped[lab]["x"].append(x)
            grouped[lab]["y"].append(y)

        traces = []
        text_iter = iter(text_list) if text_list else None
        for lab, d in grouped.items():
            n = len(d["x"])
            t = [next(text_iter) for _ in range(n)] if text_iter else [lab] * n
            traces.append(
                go.Scatter(
                    x=d["x"],
                    y=d["y"],
                    mode=mode,
                    marker=dict(color=d["color"], **marker_kwargs),
                    name=lab,
                    hovertemplate="%{text}<extra></extra>",
                    text=t,
                )
            )
        return traces

    traces = traces_for(xs, ys, cols, labels, texts)

    fig = go.Figure(data=traces)
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=10, r=10),
    )

    # optional faint school backdrop (simple rectangle bands)
    if show_background:
        fig.add_shape(
            type="rect",
            x0=-0.5,
            x1=20.5,
            y0=-0.5,
            y1=min(0.0, -math.ceil(len(xs) / 20) - 0.5),
            line=dict(width=0),
            fillcolor="rgba(0,0,0,0.03)",
            layer="below",
        )

    return fig, per_unit


def epi_curve_chart(daily_counts, y_max: int = 100) -> go.Figure:
    """
    Animated incidence chart (daily new cases). If you don't need animation,
    it's still a clean bar+line combo with capped y-axis for comparisons.
    """
    y = np.array(daily_counts, dtype=float)
    y = np.clip(y, 0, None)
    days = np.arange(1, len(y) + 1)

    y_axis_max = max(y_max, int(max(10, np.ceil(y.max() / 10.0) * 10)))

    # base (zeros)
    bar0 = go.Bar(
        x=days, y=[0] * len(days), name="", marker=dict(opacity=0.35),
        hovertemplate="Day %{x}<br>New cases %{y:.0f}<extra></extra>"
    )
    line0 = go.Scatter(
        x=days, y=[0] * len(days), mode="lines",
        line=dict(width=3),
        hovertemplate="Day %{x}<br>New cases %{y:.0f}<extra></extra>",
        name="Daily cases",
    )

    # final
    barF = go.Bar(
        x=days, y=y, name="", marker=dict(opacity=0.35),
        hovertemplate="Day %{x}<br>New cases %{y:.0f}<extra></extra>"
    )
    lineF = go.Scatter(
        x=days, y=y, mode="lines",
        line=dict(width=3),
        hovertemplate="Day %{x}<br>New cases %{y:.0f}<extra></extra>",
        name="Daily cases",
    )

    fig = go.Figure(
        data=[bar0, line0],
        frames=[go.Frame(data=[barF, lineF], name="final")]
    )
    fig.update_layout(
        xaxis=dict(title="Days since introduction", showgrid=False),
        yaxis=dict(title="Daily new cases (students)", showgrid=False, range=[0, y_axis_max]),
        barmode="overlay",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
        updatemenus=[dict(
            type="buttons",
            x=0.0, y=1.15, xanchor="left", yanchor="top",
            showactive=False,
            buttons=[
                dict(
                    label="▶ Start Outbreak",
                    method="animate",
                    args=[["final"], {"frame": {"duration": 800, "redraw": True},
                                      "fromcurrent": True, "transition": {"duration": 250}}]
                ),
                dict(
                    label="↺ Reset",
                    method="animate",
                    args=[[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]
                ),
            ],
        )],
    )
    return fig
