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
            base=x_base, text=f"{value * 100:.1f}%", textposition="inside", hoverinfo="text",
            hovertemplate="<b>%{name}</b><br>%{text}<extra></extra>"
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
