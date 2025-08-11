# charts.py
# (Python 3.9+ compatible; keeps legacy helpers used by other tabs; no emojis)
import math
from typing import Dict, List, Tuple, Optional

import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ----------------------------
# Legacy helpers (kept so Tab 2–4 don’t break)
# ----------------------------
def stacked_bar_chart(data: Dict[str, float], title: str = "", colors: Optional[List[str]] = None) -> go.Figure:
    """
    Single horizontal stacked bar showing proportions across categories.
    `data` can be raw counts or proportions; we'll normalize to 100%.
    """
    keys = list(data.keys())
    vals = np.array([max(0.0, float(data[k] or 0)) for k in keys], dtype=float)
    tot = vals.sum()
    props = (vals / tot) if tot > 0 else np.zeros_like(vals)

    if colors is None:
        colors = px.colors.qualitative.Plotly

    # Build as a "one-row" stacked bar using separate traces
    fig = go.Figure()
    cum = 0.0
    for i, (k, p) in enumerate(zip(keys, props)):
        fig.add_trace(
            go.Bar(
                x=[p],
                y=[""],
                name=k,
                orientation="h",
                marker=dict(color=colors[i % len(colors)]),
                hovertemplate=f"{k}: {p*100:.1f}%<extra></extra>",
            )
        )
        cum += p

    fig.update_layout(
        barmode="stack",
        title=title,
        xaxis=dict(range=[0, 1], showgrid=False, tickformat=".0%", title=""),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


def proportional_pictogram_bar(
    data: Dict[str, float],
    title: str = "",
    total_cases: Optional[float] = None,
    icon_size: int = 12,
    icons_per_row: int = 20,
    colors: Optional[List[str]] = None,
    show_counts_for: Optional[List[str]] = None,
) -> go.Figure:
    """
    Waffle-style pictogram (no emojis): 100 markers laid out in rows.
    `data` can be counts or proportions; we normalize to 100 units.
    """
    if colors is None:
        colors = px.colors.qualitative.Plotly
    if show_counts_for is None:
        show_counts_for = []

    keys = list(data.keys())
    vals = np.array([max(0.0, float(data[k] or 0)) for k in keys], dtype=float)
    tot = vals.sum() if total_cases is None else float(total_cases)
    props = (vals / (vals.sum() or 1.0)) if total_cases is None else (vals / (tot or 1.0))

    # Map to 100 units
    units = 100
    counts = np.floor(props * units).astype(int)
    short = units - counts.sum()
    # distribute remainder
    for i in range(short):
        counts[i % len(counts)] += 1

    xs, ys, cols, txts = [], [], [], []
    row = 0
    col = 0
    color_map = {k: colors[i % len(colors)] for i, k in enumerate(keys)}

    def _add(n, k):
        nonlocal row, col
        for _ in range(n):
            xs.append(col)
            ys.append(-row)
            cols.append(color_map[k])
            txt = f"{k}"
            if k in show_counts_for:
                # Show approximate count if total_cases known, else show percentage
                if total_cases:
                    approx = (props[keys.index(k)] * tot)
                    txt += f"<br>~{int(round(approx)):,}"
                else:
                    txt += f"<br>{props[keys.index(k)]*100:.1f}%"
            txts.append(txt)
            col += 1
            if col >= icons_per_row:
                col = 0
                row += 1

    for k, c in zip(keys, counts):
        _add(int(c), k)

    fig = go.Figure(
        data=[
            go.Scatter(
                x=xs, y=ys, mode="markers",
                marker=dict(symbol="square", size=icon_size, line=dict(width=0.3, color="rgba(0,0,0,0.3)"), color=cols),
                text=txts,
                hovertemplate="%{text}<extra></extra>",
                showlegend=False,
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


def subset_proportional_pictogram_bar(
    data: Dict[str, float],
    title: str = "",
    icon_size: int = 10,
    icons_per_row: int = 10,
    colors: Optional[List[str]] = None,
) -> go.Figure:
    """
    Smaller waffle where `data` is a dict of categories → proportion or
    a dict of categories → {"yes": proportion}. We render a small 10x10 grid.
    """
    if colors is None:
        colors = px.colors.qualitative.Plotly

    # Normalize input
    norm: Dict[str, float] = {}
    for i, (k, v) in enumerate(data.items()):
        if isinstance(v, dict) and "yes" in v:
            norm[k] = max(0.0, float(v["yes"] or 0.0))
        else:
            norm[k] = max(0.0, float(v or 0.0))

    tot = sum(norm.values()) or 1.0
    props = {k: v / tot for k, v in norm.items()}

    units = 100
    counts = {k: int(math.floor(p * units)) for k, p in props.items()}
    remainder = units - sum(counts.values())
    ks = list(props.keys())
    for i in range(remainder):
        counts[ks[i % len(ks)]] += 1

    xs, ys, cols, txts = [], [], [], []
    row = 0
    col = 0
    color_map = {k: colors[i % len(colors)] for i, k in enumerate(ks)}

    for k in ks:
        for _ in range(counts[k]):
            xs.append(col)
            ys.append(-row)
            cols.append(color_map[k])
            txts.append(f"{k}<br>{props[k]*100:.1f}%")
            col += 1
            if col >= icons_per_row:
                col = 0
                row += 1

    fig = go.Figure(
        data=[
            go.Scatter(
                x=xs, y=ys, mode="markers",
                marker=dict(symbol="square", size=icon_size, line=dict(width=0.3, color="rgba(0,0,0,0.3)"), color=cols),
                text=txts,
                hovertemplate="%{text}<extra></extra>",
                showlegend=False,
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


# ----------------------------
# Tab 5 helpers (kept/improved)
# ----------------------------
def people_outcomes_chart(
    enrollment,            # int
    immune_rate,           # float (0..1)
    infected,              # float
    hosp_rate,             # float (0..1)
    death_rate,            # float (0..1)
    per_unit: Optional[float] = None,
    style: str = "heads",                # circles (no emojis)
    show_background: bool = True,        # faint school backdrop
) -> Tuple[go.Figure, float]:
    """
    Visualizes students as small units with outcomes.
    Returns (fig, per_unit). Style options: "heads" (circles) or "square" (waffle).
    """
    enrollment = max(0, int(round(enrollment or 0)))
    immune_count = float(enrollment * (immune_rate or 0))
    infected = float(max(0.0, infected or 0.0))
    hosp = float(max(0.0, min(hosp_rate or 0.0, 1.0)) * infected)
    death = float(max(0.0, min(death_rate or 0.0, 1.0)) * infected)
    infected_no_stay = max(0.0, infected - hosp - death)
    susceptible = max(0.0, enrollment - immune_count)
    not_infected = max(0.0, susceptible - infected)

    def _bucket_size(e: int) -> int:
        if e <= 50: return 1
        if e <= 200: return 2
        if e <= 500: return 5
        if e <= 2000: return 10
        return 25

    if per_unit is None:
        per_unit = float(_bucket_size(enrollment))

    raw_counts = dict(
        immune=immune_count,
        susceptible_not_infected=not_infected,
        infected_no_stay=infected_no_stay,
        hospitalized=hosp,
        death=death,
    )

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
            "immune": colors[2],
            "susceptible_not_infected": colors[0],
            "infected_no_stay": colors[1],
            "hospitalized": colors[3],
            "death": colors[4],
        }
        units = {k: int(round((counts[k] or 0) / unit)) for k in keys}

        xs: List[float] = []
        ys: List[float] = []
        cols: List[str] = []
        labels: List[str] = []

        per_row = 20
        row = 0
        col = 0

        def _add(n: int, label_key: str, label_name: str):
            nonlocal row, col
            for _ in range(n):
                xs.append(col)
                ys.append(-row)
                cols.append(color_map[label_key])
                labels.append(label_name)
                col += 1
                if col >= per_row:
                    col = 0
                    row += 1

        for key, label in zip(keys, labels_order):
            _add(units.get(key, 0), key, label)

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

    marker_kwargs = dict(
        size=12,
        line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
        symbol="circle" if style == "heads" else "square",
    )

    # Group by label to control legend
    grouped: Dict[str, Dict[str, list]] = {}
    for x, y, c, lab in zip(xs, ys, cols, labels):
        grouped.setdefault(lab, {"x": [], "y": [], "color": c})
        grouped[lab]["x"].append(x)
        grouped[lab]["y"].append(y)

    traces = []
    for lab, d in grouped.items():
        n = len(d["x"])
        t = [lab] * n
        traces.append(
            go.Scatter(
                x=d["x"], y=d["y"], mode="markers",
                marker=dict(color=d["color"], **marker_kwargs),
                name=lab,
                hovertemplate="%{text}<extra></extra>",
                text=[f"{lab}"] * n,
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=10, r=10),
    )

    if show_background:
        fig.add_shape(
            type="rect",
            x0=-0.5, x1=20.5,
            y0=-0.5, y1=min(0.0, -math.ceil(len(xs) / 20) - 0.5),
            line=dict(width=0),
            fillcolor="rgba(0,0,0,0.03)",
            layer="below",
        )

    return fig, per_unit


def epi_curve_chart(daily_counts, y_max: int = 100) -> go.Figure:
    """
    Incidence chart (daily new cases). Includes simple play/reset animation.
    """
    y = np.array(daily_counts, dtype=float)
    y = np.clip(y, 0, None)
    days = np.arange(1, len(y) + 1)

    y_axis_max = max(y_max, int(max(10, np.ceil(y.max() / 10.0) * 10)))

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

