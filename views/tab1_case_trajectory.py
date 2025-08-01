# views/tab1_case_trajectory.py

import streamlit as st
import pandas as pd
import plotly.express as px
from helpers import apply_common_plot_layout  

def tab1_view(df):
    states = ["United States"] + sorted(df["state"].unique())
    display_states = [s.title() for s in states]
    state_display = st.selectbox("Select a state", display_states)
    state = states[display_states.index(state_display)]


    filtered = df if state == "United States" else df[df["state"] == state]
    weekly = filtered.groupby("mmwr_week_start", as_index=False)["cases"].sum()
    all_weeks = pd.Series(df["mmwr_week_start"].unique()).sort_values()

    fig = px.bar(
        weekly, x="mmwr_week_start", y="cases", color="cases",
        color_continuous_scale="viridis",
        labels={"mmwr_week_start": "Week of", "cases": "Confirmed Measles Cases"},
        text="cases"
    )
    fig.update_traces(textposition="inside", textfont_size=12)
    fig.update_layout(
        xaxis=dict(categoryorder="array", categoryarray=all_weeks),
        coloraxis_colorbar=dict(title="", x=-0.15, tickvals=[])
    )
    fig = apply_common_plot_layout(fig, "")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"<h2 style='text-align: center; margin-bottom: 0.5rem;'>Confirmed 2025 Weekly Measles Cases in {state}</h2>",
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="blocked-text">
        This is an interactive graph describing the number of total confirmed measles cases in the United States by week (using Sunday as a starting date) throughout 2025.
        Weeks with more cases have taller bars or lighter hues. For weeks with fewer cases, hover over the bar to reveal the exact count.
        There is a dropdown filter above the graph that allows state selection to view any US state's measles cases over time as well.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 0.8rem;'>
        Data Source: <a href='https://github.com/CSSEGISandData/measles_data' target='_blank' style='text-decoration: none;'>JHU Measles Tracking Team Data Repository at Johns Hopkins University</a>
    </div>
    """, unsafe_allow_html=True)
