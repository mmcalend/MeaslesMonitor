import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Tunables
R0_DEFAULT = 12
HOSP_RATE = 0.20
DEATH_RATE = 0.0003
QUARANTINE_DAYS = 21
ISOLATION_DAYS = 4
SIM_DAYS = 90
EPICURVE_Y_MAX = 15 # fixed y-axis max

def _plain_language_assumptions():
    st.markdown("""
**What these settings mean (plain language):**
- **R₀ (contagiousness):** higher means one sick person infects more people. We use 12.
- **MMR immunization rate:** share of students protected by vaccine. Lower → more at risk.
- **Hospitalization:** we assume ~20% of infections need hospital care.
- **Death rate:** ~0.03% (rare, but not zero).
- **Isolation:** sick students stay home for **4 days after rash** starts.
- **Quarantine:** un/under-vaccinated exposed students stay home **21 days** after last exposure.
- **Curve shape:** a typical outbreak that rises, peaks, then fades as fewer are susceptible.
""")

def _gamma_like_distribution(days):
    dist = (days**5) * np.exp(-days / 2)
    return dist / dist.sum() if dist.sum() > 0 else dist

def _slider_only_epicurve(days, daily, y_max=EPICURVE_Y_MAX):
    frames = []
    for d in range(len(days)):
        y_frame = np.where(days <= d, daily, 0)
        frames.append(go.Frame(data=[go.Bar(x=days, y=y_frame)], name=str(d)))

    # initial frame = day 0
    base_y = np.where(days <= 0, daily, 0)
    fig = go.Figure(
        data=[go.Bar(
            x=days,
            y=base_y,
            marker_color=px.colors.sequential.Cividis[-2],
            hovertemplate='Day %{x}<br>Cases %{y:.0f}<extra></extra>'
        )],
        frames=frames
    )
    fig.update_layout(
        xaxis=dict(title="Days since Introduction", showgrid=False, range=[0, days.max()]),
        yaxis=dict(title="Daily New Cases (students)", showgrid=False, range=[0, y_max]),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0),
        sliders=[dict(
            active=0, y=1.05, x=0.12,
            currentvalue=dict(prefix="Day ", visible=True, xanchor="right"),
            steps=[dict(method="animate", label=str(d),
                        args=[[str(d)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}])
                   for d in range(len(days))]
        )]
        # No updatemenus → no play/pause btoutns
    )
    return fig

def tab5_view(df_schools):
    # --- Header ---
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.05rem; margin-top:0; margin-bottom:0.5em;'>
        Estimate the impact of measles on a school: infections, hospitalizations, absences, and more.
        <br><em>Note: Schools with fewer than 20 kindergarten students are excluded from the list.</em>
      </p>
      <h2 style='text-align:center; margin:0.75em 0 0.5em;'>Assumptions & Data Sources</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
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

    with st.expander("What do these assumptions mean? (plain language)", expanded=False):
        _plain_language_assumptions()

    # --- Simulation Mode & School Details ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)
    mode = st.radio("Simulation mode", ["Select a School", "Enter Custom Values"],
                    horizontal=True, label_visibility="collapsed")  # accessibility fix

    if mode == "Select a School":
        sel = st.selectbox("School", df_schools["SCHOOL NAME"].sort_values(), index=0)
        row = df_schools[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment = int(row["ENROLLED"])
        immune = float(row["IMMUNE_MMR"])
        st.caption("Using school-reported kindergarten enrollment and MMR coverage for this simulation.")
    else:
        enrollment = st.number_input("Total Students", min_value=1, max_value=5000, value=500, step=10)
        immune = st.slider("MMR Immunization Rate", min_value=0.0, max_value=1.0, value=0.85, step=0.01)
        st.caption("Tip: try lower/higher MMR coverage to see how the outbreak changes.")

    susceptible = enrollment * (1 - immune)

    st.markdown(f"""
    <div style='text-align:center; margin-bottom:1em;'>
      <h2 style='margin-bottom:0.3em;'>School Details</h2>
      <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem;'>
        <div title='Total kindergarten students' style='background:#393855; color:white; padding:0.8rem; border-radius:8px; width:180px;'>
          <strong>Total Students Enrolled:</strong><br>{enrollment:,}
        </div>
        <div title='Share of students protected by MMR' style='background:#4b4971; color:white; padding:0.8rem; border-radius:8px; width:180px;'>
          <strong>MMR Coverage:</strong><br>{immune*100:.1f}%
        </div>
        <div title='Students who could still get measles' style='background:#5a5977; color:white; padding:0.8rem; border-radius:8px; width:180px;'>
          <strong>Susceptible Students:</strong><br>{int(susceptible):,}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Simulation Calculations ---
    R0 = R0_DEFAULT
    st.number_input("Initial Infected Students", min_value=1, max_value=200, value=1, step=1, key="init_cases")  # kept for UI parity
    s_frac = susceptible / enrollment if enrollment else 0
    z = 0.0001
    for _ in range(60):
        z = 1 - np.exp(-R0 * z * s_frac)
    attack = float(min(max(z, 0.0), 1.0))
    total_cases = attack * susceptible

    hosp_rate, death_rate = HOSP_RATE, DEATH_RATE
    q_days, isolation_days = QUARANTINE_DAYS, ISOLATION_DAYS
    total_exposed = susceptible
    isolate_missed = total_cases * isolation_days
    noninfected = max(total_exposed - total_cases, 0)
    quarantine_missed = noninfected * q_days
    total_days_missed = isolate_missed + quarantine_missed

    # --- Estimated Daily Measles Cases (slider animation, fixed y) ---
    days = np.arange(0, SIM_DAYS)
    daily = _gamma_like_distribution(days) * total_cases
    fig = _slider_only_epicurve(days, daily, y_max=EPICURVE_Y_MAX)
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Estimated Daily Measles Cases</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="blocked-text">
      This chart shows estimated new cases by day for {SIM_DAYS} days after measles is introduced.
      The **y-axis is fixed** at {EPICURVE_Y_MAX} students/day so different schools can be compared fairly.
      Drag the slider to watch how the outbreak grows and fades over time.
    </div>
    """, unsafe_allow_html=True)

    # --- School Calendar: Exclusion (Quarantine) Days ---
    school_days, curr = [], datetime.today().date()
    while len(school_days) < 30:
        if curr.weekday() < 5:
            school_days.append(curr)
        curr += timedelta(days=1)
    exclusion_days = set(school_days[:q_days])

    cal_html = "<div style='max-width:680px; margin:auto;'><table style='width:100%; text-align:center; border-collapse:collapse;'><tr>"
    cal_html += ''.join(f"<th style='padding:6px;border-bottom:1px solid#ccc'>{wd}</th>" for wd in ['Mon','Tue','Wed','Thu','Fri']) + '</tr>'
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
    st.markdown(f"""
    <div class="blocked-text">
      <strong>What the calendar means:</strong> students with measles stay home for <strong>{ISOLATION_DAYS} days after rash</strong>.
      Unvaccinated or not fully vaccinated exposed students are kept home for <strong>{QUARANTINE_DAYS} days</strong> after their last exposure.
      The shaded dates show the next 30 school weekdays with potential quarantine days if an outbreak began now.
    </div>
    """, unsafe_allow_html=True)

    # --- Outbreak Summary ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Outbreak Summary</h2>", unsafe_allow_html=True)
    colors = px.colors.sequential.Cividis
    st.markdown(f"""
    <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem; margin-bottom:2em;'>
      <div title='Total infections among susceptible students' style='background:{colors[-3]}; color:white; padding:1rem; border-radius:8px; width:180px;'>
        <strong>Total Infected</strong><br>{int(total_cases):,}
      </div>
      <div title='Hospitalizations = infections × {HOSP_RATE:.0%}' style='background:{colors[-4]}; color:white; padding:1rem; border-radius:8px; width:180px;'>
        <strong>Hospitalizations</strong><br>{int(total_cases*HOSP_RATE):,}
      </div>
      <div title='Deaths = infections × {DEATH_RATE:.3%}' style='background:{colors[-5]}; color:white; padding:1rem; border-radius:8px; width:180px;'>
        <strong>Deaths</strong><br>{int(total_cases*DEATH_RATE):,}
      </div>
      <div title='Exposed but not infected' style='background:{colors[-6]}; color:white; padding:1rem; border-radius:8px; width:180px;'>
        <strong>Exposed Students</strong><br>{int(noninfected):,}
      </div>
      <div title='Missed days = cases×{ISOLATION_DAYS} + exposed×{QUARANTINE_DAYS}' style='background:{colors[-7]}; color:white; padding:1rem; border-radius:8px; width:180px;'>
        <strong>Missed Days</strong><br>{int(total_days_missed):,}
      </div>
      <div title='Attack rate among susceptibles' style='background:{colors[-8]}; color:white; padding:1rem; border-radius:8px; width:180px;'>
        <strong>Attack Rate</strong><br>{attack*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Disclaimer ---
    st.markdown("""
    <div class="blocked-text">
      <strong>Disclaimer:</strong> This tool simplifies complex public health dynamics and assumes no extra interventions (like targeted vaccination, masking, or school closures). It also ignores holidays and behavior changes. Use for illustration and planning only; consult ADHS for real-time guidance and requirements.
    </div>
    """, unsafe_allow_html=True)

