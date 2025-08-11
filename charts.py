import plotly.graph_objects as go
import math

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


import plotly.graph_objects as go
import math

def people_outcomes_chart(enrollment, immune_rate, infected, hosp_rate, death_rate, per_unit=None):
    # --- Helper functions ---
    def _bucket_size(e):
        if per_unit:
            return per_unit
        if e > 2000: return 10
        if e > 800: return 5
        return 1

    def _make_people_df(e, immune_rate, infected, hosp_rate, death_rate):
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
            ("Immune (MMR-protected)", immune),
            ("Susceptible (not infected)", not_infected),
            ("Infected (no hospital stay)", infected_non_hosp),
            ("Hospitalized", hospitalized - deaths),
            ("Deaths", deaths),
        ]

    def _build_grid(counts, per_unit):
        palette = {
            "Immune (MMR-protected)": "#6aa84f",
            "Susceptible (not infected)": "#c9c9c9",
            "Infected (no hospital stay)": "#f6b26b",
            "Hospitalized": "#e69138",
            "Deaths": "#cc0000",
        }
        units = []
        for label, n in counts:
            units_needed = int(math.ceil(n / per_unit)) if n > 0 else 0
            units.extend([(label, palette[label])] * units_needed)

        N = len(units)
        cols = max(10, int(round(math.sqrt(N))))
        rows = int(math.ceil(N / cols))

        xs, ys, colors, labels = [], [], [], []
        for i, (label, color) in enumerate(units):
            r = i // cols
            c = i % cols
            xs.append(c)
            ys.append(-r)
            colors.append(color)
            labels.append(label)

        return xs, ys, colors, labels, cols, rows

    # --- Build chart ---
    pu = _bucket_size(enrollment)
    start_counts = _make_people_df(enrollment, immune_rate, 0, hosp_rate, death_rate)
    final_counts = _make_people_df(enrollment, immune_rate, infected, hosp_rate, death_rate)

    trace0, cols, rows = _build_grid(start_counts, pu)
    traceF, _, _ = _build_grid(final_counts, pu)

    fig = go.Figure(
        data=[go.Scatter(x=trace0[0], y=trace0[1], mode="markers",
                         marker=dict(symbol="square", size=12, color=trace0[2]),
                         text=trace0[3], hovertemplate="%{text}<extra></extra>", showlegend=False)],
        frames=[go.Frame(data=[go.Scatter(x=traceF[0], y=traceF[1], mode="markers",
                                          marker=dict(symbol="square", size=12, color=traceF[2]),
                                          text=traceF[3], hovertemplate="%{text}<extra></extra>", showlegend=False)],
                         name="final")]
    )

    fig.update_layout(
        xaxis=dict(visible=False, range=[-1, cols+1]),
        yaxis=dict(visible=False, range=[-(rows+1), 1]),
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        updatemenus=[dict(
            type="buttons",
            x=0.0, y=1.12, xanchor="left", yanchor="top",
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
