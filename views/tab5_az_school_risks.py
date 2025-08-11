# views/tab5_az_school_risks.py

import math
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta

# charts.py must provide these:
#   - people_outcomes_chart(enrollment, immune_rate, infected, hosp_rate, death_rate, per_unit=None, style="heads", show_background=True) -> (fig, per_unit)
#   - epi_curve_chart(daily_counts, y_max=100) -> fig
from charts import people_outcomes_chart, epi_curve_chart


# -------- Tunables (easy to tweak) --------
R0_DEFAULT       = 12
HOSP_RATE        = 0.20
DEATH_RATE       = 0.0003
QUARANTINE_DAYS  = 21
ISOLATION_DAYS   = 4
SIM_DAYS         = 90      # for the epi-curve distribution
EPI_Y_MAX        = 100     # fixed y-axis cap for comparability


def _assumptions_plain_language():
    st.markdown("""
**Plain-language overview of assumptions**
- **How contagious (R₀):** If one student gets measles, they could infect about **12** others in a fully susceptible group.
- **MMR coverage:** The share of students already protected. Lower coverage → more students at risk.
- **Hospitalizations:** We assume **20%** of infections need hospital care.
- **Deaths:** Very rare but not zero — we use **0.03%** of infections.
- **Isolation:** A student with measles stays home **4 days after rash** starts.
- **Quarantine:** Un/under-vaccinated exposed students stay home **21 days** after last exposure.
- **Outbreak pattern (simplified):** Cases grow, peak, and fall as fewer susceptible students remain.
""")


def tab5_view(df_schools: pd.DataFrame):
    # ---------- Header & callouts ----------
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.05rem; margin-top:0; margin-bottom:0.5em;'>
        Education-focused tool to estimate potential infections, hospitalizations, and missed school days
        based on enrollment and MMR coverage.
        <br><em>Note: Schools with fewer than 20 kindergarten students are excluded from the list.</em>
      </p>
      <h2 style='text-align:center; margin:0.75em 0 0.5em;'>Assumptions & Data Sources</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem; margin-bottom:2em;'>
      <div tabindex="0" title='PubMed: R₀ ≈ 12 (PMID: 28757186)' style='background:#2f2e41; color:white; padding:1rem; border-radius:10px; width:220px; cursor:help;'>
        <strong>R₀ (contagiousness)</strong><br>≈ 12 <a href="https://pubmed.ncbi.nlm.nih.gov/28757186/" target="_blank" style="color:#a5c9ff;">PubMed</a>
      </div>
      <div tabindex="0" title='ADHS: 2024–25 MMR kindergarten coverage (schools ≥20 K students)' style='background:#3d3c5a; color:white; padding:1rem; border-radius:10px; width:220px; cursor:help;'>
        <strong>MMR coverage data</strong><br>ADHS 2024–25 <a href="https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage" target="_blank" style="color:#a5c9ff;">ADHS</a>
      </div>
      <div tabindex="0" title='NFID: Hospitalization rate ≈ 20%' style='background:#47465c; color:white; padding:1rem; border-radius:10px; width:220px; cursor:help;'>
        <strong>Hospitalization rate</strong><br>20% <a href="https://www.nfid.org/infectious-disease/measles/" target="_blank" style="color:#a5c9ff;">NFID</a>
      </div>
      <div tabindex="0" title='UChicago Medicine: Death rate ≈ 0.03%' style='background:#4e4d6b; color:white; padding:1rem; border-radius:10px; width:220px; cursor:help;'>
        <strong>Death rate</strong><br>0.03% <a href="https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease" target="_blank" style="color:#a5c9ff;">UChicago</a>
      </div>
      <div tabindex="0" title='Isolation = 4 days post-rash (AAC R9-6-355)' style='background:#5A4E7A; color:white; padding:1rem; border-radius:10px; width:220px; cursor:help;'>
        <strong>Isolation</strong><br>4 days
      </div>
      <div tabindex="0" title='Quarantine = 21 days after last exposure (ADHS)' style='background:#6d6b85; color:white; padding:1rem; border-radius:10px; width:220px; cursor:help;'>
        <strong>Quarantine</strong><br>21 days
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("What do these assumptions mean? (plain language)", expanded=False):
        _assumptions_plain_language()

    # ---------- Inputs ----------
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)

    mode = st.radio(
        "Simulation mode",
        ["Select a School", "Enter Custom Values"],
        horizontal=True,
        label_visibility="collapsed",  # accessibility-safe: label exists but hidden
    )

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
        <div title='Total students' style='background:#393855; color:white; padding:0.8rem; border-radius:8px; width:200px;'>
          <strong>Total Students Enrolled:</strong><br>{enrollment:,}
        </div>
        <div title='Share protected by MMR' style='background:#4b4971; color:white; padding:0.8rem; border-radius:8px; width:200px;'>
          <strong>MMR Coverage:</strong><br>{immune*100:.1f}%
        </div>
        <div title='Could still get measles' style='background:#5a5977; color:white; padding:0.8rem; border-radius:8px; width:200px;'>
          <strong>Susceptible Students:</strong><br>{int(susceptible):,}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- Core outbreak math (simple “final size” iteration) ----------
    R0 = R0_DEFAULT
    st.number_input("Initial Infected Students", min_value=1, max_value=200, value=1, step=1, key="init_cases")

    s_frac = susceptible / enrollment if enrollment else 0
    z = 0.0001
    for _ in range(60):
        z = 1 - np.exp(-R0 * z * s_frac)
    attack = float(min(max(z, 0.0), 1.0))
    total_cases = attack * susceptible

    hosp_rate, death_rate = HOSP_RATE, DEATH_RATE
    q_days, isolation_days = QUARANTINE_DAYS, ISOLATION_DAYS

    total_infected = total_cases
    hospitalized  = total_infected * hosp_rate
    deaths        = total_infected * death_rate

    total_exposed = susceptible
    not_infected  = max(total_exposed - total_infected, 0)

    isolate_missed     = total_infected * isolation_days
    quarantine_missed  = not_infected   * q_days
    total_days_missed  = isolate_missed + quarantine_missed

    # ---------- Visualization toggle ----------
    view_mode = st.radio(
        "Visualization",
        ["People view", "Epi curve"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if view_mode == "People view":
        fig_people, per_unit = people_outcomes_chart(
            enrollment=enrollment,
            immune_rate=immune,
            infected=total_infected,
            hosp_rate=hosp_rate,
            death_rate=death_rate,
            style="heads",          
            show_background=False   
        )
        st.plotly_chart(fig_people, use_container_width=True, config={"responsive": True})

        st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>What this means in people</h2>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="blocked-text">
          Each circle represents <strong>{per_unit}</strong> student{'s' if per_unit>1 else ''}. Colors show:
          <span style="color:#6aa84f;">Immune</span>,
          <span style="color:#c9c9c9;">Susceptible (not infected)</span>,
          <span style="color:#f6b26b;">Infected (no hospital stay)</span>,
          <span style="color:#e69138;">Hospitalized</span>,
          <span style="color:#cc0000;">Deaths</span>.
          Press <strong>Start Outbreak</strong> to reveal the estimated outcomes for this scenario.
        </div>
        """, unsafe_allow_html=True)

    else:
        # Smooth 90-day epi curve (gamma-like) scaled to total infections; fixed y-axis for comparability
        days = np.arange(SIM_DAYS)
        shape = (days**5) * np.exp(-days / 2)
        shape = shape / shape.sum() if shape.sum() else shape
        daily_counts = shape * total_infected

        fig_curve = epi_curve_chart(daily_counts=daily_counts, y_max=EPI_Y_MAX)
        st.plotly_chart(fig_curve, use_container_width=True, config={"responsive": True})

        st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Estimated Daily Measles Cases</h2>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="blocked-text">
          This curve shows a simple projection of new measles cases per day over 90 days after the virus enters the school.
          We cap the y-axis at <strong>{EPI_Y_MAX}</strong> so comparisons across schools are easier.
          Press <strong>Start Outbreak</strong> to animate the build-up and decline of the outbreak.
        </div>
        """, unsafe_allow_html=True)

    # ---------- School Calendar: Exclusion (Quarantine) Days ----------
    school_days, curr = [], datetime.today().date()
    while len(school_days) < 30:
        if curr.weekday() < 5:  # Mon–Fri only
            school_days.append(curr)
        curr += timedelta(days=1)
    exclusion_days = set(school_days[:q_days])

    cal_html = "<div style='max-width:680px; margin:auto;'><table style='width:100%; text-align:center; border-collapse:collapse;'><tr>"
    cal_html += ''.join(f"<th style='padding:6px;border-bottom:1px solid#ccc'>{wd}</th>" for wd in ['Mon','Tue','Wed','Thu','Fri']) + '</tr>'
    i = 0
    while i < len(school_days):
        week = '<tr>'
        wd0 = school_days[i].weekday()
        week += ''.join("<td style='padding:12px;border:1px solid #eee;background:#f7f7f7'></td>" for _ in range(wd0))
        for _wd in range(wd0, 5):
            if i >= len(school_days):
                week += "<td style='padding:12px;border:1px solid #eee;background:#f7f7f7'></td>"
            else:
                d = school_days[i]
                shaded = d in exclusion_days
                style = 'background:#2f2e41; color:white;' if shaded else 'background:#ffffff;'
                title = f"Quarantine Day {i+1}" if shaded else ''
                week += f"<td title='{title}' style='padding:12px;border:1px solid #eee; {style}'>{d.strftime('%b %d')}</td>"
                i += 1
        week += '</tr>'
        cal_html += week
    cal_html += '</table></div>'
    st.markdown(cal_html, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>School Calendar: Exclusion (Quarantine) Days</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="blocked-text">
      <strong>What the calendar shows:</strong> Confirmed measles cases stay home for <strong>{ISOLATION_DAYS} days after rash</strong>.
      Unvaccinated or not fully vaccinated exposed students are excluded for <strong>{QUARANTINE_DAYS} days</strong> after last exposure.
      Shaded dates mark the next 30 school weekdays that could be affected if an outbreak began now.
    </div>
    """, unsafe_allow_html=True)

    # ---------- Outbreak Summary ----------
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Outbreak Summary</h2>", unsafe_allow_html=True)
    colors = px.colors.sequential.Cividis
    st.markdown(f"""
    <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem; margin-bottom:1em;'>
      <div title='Total infections among susceptible students' style='background:{colors[-3]}; color:white; padding:1rem; border-radius:8px; width:190px;'>
        <strong>Total Infected</strong><br>{int(total_infected):,}
      </div>
      <div title='Hospitalizations = infections × {HOSP_RATE:.0%}' style='background:{colors[-4]}; color:white; padding:1rem; border-radius:8px; width:190px;'>
        <strong>Hospitalizations</strong><br>{int(hospitalized):,}
      </div>
      <div title='Deaths = infections × {DEATH_RATE:.3%}' style='background:{colors[-5]}; color:white; padding:1rem; border-radius:8px; width:190px;'>
        <strong>Deaths</strong><br>{int(deaths):,}
      </div>
      <div title='Exposed but not infected' style='background:{colors[-6]}; color:white; padding:1rem; border-radius:8px; width:190px;'>
        <strong>Exposed Students</strong><br>{int(not_infected):,}
      </div>
      <div title='Missed days = cases×{ISOLATION_DAYS} + exposed×{QUARANTINE_DAYS}' style='background:{colors[-7]}; color:white; padding:1rem; border-radius:8px; width:190px;'>
        <strong>Missed Days</strong><br>{int(total_days_missed):,}
      </div>
      <div title='Attack rate among susceptibles' style='background:{colors[-8]}; color:white; padding:1rem; border-radius:8px; width:190px;'>
        <strong>Attack Rate</strong><br>{attack*100:.1f}%
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- Plain-language notes (educational) ----------
    st.markdown("""
**Plain-language notes (education)**
- **Total Infected:** Estimated number of susceptible students who catch measles.
- **Hospitalizations:** About **1 in 5** infections need hospital care (model assumption).
- **Deaths:** Very rare, but possible — we use **0.03%** of infections.
- **Exposed Students:** Had contact but didn’t get sick; they still miss school during quarantine.
- **Missed Days:** Sick students miss **4 days** after rash; exposed but not sick miss **21 days**.
- **Attack Rate:** Percent of susceptible students who end up infected in this scenario.
""")

    # ---------- Educational disclaimer ----------
    st.markdown("""
    <div class="blocked-text" style="margin-top:0.5rem;">
      <strong>Educational disclaimer:</strong> This simulator is for education and planning only. It simplifies real-world
      public health dynamics and assumes no additional interventions (e.g., targeted vaccination, masking, closures).
      It also ignores holidays and behavior changes. For real-time guidance, please consult ADHS and your local health authority.
    </div>
    """, unsafe_allow_html=True)
