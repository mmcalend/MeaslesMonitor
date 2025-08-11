import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def tab5_view(df_schools):
    # --- Header & Intro ---
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.1rem; margin-top:0; margin-bottom:0.5em;'>
        Estimate the impact of measles on school communities, including infections, hospitalizations, absences, and more.<br>
        <em>Note: Schools with fewer than 20 kindergarten students are excluded from the selection list.</em>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Understanding Disease Transmission ---
    with st.expander("Understanding Disease Transmission (Click to Learn More)", expanded=False):
        st.markdown("""
        **Why is measles so contagious?**
        
        Measles is one of the most contagious diseases known to humans...
        (full original text)
        """)

    st.markdown("""
    <div style='text-align:center; margin-bottom:1em;'>
      <h2 style='text-align:center; margin:0.75em 0 0.5em;'>Scientific Assumptions & Data Sources</h2>
    </div>
    """, unsafe_allow_html=True)

    # --- Assumptions ---
    assumptions_data = [
        {"title": "R₀: 12", "link": "...", "link_text": "PubMed", "bg_color": "#2f2e41", "explanation": "..."},
        {"title": "MMR Rate: ADHS 2024–25", "link": "...", "link_text": "ADHS", "bg_color": "#3d3c5a", "explanation": "..."},
        {"title": "Hospitalization Rate: 20%", "link": "...", "link_text": "NFID", "bg_color": "#47465c", "explanation": "..."},
        {"title": "Death Rate: 0.03%", "link": "...", "link_text": "UChicago", "bg_color": "#4e4d6b", "explanation": "..."},
        {"title": "Isolation: 4 days", "link": "...", "link_text": "Protocol", "bg_color": "#5A4E7A", "explanation": "..."},
        {"title": "Quarantine: 21 days", "link": "...", "link_text": "ADHS", "bg_color": "#6d6b85", "explanation": "..."}
    ]

    cols = st.columns(3)
    for i, assumption in enumerate(assumptions_data):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:{assumption["bg_color"]}; color:white; padding:1rem; border-radius:10px; margin-bottom:0.5rem;'>
              <strong>{assumption["title"]}</strong><br>
              <a href="{assumption["link"]}" target="_blank" style="color:#a5c9ff;">{assumption["link_text"]}</a>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Learn more about {assumption['title']}", key=f"assumption_{i}"):
                st.info(assumption['explanation'])

    # --- Herd Immunity Calculator ---
    with st.expander("Herd Immunity Calculator", expanded=False):
        r0_slider = st.slider("Adjust R₀", 2, 18, 12)
        herd_immunity_threshold = (1 - 1 / r0_slider) * 100
        st.markdown(f"With R₀ = {r0_slider}, we need **{herd_immunity_threshold:.1f}%** vaccinated.")

    # --- Simulation Mode ---
    st.markdown("<h2 style='text-align:center;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)
    mode = st.radio("Select simulation mode:", ["Select a School", "Enter Custom Values"], horizontal=True)
    if mode == "Select a School":
        sel = st.selectbox("School:", df_schools["SCHOOL NAME"].sort_values())
        data = df_schools[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment, immune = int(data["ENROLLED"]), float(data["IMMUNE_MMR"])
    else:
        enrollment = st.number_input("Total Students", 1, 1000, 500)
        immune = st.slider("MMR Immunization Rate", 0.0, 1.0, 0.85)

    susceptible = enrollment * (1 - immune)

    # --- School Details ---
    detail_cols = st.columns(3)
    detail_cols[0].markdown(f"<div style='background:#393855;color:white;padding:0.8rem;border-radius:8px;text-align:center;'><strong>Total Students:</strong><br>{enrollment:,}</div>", unsafe_allow_html=True)
    detail_cols[1].markdown(f"<div style='background:#4b4971;color:white;padding:0.8rem;border-radius:8px;text-align:center;'><strong>MMR Coverage:</strong><br>{immune*100:.1f}%</div>", unsafe_allow_html=True)
    detail_cols[2].markdown(f"<div style='background:#5a5977;color:white;padding:0.8rem;border-radius:8px;text-align:center;'><strong>Susceptible Students:</strong><br>{int(susceptible):,}</div>", unsafe_allow_html=True)

    # --- Simulation ---
    R0, hosp_rate, death_rate, q_days, isolation_days = 12, 0.2, 0.0003, 21, 4
    initial = st.number_input("Initial Infected Students", 1, 50, 1)
    s_frac = susceptible / enrollment if enrollment else 0
    z = 0.0001
    for _ in range(50):
        z = 1 - np.exp(-R0 * z * s_frac)
    attack = min(z, 1.0)
    total_cases = attack * susceptible
    total_exposed = susceptible
    isolate_missed = total_cases * isolation_days
    noninfected = max(total_exposed - total_cases, 0)
    quarantine_missed = noninfected * q_days
    total_days_missed = isolate_missed + quarantine_missed

    # --- Daily Cases Chart ---
    days = np.arange(0, 90)
    dist = (days**5) * np.exp(-days / 2)
    dist /= dist.sum()
    daily = dist * total_cases
    fig = go.Figure([go.Bar(x=days, y=daily, marker_color=px.colors.sequential.Cividis[-2],
                             hovertemplate='Day %{x}<br>New Cases: %{y:.1f}<br>Cumulative: %{customdata:.0f}<extra></extra>',
                             customdata=np.cumsum(daily))])
    peak_day, peak_cases = int(np.argmax(daily)), float(np.max(daily))
    fig.add_annotation(x=peak_day, y=peak_cases,
                       text=f"Peak: Day {peak_day}<br>{peak_cases:.1f} cases",
                       showarrow=True, arrowhead=2, arrowcolor="red", font=dict(color="red"))
    fig.update_layout(xaxis_title="Days since Introduction", yaxis_title="Daily New Cases (students)",
                      plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    # --- Plotly Calendar ---
    school_days, curr = [], datetime.today().date()
    while len(school_days) < 30:
        if curr.weekday() < 5:
            school_days.append(curr)
        curr += timedelta(days=1)
    exclusion_days = set(school_days[:q_days])

    week_nums = [d.isocalendar()[1] for d in school_days]
    weekdays = [d.weekday() for d in school_days]
    z_vals = [1 if d in exclusion_days else 0 for d in school_days]

    fig_cal = go.Figure(data=go.Heatmap(
        x=weekdays,
        y=week_nums,
        z=z_vals,
        text=[d.strftime("%b %d") for d in school_days],
        hovertemplate="Date: %{text}<br>Status: %{z}",
        colorscale=[[0, px.colors.sequential.Cividis[0]], [1, px.colors.sequential.Cividis[-2]]],
        showscale=False
    ))
    fig_cal.update_layout(
        title="School Calendar: Exclusion (Quarantine) Days",
        xaxis=dict(tickmode='array', tickvals=list(range(5)), ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri']),
        yaxis_title="Week #",
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_cal, use_container_width=True)

    # --- Outbreak Summary ---
    summary_data = [
        {"title": "Total Infected", "value": f"{int(total_cases):,}"},
        {"title": "Hospitalizations", "value": f"{int(total_cases*hosp_rate):,}"},
        {"title": "Deaths", "value": f"{int(total_cases*death_rate):,}"},
        {"title": "Exposed Students", "value": f"{int(noninfected):,}"},
        {"title": "Total Missed Days", "value": f"{int(total_days_missed):,}"},
        {"title": "Attack Rate", "value": f"{attack*100:.1f}%"}
    ]
    cols1 = st.columns(3)
    cols2 = st.columns(3)
    all_cols = cols1 + cols2
    for i, item in enumerate(summary_data):
        with all_cols[i]:
            st.markdown(f"<div style='background:{px.colors.sequential.Cividis[i%len(px.colors.sequential.Cividis)]}; color:white; padding:1rem; border-radius:8px; text-align:center;'>{item['title']}<br>{item['value']}</div>", unsafe_allow_html=True)

