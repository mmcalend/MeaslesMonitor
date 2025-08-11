## views/tab5_az_school_risks.py
"""
Arizona School Risks — simplified, plain-language Tab 5

Flow:
  1) Choose scenario
  2) Results at a glance
  3) Visualize (People view or Epi curve)
  4) Calendar
  5) Assumptions & notes

Kept your color/font scheme, calendar, and avoided emojis.
"""
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from charts import people_outcomes_chart, epi_curve_chart

# -------- Tunables --------
R0_DEFAULT       = 12
HOSP_RATE        = 0.20
DEATH_RATE       = 0.0003
QUARANTINE_DAYS  = 21
ISOLATION_DAYS   = 4
SIM_DAYS         = 90
EPI_Y_MAX        = 100


# ----------------- Small helpers -----------------
def _final_size_attack_rate(r0: float, susceptible_share: float, iters: int = 60) -> float:
    """Approximate final attack rate using fixed-point iteration of the SIR final-size relation.
    Returns a fraction between 0 and 1 over susceptibles."""
    if susceptible_share <= 0 or r0 <= 0:
        return 0.0
    z = 1e-4
    for _ in range(iters):
        z = 1 - np.exp(-r0 * z * susceptible_share)
    return float(max(0.0, min(1.0, z)))


def _build_school_days(n_days: int = 30):
    """Return next n school *weekdays* (Mon–Fri) starting today."""
    days, curr = [], datetime.today().date()
    while len(days) < n_days:
        if curr.weekday() < 5:
            days.append(curr)
        curr += timedelta(days=1)
    return days


def _calendar_html(school_days, exclusion_days: set):
    # We keep the calendar HTML to preserve your look.
    header = ''.join(
        f"<th style='padding:6px;border-bottom:1px solid #eee'>{wd}</th>"
        for wd in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    )
    html = [
        "<div style='max-width:680px;margin:auto;'>",
        "<table style='width:100%;text-align:center;border-collapse:collapse;'>",
        f"<tr>{header}</tr>",
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
            bg = "#6A4C93" if shaded else "#f7f7f7"
            fg = "white" if shaded else "#333"
            week.append(
                f"<td style='padding:12px;border:1px solid #eee;background:{bg};"
                f"color:{fg};border-radius:4px'>{d.strftime('%b %d')}</td>"
            )
            i += 1
        week.append("</tr>")
        html.append(''.join(week))
    html.append("</table></div>")
    return ''.join(html)


def render(df_schools: pd.DataFrame):
    # -------- Title --------
    st.markdown(
        """
        <div style='text-align:center'>
          <h1 style='margin-bottom:0.5rem'>Arizona School Risks</h1>
          <p style='margin:0'>Estimate infections, hospitalizations, and missed school days based on enrollment and MMR coverage.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------- Scenario selection --------
    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        mode = st.radio("Simulation mode", ["Select a School", "Enter Custom Values"], horizontal=True)
    with c2:
        R0 = st.slider(
            "How contagious is measles (R₀)?", 5, 20, R0_DEFAULT,
            help="Higher means each infected student infects more people if others are susceptible."
        )

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

    # --- What if we raise MMR coverage? ---
    st.markdown("---")
    st.markdown("### What if we raise MMR?")
    inc = st.slider(
        "Increase coverage by (percentage points)", 0, 20, 5, 1,
        help="Try 0–20 points. For example, if current MMR is 80% and you add 5 points, it becomes 85%.",
    )
    immune_plus = min(1.0, immune + inc / 100.0)
    susceptible_plus = enrollment * (1 - immune_plus)

    # -------- Core math --------
    s_share = susceptible / enrollment if enrollment else 0.0
    attack_over_sus = _final_size_attack_rate(R0, s_share)
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

    # --- What-if metrics (with increased MMR) ---
    attack_over_sus_plus = _final_size_attack_rate(R0, (susceptible_plus / enrollment) if enrollment else 0.0)
    total_infected_plus = attack_over_sus_plus * susceptible_plus
    hospitalized_plus = total_infected_plus * HOSP_RATE
    deaths_plus = total_infected_plus * DEATH_RATE
    exposed_not_inf_plus = max(susceptible_plus - total_infected_plus, 0)
    missed_days_plus = total_infected_plus * ISOLATION_DAYS + exposed_not_inf_plus * QUARANTINE_DAYS

    st.markdown(f"#### If MMR increases by **{inc}** points")
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

    # -------- Visualize the outbreak --------
    st.markdown("---")
    st.markdown("## Visualize the outbreak")

    view = st.radio("View", ["People view", "Epi curve"], horizontal=True, label_visibility="collapsed")
    if view == "People view":
        fig_people, per_unit = people_outcomes_chart(
            enrollment=enrollment,
            immune_rate=immune,
            infected=total_infected,
            hosp_rate=HOSP_RATE,
            death_rate=DEATH_RATE,
            per_unit=None,
            style="heads",            # circles only
            show_background=True,
        )
        st.plotly_chart(fig_people, use_container_width=True)
        st.caption("Each circle represents a fixed number of students so you can compare groups fairly across schools.")
    else:
        # Make a simple 90-day bell-shaped incidence curve scaled to total infections
        x = np.arange(1, SIM_DAYS + 1)
        k = 10.0
        theta = SIM_DAYS / (k * 2.5)
        y = (x ** (k - 1) * np.exp(-x / theta))
        y = y / y.sum() * (total_infected or 0)
        fig_curve = epi_curve_chart(daily_counts=y, y_max=EPI_Y_MAX)
        st.plotly_chart(fig_curve, use_container_width=True)
        with st.expander("What am I looking at?", expanded=False):
            st.markdown("This is a simple projection of *new* measles cases per day over time. We cap the y-axis so it’s easy to compare across schools.")

    # -------- Calendar of exclusions --------
    st.markdown("---")
    st.markdown("## Calendar: exclusion (quarantine) days")
    school_days = _build_school_days(30)
    exclusion_days = set(school_days[:QUARANTINE_DAYS])
    st.markdown(_calendar_html(school_days, exclusion_days), unsafe_allow_html=True)
    st.caption("Shaded dates mark upcoming school weekdays where exposed students may need to stay home if an exposure happened today.")

    # -------- Assumptions & notes --------
    with st.expander("Assumptions & notes", expanded=False):
        st.markdown(
            """
            - **R₀ (contagiousness):** We use **12** as a typical measles value. Lower or higher changes how fast it spreads.
            - **MMR coverage:** Share of students already protected. Lower coverage → more students at risk.
            - **Hospitalizations:** We show **20%** of infections as a teaching example.
            - **Deaths:** We show **0.03%** of infections; actual risk varies by age and health.
            - **Isolation vs. quarantine:** Sick students miss **4 days** after rash; exposed but not sick miss **21 days**.
            - **Attack rate:** Percent of susceptible students who end up infected under these assumptions.
            - **Limitations:** Simplified education tool. No special interventions modeled; weekends/holidays not applied.
            """
        )
        st.info("For real-world guidance, consult ADHS and your local health authority.")


def tab5_view(df_schools: pd.DataFrame):
    render(df_schools)
