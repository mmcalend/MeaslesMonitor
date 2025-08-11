import streamlit as st
import numpy as np
import plotly.express as px
from helpers import apply_common_plot_layout

import streamlit as st
import numpy as np
import plotly.express as px
from helpers import apply_common_plot_layout

def tab2_view(df):
    measles_data = df.copy()
    measles_data['state'] = measles_data['state'].replace({'New York City': 'New York'})

    # Group and calculate cumulative cases
    weekly_state = measles_data.groupby(['state', 'code', 'mmwr_week_start'])['cases'].sum().reset_index()
    weekly_state['cumulative_cases'] = weekly_state.groupby('code')['cases'].cumsum()
    weekly_state["log_cases"] = np.log10(weekly_state["cumulative_cases"].replace(0, np.nan))
    weekly_state["week_str"] = weekly_state["mmwr_week_start"].dt.strftime("%b %d")

    # Choropleth animation
    fig = px.choropleth(
        weekly_state,
        locations="code",
        locationmode="USA-states",
        color="log_cases",
        hover_name="state",
        animation_frame="week_str",
        hover_data={"log_cases": False, "cumulative_cases": True, "week_str": False, "code": False},
        scope="usa",
        color_continuous_scale="viridis",
        labels={"cumulative_cases": "Total Cases", "week_str": "Week of"}
    )

    # Safe layout updates
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        title=dict(font=dict(size=18)),
        coloraxis_colorbar=dict(
            title="Confirmed Total Cases<br>(Log Scale)",
            title_side="right",            # ➜ Horizontal title on the right
            title_font=dict(size=12),
            tickvals=[]
        )
    )

    fig = apply_common_plot_layout(fig, "", colorbar=True)
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    # Header and description
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.5rem;'>Confirmed 2025 Weekly Measles Cases in the United States</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class="blocked-text">
        Above is an animated map visualizing the number of cumulative confirmed measles cases in the United States by week (using Sunday as a starting date) throughout 2025.
        As more cases total, the hue gets brighter. There is a slider at the bottom of the map to pause the animation and examine any week.
        Each state label shows total cases on hover.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 0.8rem;'>
        Data Source: <a href='https://github.com/CSSEGISandData/measles_data' target='_blank' style='text-decoration: none;'>JHU Measles Tracking Team Data Repository at Johns Hopkins University</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 0.8rem; font-style: italic;'>
        Note: Case counts shown here are based on the JHU Measles Tracking Team dataset, which aggregates 
        confirmed cases from state and local reports. These counts may differ from CDC's national 
        measles cases due to differences in reporting schedules, data aggregation methods, and 
        classification criteria. Minor discrepancies, such as temporary dips or spikes, can occur 
        when local data is updated or backfilled after initial reporting.
    </div>
    """, unsafe_allow_html=True)

