import streamlit as st
import pandas as pd
import plotly.express as px
from helpers import apply_common_plot_layout  

def tab1_view(df, df_cdc_us):
    df["state"] = df["state"].str.title()
    states = ["United States"] + sorted(df["state"].unique())
    state_display = st.selectbox("Select a state", states)

    if state_display == "United States":
        weekly = df_cdc_us.groupby("mmwr_week_start", as_index=False)["cases"].sum()
    else:
        filtered = df[df["state"] == state_display]
        weekly = filtered.groupby("mmwr_week_start", as_index=False)["cases"].sum()

    all_weeks = pd.Series(weekly["mmwr_week_start"].unique()).sort_values()

    fig = px.bar(
        weekly, x="mmwr_week_start", y="cases", color="cases",
        color_continuous_scale="viridis",
        labels={"mmwr_week_start": "Week of", "cases": "Confirmed Measles Cases"},
        text="cases"
    )
    fig.update_traces(textposition="inside", textfont_size=12)
    fig.update_layout(
        xaxis=dict(categoryorder="array", categoryarray=all_weeks),
        coloraxis_colorbar=dict(title="", x=1, tickvals=[])
    )
    fig = apply_common_plot_layout(fig, "")
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    st.markdown(
        f"<h2 style='text-align: center; margin-bottom: 0.5rem;'>Confirmed 2025 Weekly Measles Cases in {state_display}</h2>",
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="blocked-text">
        Above is an interactive graph describing the number of total confirmed measles cases 
        by week (using Sunday as a starting date) throughout 2025.
        Weeks with more cases have taller bars or lighter hues. 
        For weeks with fewer cases, hover over the bar to reveal the exact count. 
        Use the dropdown to switch between the United States (CDC data) and any state (JHU data).
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 0.8rem;'>
        Data Sources: <br>
        <a href='https://www.cdc.gov/measles/data-research/index.html' target='_blank'> U.S. Centers for Disease Control and Prevention (CDC) </a> (U.S. Level). <br>
        <a href='https://github.com/CSSEGISandData/measles_data' target='_blank'>JHU Measles Tracking Team</a> (State Level) 
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='font-size: 0.8rem; font-style: italic;'>
        Note: Differences between the CDC and JHU counts can occur due to reporting delays, 
        aggregation methods, and case definition criteria.
    </div>
    """, unsafe_allow_html=True)
