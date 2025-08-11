import plotly.graph_objects as go
import math
import plotly.express as px
import numpy as np
import plotly.graph_objects as go


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


def people_outcomes_chart(
    enrollment,
    immune_rate,
    infected,
    hosp_rate,
    death_rate,
    per_unit=None,
    style="heads",                
    show_background=False          
    """
    Returns (fig, per_unit).
    style options: "heads" (circles), "square" (waffle), or "emoji" (🧍).
    """

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

    def _legend(fig):
        for name, color in [
            ("Immune (MMR-protected)", "#6aa84f"),
            ("Susceptible (not infected)", "#c9c9c9"),
            ("Infected (no hospital stay)", "#f6b26b"),
            ("Hospitalized", "#e69138"),
            ("Deaths", "#cc0000"),
        ]:
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(symbol="circle", size=10, color=color),
                name=name, showlegend=True
            ))

    # Build data
    pu = _bucket_size(enrollment)
    start_counts = _counts(enrollment, immune_rate, 0, hosp_rate, death_rate)
    final_counts = _counts(enrollment, immune_rate, infected, hosp_rate, death_rate)

    xs0, ys0, c0, labels0, cols, rows = _grid(start_counts, pu)
    xsF, ysF, cF, labelsF, _, _        = _grid(final_counts, pu)

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

    # Build traces for chosen style (we’ll map “heads” → circle markers)
    def traces_for(grouped, use_mode, marker_kwargs, text_list=None):
        traces = []
        for cat in categories:
            pts = grouped.get(cat, {"x": [], "y": [], "color": "#000"})
            base = dict(
                x=pts["x"], y=pts["y"],
                hovertemplate=f"{cat}<extra></extra>",
                showlegend=False
            )
            if use_mode == "markers":
                base["mode"] = "markers"
                base["marker"] = dict(color=pts["color"], **marker_kwargs)
                traces.append(go.Scatter(**base))
            else:  # text
                base["mode"] = "text"
                base["text"] = text_list or []
                base["textfont"] = dict(size=16, color=pts["color"])
                traces.append(go.Scatter(**base))
        return traces

    if style == "square":
        data0 = traces_for(g0, "markers", dict(symbol="square", size=12, line=dict(width=0)))
        dataF = traces_for(gF, "markers", dict(symbol="square", size=12, line=dict(width=0)))
    elif style == "emoji":
        data0 = traces_for(g0, "text", {}, text_list=["🧍"])
        dataF = traces_for(gF, "text", {}, text_list=["🧍"])
    else:  # "heads" — circles only
        data0 = traces_for(g0, "markers", dict(symbol="circle", size=10, line=dict(width=0)))
        dataF = traces_for(gF, "markers", dict(symbol="circle", size=10, line=dict(width=0)))

    fig = go.Figure(data=data0, frames=[go.Frame(data=dataF, name="final")])
    _legend(fig)

    # Optional school backdrop drawn as shapes (simple building + roof)
    shapes = []
    if show_background:
        # Compute bounds from grid
        x0, x1 = -0.6, cols + 0.6
        y_top, y_bot = 0.6, -(rows + 0.6)
        # Building body
        shapes.append(dict(type="rect", x0=x0, x1=x1, y0=y_top - 0.6, y1=y_top - 2.2,
                           line=dict(color="rgba(0,0,0,0)"),
                           fillcolor="rgba(150,150,180,0.08)", layer="below"))
        # Roof (triangle)
        shapes.append(dict(type="path",
                           path=f"M {x0} {y_top - 0.6} L {(x0+x1)/2} {y_top + 0.2} L {x1} {y_top - 0.6} Z",
                           line=dict(color="rgba(0,0,0,0)"),
                           fillcolor="rgba(150,150,180,0.08)", layer="below"))

    fig.update_layout(
        xaxis=dict(visible=False, range=[-1, cols+1]),
        yaxis=dict(visible=False, range=[-(rows+1), 1]),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        shapes=shapes,
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


def epi_curve_chart(daily_counts, y_max=100):
    """
    Build an epi curve line+bar with a Start Outbreak button (no slider).
    y_max keeps the Y-axis consistent across schools.
    """
    days = np.arange(len(daily_counts))
    y = np.asarray(daily_counts, dtype=float)

    line0 = go.Scatter(x=days, y=[0]*len(days), mode="lines",
                       line=dict(width=3), name="Daily cases")
    bar0  = go.Bar(x=days, y=[0]*len(days), name="")

    lineF = go.Scatter(x=days, y=y, mode="lines",
                       line=dict(width=3), name="Daily cases")
    barF  = go.Bar(x=days, y=y, name="", marker=dict(opacity=0.35))

    fig = go.Figure(
        data=[bar0, line0],
        frames=[go.Frame(data=[barF, lineF], name="final")]
    )
    fig.update_layout(
        xaxis=dict(title="Days since introduction", showgrid=False),
        yaxis=dict(title="Daily new cases (students)", showgrid=False, range=[0, y_max]),
        barmode="overlay",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
        updatemenus=[dict(
            type="buttons",
            x=0.0, y=1.15, xanchor="left", yanchor="top",
            showactive=False,
            buttons=[
                dict(label="▶ Start Outbreak", method="animate",
                     args=[["final"], {"frame": {"duration": 800, "redraw": True},
                                       "fromcurrent": True, "transition": {"duration": 250}}]),
                dict(label="↺ Reset", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": True},
                                    "mode": "immediate"}]),
            ],
        )],
    )
    return fig
