import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def tab5_view(df_schools):
    # --- Header & Assumptions ---
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.1rem; margin-top:0; margin-bottom:0.5em;'>
        Estimate the impact of measles on school communities, including infections, hospitalizations, absences, and more.<br>
        <em>Note: Schools with fewer than 20 kindergarten students are excluded from the selection list.</em>
      </p>
      <h2 style='text-align:center; margin:0.75em 0 0.5em;'>Assumptions & Data Sources</h2>
    </div>
    <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem; margin-bottom:2em;'>
      <div tabindex="0" title='PubMed: R₀ = 12 (PMID: 28757186)' style='background:#2f2e41; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>R₀:</strong><br>12 <a href="https://pubmed.ncbi.nlm.nih.gov/28757186/" target="_blank" style="color:#a5c9ff;">PubMed</a>
      </div>
      <div tabindex="0" title='ADHS: MMR kindergarten coverage for 2024–25 (schools ≥20 kindergarten students)' style='background:#3d3c5a; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>MMR Rate:</strong><br>ADHS 2024–25 <a href="https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage" target="_blank" style="color:#a5c9ff;">ADHS</a>
      </div>
      <div tabindex="0" title='NFID: Hospitalization rate ≈ 20%' style='background:#47465c; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Hospitalization Rate:</strong><br>20% <a href="https://www.nfid.org/infectious-disease/measles/" target="_blank" style="color:#a5c9ff;">NFID</a>
      </div>
      <div tabindex="0" title='UChicago Medicine: Death rate ≈ 0.03%' style='background:#4e4d6b; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Death Rate:</strong><br>0.03% <a href="https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease" target="_blank" style="color:#a5c9ff;">UChicago</a>
      </div>
      <div tabindex="0" title='Isolation Period = 4 days post-rash (AAC R9-6-355)' style='background:#5A4E7A; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Isolation:</strong><br>4 days <a href="https://www.azdhs.gov/documents/…/measles-protocol.pdf" target="_blank" style="color:#a5c9ff;">Protocol</a>
      </div>
      <div tabindex="0" title='Quarantine Period= 21 days (ADHS)' style='background:#6d6b85; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Quarantine:</strong><br>21 days <a href="https://www.azdhs.gov/documents/…/mmr-guidance.pdf" target="_blank" style="color:#a5c9ff;">ADHS</a>
      </div>
    </div>
    """, unsafe_allow_html=True)


    # --- Simulation Mode & School Details ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)
    mode = st.radio("", ["Select a School", "Enter Custom Values"], horizontal=True)
    if mode == "Select a School":
        sel = st.selectbox("School:", df_schools["SCHOOL NAME"].sort_values())
        data = df_schools[df_schools["SCHOOL NAME"]==sel].iloc[0]
        enrollment = int(data["ENROLLED"])
        immune = float(data["IMMUNE_MMR"])
    else:
        enrollment = st.number_input("Total Students", 1, 1000, 500)
        immune = st.slider("MMR Immunization Rate", 0.0, 1.0, 0.85)
    susceptible = enrollment * (1 - immune)
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:1em;'>
      <h2 style='margin-bottom:0.3em;'>School Details</h2>
      <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem;'>
        <div title='Total Kindergarten Students Enrolled' style='background:#393855; color:white; padding:0.8rem; border-radius:8px; width:160px;'>
          <strong>Total Students Enrolled:</strong> {enrollment:,}
        </div>
        <div title='MMR Immunization Rate' style='background:#4b4971; color:white; padding:0.8rem; border-radius:8px; width:160px;'>
          <strong>MMR Kindergarten Coverage:</strong> {immune*100:.1f}%
        </div>
        <div title='Enrollment × (1 - MMR rate)' style='background:#5a5977; color:white; padding:0.8rem; border-radius:8px; width:160px;'>
          <strong>Susceptible Students:</strong> {int(susceptible):,}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Simulation Calculations ---
    R0 = 12
    initial = st.number_input("Initial Infected Students", 1, 50, 1)
    s_frac = susceptible / enrollment if enrollment else 0
    z = 0.0001
    for _ in range(50):
        z = 1 - np.exp(-R0 * z * s_frac)
    attack = min(z, 1.0)
    total_cases = attack * susceptible
    hosp_rate, death_rate, q_days, isolation_days = 0.2, 0.0003, 21, 4
    total_exposed = susceptible
    isolate_missed = total_cases * isolation_days
    noninfected = max(total_exposed - total_cases, 0)
    quarantine_missed = noninfected * q_days
    total_days_missed = isolate_missed + quarantine_missed
    
    # --- Estimated Daily Measles Cases ---
    days = np.arange(0, 90)
    dist = (days**5) * np.exp(-days / 2)
    dist /= dist.sum()
    daily = dist * total_cases
    colors = px.colors.sequential.Cividis
    bar_color = colors[-2]
    fig = go.Figure([
        go.Bar(
            x=days,
            y=daily,
            marker_color=bar_color,
            hovertemplate='Day %{x}<br>Cases %{y:.0f}<extra></extra>'
        )
    ])
    fig.update_layout(
        xaxis=dict(title="Days since Introduction", showgrid=False),
        yaxis=dict(title="Daily New Cases (students)", showgrid=False),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Estimated Daily Measles Cases</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class="blocked-text">
      This bar chart shows the projected number of new measles cases per school day over a 90-day period following the introduction of the virus into the school.
      "Days since Introduction" plots each day from Day 0 (first case) to Day 89 and "Daily New Cases (students)" shows the estimated count of newly infected students on each day.
      The curve follows a gamma distribution: it rises gradually as the outbreak grows, peaks around Day 12 when most susceptible students have been exposed, then tapers off as fewer susceptibles remain.
      Hovering over each bar reveals the exact day and number of cases.
    </div>
    """, unsafe_allow_html=True)

    # --- School Calendar: Exclusion (Quarantine) Days ---
    school_days, curr = [], datetime.today().date()
    while len(school_days) < 30:
        if curr.weekday() < 5:
            school_days.append(curr)
        curr += timedelta(days=1)
    exclusion_days = set(school_days[:q_days])
    # Fixed-width container
    cal_html = "<div style='max-width:680px; margin:auto;'><table style='width:100%; text-align:center; border-collapse:collapse;'><tr>"
    cal_html += ''.join(
        f"<th style='padding:6px;border-bottom:1px solid#ccc'>{wd}</th>" for wd in ['Mon','Tue','Wed','Thu','Fri']
    ) + '</tr>'
    i = 0
    while i < len(school_days):
        week = '<tr>'
        wd0 = school_days[i].weekday()
        week += ''.join("<td style='padding:12px;border:1px solid#eee;background:#f0f0f0'></td>" for _ in range(wd0))
        for wd in range(wd0, 5):
            if i >= len(school_days):
                week += "<td style='padding:12px;border:1px solid#eee;background:#f0f0f0'></td>"
            else:
                d = school_days[i]
                style = 'background:#2f2e41; color:white; ' if d in exclusion_days else ''
                title = f"Quarantine Day {i+1}" if d in exclusion_days else ''
                week += f"<td title='{title}' style='padding:12px;border:1px solid#eee;{style}'>{d.strftime('%b %d')}</td>"
                i += 1
        week += '</tr>'
        cal_html += week
    cal_html += '</table></div>'
    st.markdown(cal_html, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>School Calendar: Exclusion (Quarantine) Days</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class="blocked-text">
      Confirmed measles cases must be kept out of school from symptom onset through 4 days after rash onset.
      Unvaccinated or incompletely vaccinated exposed students are excluded for 21 days after last exposure.
      This calendar grid shows the next 30 school weekdays with shaded cells marking quarantine days if an outbreak were to occur. Hover for day number.
    </div>
    """, unsafe_allow_html=True)

    # --- Outbreak Summary ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Outbreak Summary</h2>", unsafe_allow_html=True)
    summary_html = f"""
    <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem; margin-bottom:2em;'>
      <div title='Total Infections = Enrollment × Attack Rate' style='background:{colors[-3]}; color:white; padding:1rem; border-radius:8px; width:160px; cursor:help;'>
        <strong>Total Infected</strong><br>{int(total_cases):,}
      </div>
      <div title='Hospitalizations = Total Infected × 0.20' style='background:{colors[-4]}; color:white; padding:1rem; border-radius:8px; width:160px; cursor:help;'>
        <strong>Hospitalizations</strong><br>{int(total_cases*hosp_rate):,}
      </div>
      <div title='Deaths = Total Infected × 0.0003' style='background:{colors[-5]}; color:white; padding:1rem; border-radius:8px; width:160px; cursor:help;'>
        <strong>Deaths</strong><br>{int(total_cases*death_rate):,}
      </div>
      <div title='Exposed (Not Infected) = Enrollment × (1 - Immune Rate)' style='background:{colors[-6]}; color:white; padding:1rem; border-radius:8px; width:160px; cursor:help;'>
        <strong>Exposed Students</strong><br>{int(noninfected):,}
      </div>
      <div title='Missed Days = Cases × 4 days + (Exposed but not infected) × 21 days' style='background:{colors[-7]}; color:white; padding:1rem; border-radius:8px; width:160px; cursor:help;'>
        <strong>Missed Days</strong><br>{int(total_days_missed):,}
      </div>
      <div title='Attack Rate = 1 - exp(-R₀ × z × s_frac)' style='background:{colors[-8]}; color:white; padding:1rem; border-radius:8px; width:160px; cursor:help;'>
        <strong>Attack Rate</strong><br>{attack*100:.1f}%
      </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    # --- Disclaimer ---
    st.markdown("""
    <div class="blocked-text">
      <strong>Disclaimer:</strong> This model simplifies public health dynamics under fixed parameters and assumes no additional interventions. It excludes holidays and behavioral changes. Use illustratively. Consult ADHS for real-time guidance.
    </div>
    """, unsafe_allow_html=True)
