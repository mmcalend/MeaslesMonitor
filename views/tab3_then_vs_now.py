import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from helpers import apply_common_plot_layout
import plotly.graph_objects as go

def tab3_view(df, df19, mmr):
    state = st.selectbox("Select a state for 2019 vs 2025 comparison", ["United States"] + sorted(df19["State"].unique()))

    # --- Merge 2025 and 2019 case data ---
    state_cases = df.groupby('code')['cases'].sum().reset_index()
    merged = pd.merge(state_cases, df19, left_on='code', right_on='code')
    filtered_merged = merged if state == "United States" else merged[merged["State"] == state]

    # --- Measles 2019 vs 2025 comparison chart ---
    state_names = filtered_merged["State"]
    fig = go.Figure([
        go.Bar(x=filtered_merged["code"], y=filtered_merged["cases"], name="2025 Cases", marker_color="#6A4C93", opacity=0.8, customdata=state_names, hovertemplate=("%{customdata}<br>" "2025 Cases: %{y}<extra></extra>" ))
        go.Scatter(x=filtered_merged["code"], y=filtered_merged["Cases"], mode="lines", fill="tozeroy", name="2019 Cases", line=dict(color="#B497BD"), customdata=state_names, hovertemplate=("%{customdata}<br>" "2019 Cases: %{y}<extra></extra>" ))
    ])
    fig.update_layout(
        barmode="overlay",
        hovermode="x unified",
        legend=dict(orientation = "h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=12)),
        xaxis=dict(categoryorder="category ascending", rangeslider=dict(visible=False), type="category")
    )
    fig = apply_common_plot_layout(fig, "")
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    st.markdown(f"<h2 style='text-align: center; margin-bottom: 0.5rem;'>{state} Measles Outbreaks: 2019 vs 2025</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class="blocked-text">
        This graph compares total measles cases by state during 2019 vs 2025, highlighting changes in outbreak geography.
        The lighter purple bars represent 2019 measles cases, which was the previous biggest outbreak in the US before 2025, which are represented by the darker purple bars.  In addition, there is a dropdown filter above the graph that allows state selection to compare any US state's measles cases between the two years.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 0.8rem;'>
        <a href='https://data.cdc.gov/NNDSS/NNDSS-TABLE-1V-Malaria-to-Measles-Imported/jf8m-mtc3/about_data' target='_blank'>2019 Data Source: NNDSS TABLE 1V</a><br>
        <a href='https://github.com/CSSEGISandData/measles_data' target='_blank'>2025 Data Source: JHU Measles Tracking Team</a>
    </div>
    """, unsafe_allow_html=True)

    # --- Preprocess MMR vaccination data ---
    mmr["estimate_pct"] = mmr["estimate_pct"].str.replace('%', '').astype(float)
    mmr_filtered = mmr[mmr["school_year"].isin(["2018-19", "2023-24"])].copy()
    mmr_comparison = mmr_filtered.pivot(index=["state", "code"], columns="school_year", values="estimate_pct").reset_index()
    mmr_comparison = mmr_comparison.dropna()
    mmr_comparison.columns.name = None
    mmr_comparison = mmr_comparison.rename(columns={
        "2018-19": "MMR Rate 2018-19",
        "2023-24": "MMR Rate 2023-24"
    })

    filtered_mmr_comparison = mmr_comparison if state == "United States" else mmr_comparison[mmr_comparison["state"] == state]
    threshold = 95
    x_codes = filtered_mmr_comparison["code"]
    y_2018 = filtered_mmr_comparison["MMR Rate 2018-19"]
    y_2023 = filtered_mmr_comparison["MMR Rate 2023-24"]
    
    below_thresh = (y_2023 < threshold).sum()
    

    n_states = len(x_codes)
    dynamic_height = max(600, n_states * 25 + 150)

    fig = go.Figure()

    
    for idx, code in enumerate(x_codes):
        fig.add_trace(go.Scatter(
            x=[y_2018.iloc[idx], y_2023.iloc[idx]],
            y=[code, code],
            mode='lines',
            line=dict(color='#B0B0B0', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))

    state_names = filtered_mmr_comparison["state"]
    fig.add_trace(go.Scatter(
        x=y_2018,
        y=x_codes,
        mode='markers',
        name="2018–19",
        marker=dict(size=10, color="#B497BD", symbol="circle-open"),
        customdata=state_names,
        hovertemplate=(
        "%{customdata}<br>"
        "<br>2018–19: %{x}%<extra></extra>"
    )
    ))

    
    fig.add_trace(go.Scatter(
        x=y_2023,
        y=x_codes,
        mode='markers',
        name="2023–24",
        marker=dict(size=10, color="#6A4C93", symbol="circle"),
        customdata=state_names,
        hovertemplate=(
        "%{customdata}<br>"
        "<br>2023–24: %{x}%<extra></extra>"
    )
    ))

 
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="gray",
        annotation_text="95% Herd Immunity Target",
        annotation_position="top right",
        annotation_font_size=12
    )

    fig.update_layout(
        xaxis=dict(title="MMR Vaccination Rate (%)", range=[75, 100]),
        yaxis=dict(title="", tickfont=dict(size=12), automargin=True),
        height=dynamic_height,
        title_text="MMR Vaccination Rates by State: 2018–19 vs 2023–24",
        legend=dict(title="", orientation = "h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=12)),
        margin=dict(l=80, r=20, t=50, b=50),
        yaxis_categoryorder="category ascending"
    )
    
    fig = apply_common_plot_layout(fig, "")
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    st.markdown(f"<h2 style='text-align: center; margin-bottom: 0.5rem;'>Measles, Mumps, and Rubella (MMR) Kindergarten Vaccination Rates per School Year</h2>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='text-align: center; font-size: 1.1rem; margin-top: 1rem;'>
       <span style='color:#E45756'>{below_thresh} U.S. states</strong> had MMR coverage <span style='color:#E45756'>below the 95% herd immunity threshold</span> in 2023–24.
    </div>
    """, unsafe_allow_html=True)

    
    st.markdown("""
    <div class="blocked-text">
    The MMR vaccine has been used in the United States since the 1970s and has a proven track record of safety. Most side effects are mild—such as fever or soreness at the injection site—and serious adverse reactions are extremely rare. To stop measles outbreaks, communities need at least <strong>95% vaccination coverage</strong> to achieve <strong>herd immunity</strong>. This protects everyone, including vulnerable people.
    <br> <br>
    This chart connects each state’s MMR vaccination rate in 2018–2019 (solid dot) with its rate in 2023–2024 (open dot), showing direction and magnitude of change. A dashed line marks the 95% herd immunity threshold. States without data in either year are excluded.
    </div>
    <div style='font-size: 0.8rem;'>
    Source: <a href='https://www.cdc.gov/measles/data-research/index.html' target='_blank' style='color:inherit'>CDC MMR vaccine coverage for kindergarteners (2009–2024)</a>.
    </div>
    """, unsafe_allow_html=True)

    

