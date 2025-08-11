import streamlit as st
import pandas as pd
import plotly.express as px
from helpers import apply_common_plot_layout

DISCLAIMER = (
    "U.S. total uses CDC rash-onset weeks with retrospective corrections. "
    "States use JHU/CSSE compilation from state health departments (onset when available; "
    "reporting practices vary). Weekly dips/spikes may reflect reporting timing, not true incidence."
)

def _prep_week_axis(*dfs):
    weeks = pd.Index([])
    for d in dfs:
        if d is not None and not d.empty and "mmwr_week_start" in d.columns:
            weeks = weeks.union(pd.to_datetime(d["mmwr_week_start"], errors="coerce"))
    weeks = weeks.dropna().sort_values()
    return weeks.tolist()

def _aggregate_weekly(dfin):
    return (
        dfin.groupby("mmwr_week_start", as_index=False)["cases"]
        .sum()
        .sort_values("mmwr_week_start")
    )

def tab1_view(df: pd.DataFrame, df_us_cdc: pd.DataFrame | None = None):
    if "state" in df.columns:
        df["state"] = df["state"].astype(str).str.title()

    states = ["United States"]
    if "state" in df.columns:
        states += sorted([s for s in df["state"].dropna().unique() if s and s != "United States"])
    state = st.selectbox("Select a state", states)

    is_us = (state == "United States")
    if is_us:
        if df_us_cdc is not None and not df_us_cdc.empty:
            weekly = df_us_cdc[["mmwr_week_start", "cases"]].copy()
            source_label = "Source: CDC (rash-onset week)"
        else:
            weekly = _aggregate_weekly(df.copy())
            source_label = "Source: JHU/CSSE (national aggregation)"
    else:
        filtered = df[df["state"] == state].copy()
        weekly = _aggregate_weekly(filtered)
        source_label = "Source: JHU/CSSE (state compilation)"

    weekly["mmwr_week_start"] = pd.to_datetime(weekly["mmwr_week_start"], errors="coerce")
    all_weeks = _prep_week_axis(df, df_us_cdc)

    fig = px.bar(
        weekly,
        x="mmwr_week_start",
        y="cases",
        color="cases",
        color_continuous_scale="viridis",
        labels={"mmwr_week_start": "Week of", "cases": "Confirmed Measles Cases"},
        text="cases",
    )
    fig.update_traces(textposition="inside", textfont_size=12, cliponaxis=False)
    fig.update_layout(
        xaxis=dict(
            title="Week of",
            categoryorder="array",
            categoryarray=all_weeks if all_weeks else None,
            tickformat="%b %-d",
        ),
        yaxis_title="Confirmed Measles Cases",
        coloraxis_colorbar=dict(title="", x=-0.05, tickvals=[]),
        margin=dict(l=10, r=10, t=10, b=10),
    )

    st.markdown('<div style="overflow-x: auto; padding-bottom: 1rem;">', unsafe_allow_html=True)
    fig = apply_common_plot_layout(fig, "")
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"<h2 style='text-align: center; margin-bottom: 0.5rem;'>Confirmed 2025 Weekly Measles Cases in {state}</h2>",
        unsafe_allow_html=True,
    )
    st.caption(source_label)
    st.caption(DISCLAIMER)

    st.markdown(
        """
        <div class="blocked-text">
            Above is an interactive graph describing the number of total confirmed measles cases by MMWR week (Sunday start) throughout 2025.
            Weeks with more cases have taller bars or lighter hues. Hover over a bar to see the exact count.
            Use the dropdown above to view any U.S. state's measles cases over time.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style='font-size: 0.8rem;'>
            Data Sources:
            <a href='https://github.com/CSSEGISandData/measles_data' target='_blank' style='text-decoration: none;'>JHU Measles Tracking Team Data Repository</a>
            &nbsp;•&nbsp;
            <a href='https://www.cdc.gov/measles/data-research/index.html' target='_blank' style='text-decoration: none;'>CDC Measles Data (epi-curve)</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if is_us and df_us_cdc is not None and not df_us_cdc.empty:
        latest = pd.to_datetime(df_us_cdc["mmwr_week_start"]).max()
        if pd.notna(latest):
            st.caption(f"Updated through: {latest:%b %d, %Y}")

    st.markdown(
        """
        ---
        **About this chart**  
        The "United States" view uses CDC's national measles epi-curve based on **rash-onset week**.  
        This method places each case in the week symptoms began, and CDC backfills data when late reports arrive — creating a smoother national curve.  

        The state-level views use data compiled by the JHU Measles Tracking Team from official state health department reports.  
        These state-level counts may be based on **report dates** or **onset dates**, depending on state practices, and are updated daily.  
        As a result, the national total from the state data may differ from the CDC national epi-curve in timing or weekly patterns.  
        Short-term dips/spikes are often due to reporting schedules and do not necessarily reflect actual changes in transmission.
        """
    )
