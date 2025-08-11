# views/tab5_az_school_risks.py
# (Python 3.9+ compatible; with “What if we raise MMR?” placed below results; sources reinstated w/ links; no exports)
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from charts import people_outcomes_chart, epi_curve_chart

# -------- Tunables --------
R0_DEFAULT       = 12          # fixed for measles (no UI control)
HOSP_RATE        = 0.20
DEATH_RATE       = 0.0003
QUARANTINE_DAYS  = 21
ISOLATION_DAYS   = 4
SIM_DAYS         = 90
EPI_Y_MAX        = 20          # cap y-axis per your request


# ----------------- Small helpers -----------------
def _final_size_attack_rate(r0, susceptible_share, iters=60):
    try:
        r0 = float(r0)
        susceptible_share = float(susceptible_share)
    except Exception:
        return 0.0
    if susceptible_share <= 0 or r0 <= 0:
        return 0.0
    z = 1e-4
    for _ in range(iters):
        z = 1 - np.exp(-r0 * z * susceptible_share)
    return float(max(0.0, min(1.0, z)))


def _build_school_days(n_days=30):
    days, curr = [], datetime.today().date()
    while len(days) < n_days:
        if curr.weekday() < 5:
            days.append(curr)
        curr += timedelta(days=1)
    return days


def _calendar_html(school_days, exclusion_days):
    header = ''.join(
        "<th style='padding:6px;border-bottom:1px solid #eee'>{}</th>".format(wd)
        for wd in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    )
    html = [
        "<div style='max-width:680px;margin:auto;'>",
        "<table style='width:100%;text-align:center;border-collapse:collapse;'>",
        "<tr>{}</tr>".format(header),
    ]
    i = 0
    while i < len(school_days):
        week = ["<tr>"]
        wd0 = school_days[i].weekday()
        week.extend("<td style='padding:12px;border:1px solid #eee;background:#f7f7f7'></td>" for _ in range(wd0))
        for _wd in range(wd0, 5):
            if i >= len(school_days):
                week.append("<td></td>")
                continue
            d = school_days[i]
            shaded = d in exclusion_days
            bg = "#2f2e41" if shaded else "#f7f7f7"
            fg = "white" if shaded else "#333"
            title = ("Quarantine day {}".format(len([x for x in exclusion_days if x <= d])) if shaded else "")
            week.append(
                "<td title='{}' style='padding:12px;border:1px solid #eee;background:{};color:{};border-radius:4px'>{}</td>".format(
                    title, bg, fg, d.strftime('%b %d')
                )
            )
            i += 1
        week.append("</tr>")
        html.append(''.join(week))
    html.append("</table></div>")
    return ''.join(html)


def render(df_schools: pd.DataFrame):
    # -------- Title & Sources cards --------
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.0em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.05rem; color:#555; margin-top:0; margin-bottom:0.5em;'>
        Estimate infections, hospitalizations, and missed school days based on enrollment and MMR coverage.<br>
        <em>Educational, simplified simulation (not real-time guidance).</em>
      </p>
      <h2 style='text-align:center; margin:0.75em 0 0.5em;'>Assumptions & Data Sources</h2>
    </div>
    <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:1rem; margin-bottom:1.25em;'>
      <div title='Typical measles estimate' style='background:#2f2e41; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>R₀:</strong><br>12
        <div style='font-size:0.9em;opacity:0.9; margin-top:0.25rem;'>
          <a href="https://pubmed.ncbi.nlm.nih.gov/28757186/" target="_blank" style="color:#a5c9ff;">PubMed</a>
        </div>
      </div>
      <div title='MMR kindergarten coverage for 2024–25 (schools ≥20 students)' style='background:#3d3c5a; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>MMR Rate:</strong><br>
        <a href="https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage" target="_blank" style="color:#a5c9ff;">ADHS 2024–25</a>
      </div>
      <div title='Teaching example rate' style='background:#47465c; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Hospitalization Rate:</strong><br>20%
        <div style='font-size:0.9em;opacity:0.9; margin-top:0.25rem;'>
          <a href="https://www.nfid.org/infectious-disease/measles/" target="_blank" style="color:#a5c9ff;">NFID</a>
        </div>
      </div>
      <div title='Teaching example rate' style='background:#4e4d6b; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Death Rate:</strong><br>0.03%
        <div style='font-size:0.9em;opacity:0.9; margin-top:0.25rem;'>
          <a href="https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease" target="_blank" style="color:#a5c9ff;">UChicago Medicine</a>
        </div>
      </div>
      <div title='Isolation = 4 days after rash onset' style='background:#5A4E7A; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Isolation:</strong><br>4 days
        <div style='font-size:0.9em;opacity:0.9; margin-top:0.25rem;'>
          <a href="https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/investigation-manual/communicable/measles-protocol.pdf" target="_blank" style="color:#a5c9ff;">AZ Protocol</a>
        </div>
      </div>
      <div title='Exclusion for un/under-vaccinated exposures' style='background:#6d6b85; color:white; padding:1rem; border-radius:10px; width:200px; cursor:help;'>
        <strong>Quarantine:</strong><br>21 days
        <div style='font-size:0.9em;opacity:0.9; margin-top:0.25rem;'>
          <a href="https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/investigation-manual/communicable/mmr-guidance.pdf" target="_blank" style="color:#a5c9ff;">ADHS Guidance</a>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # -------- Scenario selection --------
    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        mode = st.radio("Simulation mode", ["Select a School", "Enter Custom Values"], horizontal=True)
    with c2:
        st.metric("Measles contagiousness (R₀)", f"{R0_DEFAULT} (fixed)")
        st.caption("R₀ is fixed for measles here to keep this an apples-to-apples teaching demo.")

    if mode == "Select a School":
        sel = st.selectbox(
            "School",
            df_schools["SCHOOL NAME"].sort_values(),
            index=0,
            help="Pick a school to auto-fill enrollment and MMR coverage.",
        )
        row = df_schools.loc[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment = int(row.get("ENROLLED", 0) or 0)
        immune = float(row.get("IMMUNE_MMR", 0) or 0)
    else:
        colA, colB = st.columns(2)
        with colA:
            enrollment = st.number_input(
                "Total Students", min_value=1, max_value=5000, value=500, step=10,
                help="How many students are in the school?",
            )
        with colB:
            immune = st.slider(
                "MMR Immunization Rate", min_value=0.0, max_value=1.0, value=0.85, step=0.01,
                help="Share of students already protected by MMR (0.00 to 1.00).",
            )

    susceptible = max(0, enrollment * (1 - immune))

    # -------- Core math --------
    s_share = (susceptible / enrollment) if enrollment else 0.0
    attack_over_sus = _final_size_attack_rate(R0_DEFAULT, s_share)
    total_infected = attack_over_sus * susceptible
    hospitalized = total_infected * HOSP_RATE
    deaths = total_infected * DEATH_RATE
    exposed_not_inf = max(susceptible - total_infected, 0)
    missed_days = total_infected * ISOLATION_DAYS + exposed_not_inf * QUARANTINE_DAYS

    # -------- Results at a glance --------
    st.markdown("## Results at a glance")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total infected", f"{int(round(total_infected)):,}")
    m2.metric("Hospitalizations (assumed 20%)", f"{int(round(hospitalized)):,}")
    m3.metric("Deaths (assumed 0.03%)", f"{int(round(deaths)):,}")
    m4.metric("Exposed not infected", f"{int(round(exposed_not_inf)):,}")
    m5.metric("Missed school days", f"{int(round(missed_days)):,}")
    st.caption("‘Assumed’ rates are educational placeholders and can change by context. See ‘Assumptions & notes’ below.")

    # --- What if we raise MMR? ---
    st.markdown("---")
    st.markdown("### What if we raise MMR?")
    inc = st.slider(
        "Increase coverage by (percentage points)", 0, 20, 5, 1,
        help="Try 0–20 points. For example, if current MMR is 80% and you add 5 points, it becomes 85%.",
    )
    immune_plus = min(1.0, immune + inc / 100.0)
    susceptible_plus = enrollment * (1 - immune_plus)

    attack_over_sus_plus = _final_size_attack_rate(R0_DEFAULT, (susceptible_plus / enrollment) if enrollment else 0.0)
    total_infected_plus = attack_over_sus_plus * susceptible_plus
    hospitalized_plus = total_infected_plus * HOSP_RATE
    deaths_plus = total_infected_plus * DEATH_RATE
    exposed_not_inf_plus = max(susceptible_plus - total_infected_plus, 0)
    missed_days_plus = total_infected_plus * ISOLATION_DAYS + exposed_not_inf_plus * QUARANTINE_DAYS

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total infected", f"{int(round(total_infected_plus)):,}",
              delta=int(round(total_infected_plus - total_infected)), delta_color="inverse")
    c2.metric("Hospitalizations", f"{int(round(hospitalized_plus)):,}",
              delta=int(round(hospitalized_plus - hospitalized)), delta_color="inverse")
    c3.metric("Deaths", f"{int(round(deaths_plus)):,}",
              delta=int(round(deaths_plus - deaths)), delta_color="inverse")
    c4.metric("Exposed not infected", f"{int(round(exposed_not_inf_plus)):,}",
              delta=int(round(exposed_not_inf_plus - exposed_not_inf)))
    c5.metric("Missed school days", f"{int(round(missed_days_plus)):,}",
              delta=int(round(missed_days_plus - missed_days)), delta_color="inverse")
    st.caption("Green deltas = fewer infections or days missed after raising MMR.")

    # -------- Visuals --------
    st.markdown("---")
    st.markdown("## Visualize the outbreak")

    view = st.radio("View", ["People view", "Epi curve"], horizontal=True, label_visibility="collapsed")
    if view == "People view":
        fig_people, _ = people_outcomes_chart(
            enrollment=enrollment,
            immune_rate=immune,
            infected=total_infected,
            hosp_rate=HOSP_RATE,
            death_rate=DEATH_RATE,
        )
        st.plotly_chart(fig_people, use_container_width=True)
    else:
        x = np.arange(1, SIM_DAYS + 1)
        k = 10.0
        theta = SIM_DAYS / (k * 2.5)
        y = (x ** (k - 1) * np.exp(-x / theta))
        y = y / y.sum() * (total_infected or 0)
        fig_curve = epi_curve_chart(daily_counts=y, y_max=EPI_Y_MAX)
        st.plotly_chart(fig_curve, use_container_width=True)

    # -------- Calendar --------
    st.markdown("---")
    st.markdown("## Calendar: exclusion (quarantine) days")
    school_days = _build_school_days(30)
    exclusion_days = set(school_days[:QUARANTINE_DAYS])
    st.markdown(_calendar_html(school_days, exclusion_days), unsafe_allow_html=True)

    # -------- Assumptions & notes --------
    with st.expander("Assumptions & notes", expanded=False):
        st.markdown("""
        - **R₀:** 12, per [PubMed](https://pubmed.ncbi.nlm.nih.gov/28757186/)
        - **MMR coverage:** Data from [ADHS](https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage)
        - **Hospitalizations:** 20% per [NFID](https://www.nfid.org/infectious-disease/measles/)
        - **Deaths:** 0.03% per [UChicago Medicine](https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease)
        - **Isolation:** 4 days after rash ([AZ Protocol](https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/investigation-manual/communicable/measles-protocol.pdf))
        - **Quarantine:** 21 days ([ADHS Guidance](https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/investigation-manual/communicable/mmr-guidance.pdf))
        """)
        st.info("For real-world guidance, consult ADHS and your local health authority.")


def tab5_view(df_schools: pd.DataFrame):
    render(df_schools)


def tab5_view(df_schools: pd.DataFrame):
    render(df_schools)
