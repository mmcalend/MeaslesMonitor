import plotly.graph_objects as go
import math
import plotly.express as px

def proportional_pictogram_bar(data, title, total_cases=None, icon_size=16, icons_per_row=10, colors=None, show_counts_for=None):
    total_icons = 100
    x_coords, y_coords, colors_out, hover_texts = [], [], [], []

    if colors is None:
        colors = px.colors.qualitative.Plotly
    if show_counts_for is None:
        show_counts_for = []

    numeric_data = {k: (v if isinstance(v, (int, float)) else 0) for k, v in data.items()}

    raw_counts = {k: v * total_icons for k, v in numeric_data.items()}
    floored = {k: int(math.floor(v)) for k, v in raw_counts.items()} 
    remainders = {k: raw_counts[k] - floored[k] for k in raw_counts}
    total_floored = sum(floored.values())
    icons_to_allocate = total_icons - total_floored

    for k in sorted(remainders, key=remainders.get, reverse=True)[:icons_to_allocate]:
        floored[k] += 1

    current_index = 0
    sorted_items = list(floored.items())
    for i, (label, count) in enumerate(sorted_items):
        pct = count / total_icons
        show_count = label in show_counts_for and total_cases is not None
        label_text = f"{label}: {int(round(pct * total_cases))} ({pct*100:.1f}%)" if show_count else f"{label}: {pct*100:.1f}%"

        for _ in range(count):
            row = current_index // icons_per_row
            col = current_index % icons_per_row
            x_coords.append(col)
            y_coords.append(-row)
            colors_out.append(colors[i % len(colors)])
            hover_texts.append(label_text)
            current_index += 1

    fig = go.Figure(go.Scatter(
        x=x_coords, y=y_coords, mode="markers",
        marker=dict(size=icon_size, symbol="square", color=colors_out),
        text=hover_texts, hoverinfo="text", showlegend=False))

    for i, (label, _) in enumerate(sorted_items):
        pct = floored[label] / total_icons
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(symbol="square", size=14, color=colors[i % len(colors)]),
            name=f"{label}: {pct*100:.1f}%"
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        showlegend=True,
        height=300,
        width=400,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig

def subset_proportional_pictogram_bar(data, title, icon_size=16, icons_per_row=10, colors=None):
    total_icons_per_row = 100
    x_coords, y_coords, colors_out, hover_texts = [], [], [], []

    if colors is None:
        colors = px.colors.qualitative.Plotly

    current_row = 0
    sorted_items = list(data.items())

    for i, (main_label, subset_data) in enumerate(sorted_items):
        main_color = colors[i % len(colors)]
        total_yes_proportion = subset_data['yes']

        num_yes_icons = int(round(total_yes_proportion * total_icons_per_row))
        for col in range(num_yes_icons):
            x_coords.append(col)
            y_coords.append(-current_row)
            colors_out.append(main_color)
            hover_texts.append(f"{main_label} (Hospitalized): {total_yes_proportion*100:.1f}%")

        # Add "No" icons
        num_no_icons = total_icons_per_row - num_yes_icons
        for col in range(num_yes_icons, total_icons_per_row):
            x_coords.append(col)
            y_coords.append(-current_row)
            colors_out.append("#D3D3D3") 
            hover_texts.append(f"{main_label} (Not Hospitalized): {(1 - total_yes_proportion)*100:.1f}%" if (1 - total_yes_proportion) > 0 else f"{main_label} (Not Hospitalized): 0.0%")

        current_row += 1

    fig = go.Figure(go.Scatter(
        x=x_coords, y=y_coords, mode="markers",
        marker=dict(size=icon_size, symbol="square", color=colors_out),
        text=hover_texts, hoverinfo="text", showlegend=False))

    for i, (main_label, subset_data) in enumerate(sorted_items):
        main_color = colors[i % len(colors)]
        total_yes_proportion = subset_data['yes']

        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(symbol="square", size=14, color=main_color),
            name=f"{main_label} (Hospitalized): {total_yes_proportion*100:.1f}%"
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, tickvals=[-r for r in range(len(sorted_items))], ticktext=[label for label, _ in sorted_items]),
        showlegend=True,
        height=100 + len(sorted_items) * 40, 
        width=600,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig


def stacked_bar_chart(data, title, colors):
    labels, values = list(data.keys()), list(data.values())
    fig = go.Figure()
    x_base = 0
    for i, (label, value) in enumerate(zip(labels, values)):
        fig.add_trace(go.Bar(
            y=[""], x=[value * 100], orientation="h", name=label,
            marker=dict(color=colors[i % len(colors)]), offsetgroup=i,
            base=x_base, text=f"{value * 100:.1f}%", textposition="inside", hoverinfo="name + text"
        ))
        x_base += value * 100

    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis=dict(range=[0, 100], showticklabels=False),
        yaxis=dict(showticklabels=False),
        height=180,
        margin=dict(l=30, r=30, t=40, b=20),
        showlegend=True
    )
    return fig

# charts.py
import math
import plotly.graph_objects as go
import plotly.express as px

def people_outcomes_chart(enrollment, immune_rate, infected, hosp_rate, death_rate, per_unit=None, style="square"):
    """
    Returns (fig, per_unit).
    style: "square" (default), "emoji", or "vector" (stick figures).
    """

    # --- Helper functions ---
    def _bucket_size(e):
        if per_unit:
            return per_unit
        if e > 2000: return 10
        if e > 800:  return 5
        return 1

    def _counts(e, immune_rate, infected, hosp_rate, death_rate):
        immune = int(round(e * immune_rate))
        total_infected = int(round(infected))
        deaths = int(round(total_infected * death_rate))
        hospitalized = int(round(total_infected * hosp_rate))
        hospitalized = min(hospitalized, total_infected)
        deaths = min(deaths, hospitalized)

        susceptible_total = e - immune
        not_infected = max(susceptible_total - total_infected, 0)
        infected_non_hosp = max(total_infected - hospitalized, 0)

        return [
            ("Immune (MMR-protected)", immune, "#6aa84f"),
            ("Susceptible (not infected)", not_infected, "#c9c9c9"),
            ("Infected (no hospital stay)", infected_non_hosp, "#f6b26b"),
            ("Hospitalized", hospitalized - deaths, "#e69138"),
            ("Deaths", deaths, "#cc0000"),
        ]

    def _grid(counts, per_unit):
        """Return per-person unit grid as (xs, ys, colors, labels, cols, rows)."""
        units = []
        for label, n, color in counts:
            k = int(math.ceil(n / per_unit)) if n > 0 else 0
            units.extend([(label, color)] * k)

        N = len(units)
        cols = max(10, int(round(math.sqrt(N))))
        rows = int(math.ceil(N / cols))

        xs, ys, colors, labels = [], [], [], []
        for i, (label, color) in enumerate(units):
            r = i // cols
            c = i % cols
            xs.append(c)
            ys.append(-r)  # stack downward
            colors.append(color)
            labels.append(label)
        return xs, ys, colors, labels, cols, rows

    def _legend_proxies(fig):
        for name, color in [
            ("Immune (MMR-protected)", "#6aa84f"),
            ("Susceptible (not infected)", "#c9c9c9"),
            ("Infected (no hospital stay)", "#f6b26b"),
            ("Hospitalized", "#e69138"),
            ("Deaths", "#cc0000"),
        ]:
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(symbol="square", size=10, color=color),
                name=name, showlegend=True
            ))

    # --- Build initial/final states ---
    pu = _bucket_size(enrollment)
    start_counts = _counts(enrollment, immune_rate, 0, hosp_rate, death_rate)
    final_counts = _counts(enrollment, immune_rate, infected, hosp_rate, death_rate)

    xs0, ys0, c0, labels0, cols, rows = _grid(start_counts, pu)
    xsF, ysF, cF, labelsF, _, _        = _grid(final_counts, pu)

    # Group points by category for consistent coloring/performance
    def _group(xs, ys, cols, labels):
        by = {}
        for x, y, col, lab in zip(xs, ys, cols, labels):
            by.setdefault(lab, {"x": [], "y": [], "color": col})
            by[lab]["x"].append(x); by[lab]["y"].append(y)
        return by

    g0 = _group(xs0, ys0, c0, labels0)
    gF = _group(xsF, ysF, cF, labelsF)
    categories = [
        "Immune (MMR-protected)",
        "Susceptible (not infected)",
        "Infected (no hospital stay)",
        "Hospitalized",
        "Deaths",
    ]

    # ---- STYLE 1: square markers ----
    if style == "square":
        data_init = []
        for cat in categories:
            pts = g0.get(cat, {"x": [], "y": [], "color": "#000"})
            data_init.append(go.Scatter(
                x=pts["x"], y=pts["y"], mode="markers",
                marker=dict(symbol="square", size=12, color=pts["color"], line=dict(width=0)),
                hovertemplate=f"{cat}<extra></extra>", showlegend=False
            ))
        data_final = []
        for cat in categories:
            pts = gF.get(cat, {"x": [], "y": [], "color": "#000"})
            data_final.append(go.Scatter(
                x=pts["x"], y=pts["y"], mode="markers",
                marker=dict(symbol="square", size=12, color=pts["color"], line=dict(width=0)),
                hovertemplate=f"{cat}<extra></extra>", showlegend=False
            ))

    # ---- STYLE 2: emoji stick figure ----
    elif style == "emoji":
        data_init = []
        for cat in categories:
            pts = g0.get(cat, {"x": [], "y": [], "color": "#000"})
            data_init.append(go.Scatter(
                x=pts["x"], y=pts["y"], mode="text",
                text=["🧍"] * len(pts["x"]),
                textfont=dict(size=16, color=pts["color"]),
                hovertemplate=f"{cat}<extra></extra>", showlegend=False
            ))
        data_final = []
        for cat in categories:
            pts = gF.get(cat, {"x": [], "y": [], "color": "#000"})
            data_final.append(go.Scatter(
                x=pts["x"], y=pts["y"], mode="text",
                text=["🧍"] * len(pts["x"]),
                textfont=dict(size=16, color=pts["color"]),
                hovertemplate=f"{cat}<extra></extra>", showlegend=False
            ))

    # ---- STYLE 3: vector stick figure (head + body/arms/legs) ----
    else:  # style == "vector"
        def build_vector_traces(grouped):
            """Return two traces per category: heads (markers) and lines (body/arms/legs)."""
            traces = []
            for cat in categories:
                pts = grouped.get(cat, {"x": [], "y": [], "color": "#000"})
                xs, ys, col = pts["x"], pts["y"], pts["color"]
                # heads
                traces.append(go.Scatter(
                    x=xs, y=ys, mode="markers",
                    marker=dict(symbol="circle", size=8, color=col),
                    hovertemplate=f"{cat}<extra></extra>", showlegend=False
                ))
                # vector lines: build combined polyline with None separators for body+arms+legs
                lx, ly = [], []
                for x, y in zip(xs, ys):
                    # Body: from y-0.25 down to y-0.9
                    lx += [x, x, None]
                    ly += [y - 0.25, y - 0.9, None]
                    # Arms: horizontal at y-0.55
                    lx += [x - 0.3, x + 0.3, None]
                    ly += [y - 0.55, y - 0.55, None]
                    # Legs: from hip (y-0.9) to two feet
                    lx += [x, x - 0.25, None, x, x + 0.25, None]
                    ly += [y - 0.9, y - 1.5, None, y - 0.9, y - 1.5, None]
                traces.append(go.Scatter(
                    x=lx, y=ly, mode="lines",
                    line=dict(width=2, color=col),
                    hoverinfo="skip", showlegend=False
                ))
            return traces

        data_init = build_vector_traces(g0)
        data_final = build_vector_traces(gF)

    # Build figure with consistent trace count/order for animation
    fig = go.Figure(data=data_init, frames=[go.Frame(data=data_final, name="final")])
    _legend_proxies(fig)

    fig.update_layout(
        xaxis=dict(visible=False, range=[-1, cols + 1]),
        yaxis=dict(visible=False, range=[-(rows + 1), 1]),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        updatemenus=[dict(
            type="buttons",
            x=0.0, y=1.15, xanchor="left", yanchor="top",
            showactive=False,
            buttons=[
                dict(label="▶ Start Outbreak", method="animate",
                     args=[["final"], {"frame": {"duration": 700, "redraw": True},
                                       "fromcurrent": True, "transition": {"duration": 250}}]),
                dict(label="↺ Reset", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": True},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    return fig, pu
