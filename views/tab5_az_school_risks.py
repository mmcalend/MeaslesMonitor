import streamlit as st 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Tunables / constants ---
R0_FIXED = 12.0
HOSP_RATE_DEFAULT = 0.20
DEATH_RATE_DEFAULT = 0.0003
QUARANTINE_DAYS_DEFAULT = 21
SIM_DAYS = 90
EPI_Y_MAX = 20  # <-- fixed y-axis max for the epi curve

# --- Helper: final attack rate on susceptibles via fixed-point iteration ---
def _final_attack_share_on_susceptibles(r0: float, susceptible_share: float, iters: int = 60) -> float:
    """Return share of susceptibles infected (0..1)."""
    if r0 <= 0 or susceptible_share <= 0:
        return 0.0
    z = 1e-4
    for _ in range(iters):
        z = 1 - np.exp(-r0 * z * susceptible_share)
    return float(np.clip(z, 0.0, 1.0))

# --- Helper: stylized summary tile ---
def _metric_tile(label: str, value: str, bg: str):
    return f"""
    <div style='background:{bg}; color:white; padding:1rem; border-radius:10px; width:190px;'>
      <div style='font-weight:600; margin-bottom:0.25rem;'>{label}</div>
      <div style='font-size:1.25rem;'>{value}</div>
    </div>
    """

def tab5_view(df_schools: pd.DataFrame):
    colors = px.colors.sequential.Cividis
    # ---------------------------------------------------------------------
    # 1) Title & short intro
    # ---------------------------------------------------------------------
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.2em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.05rem; color:#555; margin:0;'>
        Educational model to illustrate how measles can spread in a school and how vaccination changes the outcome.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # 2) Assumptions (with expandable explanations)
    # ---------------------------------------------------------------------
    st.markdown("### Assumptions & Data Sources")
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"**R₀ (Basic Reproduction Number):** {R0_FIXED:.0f}  \nSource: [PubMed](https://pubmed.ncbi.nlm.nih.gov/28757186/)")
        with st.expander("Learn more about R₀"):
            st.write(
                "R₀ is the average number of people one infected person will infect in a fully susceptible population. "
                "Measles has one of the highest R₀ values (~12), so it spreads quickly when vaccination rates are low."
            )
    with cols[1]:
        st.markdown(f"**Hospitalization rate:** {int(HOSP_RATE_DEFAULT*100)}%  \nSource: [NFID](https://www.nfid.org/infectious-disease/measles/)")
        with st.expander("Why this matters"):
            st.write(
                "Hospitalizations reflect severe illness and healthcare burden. We estimate 20% of infections may require hospital care."
            )
    with cols[2]:
        st.markdown(f"**Death rate:** {DEATH_RATE_DEFAULT*100:.02f}%  \nSource: [UChicago Medicine](https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease)")
        with st.expander("Why this matters"):
            st.write(
                "Deaths are rare in high-income settings but can occur. Even low probabilities matter when many people get infected."
            ))

    cols2 = st.columns(2)
    with cols2[0]:
        st.markdown(f"**Isolation (cases):** 4 days after rash onset  \nSource: ADHS protocol")
        with st.expander("What is isolation?"):
            st.write(
                "People with measles should stay home to avoid spreading infection. Isolation typically lasts through 4 days after rash onset."
            )
    with cols2[1]:
        st.markdown(f"**Quarantine (exposed, un/undervaccinated):** {QUARANTINE_DAYS_DEFAULT} days  \nSource: ADHS")
        with st.expander("What is quarantine?"):
            st.write(
                "Close contacts who are unvaccinated or under-vaccinated stay home for 21 days (one incubation period) after the last exposure."
            )

    st.markdown("---")

    # ---------------------------------------------------------------------
    # 3) School / custom selection
    # ---------------------------------------------------------------------
    st.markdown("### Choose Simulation Mode")
    mode = st.radio("", ["Select a School", "Enter Custom Values"], horizontal=True)

    if mode == "Select a School":
        sel = st.selectbox("School:", df_schools["SCHOOL NAME"].sort_values())
        row = df_schools.loc[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment = int(row["ENROLLED"])
        immune = float(row["IMMUNE_MMR"])  # 0..1
    else:
        enrollment = st.number_input("Total Students", min_value=1, max_value=5000, value=500, step=10, help="School size used in the simulation.")
        immune = st.slider("MMR Immunization Rate", 0.0, 1.0, 0.85, 0.01, help="Share of students fully protected by MMR (0–1).")

    susceptible = max(0, int(round(enrollment * (1.0 - immune))))
    st.markdown(f"""
    <div style='text-align:center; margin: 0.75rem 0 0.25rem;'>
      <h3 style='margin:0;'>School Details</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:0.75rem; margin-bottom:0.75rem;'>
            {_metric_tile("Enrollment", f"{enrollment:,}", colors[-3])}
            {_metric_tile("MMR (immune)", f"{immune*100:.1f}%", colors[-4])}
            {_metric_tile("Susceptible", f"{susceptible:,}", colors[-5])}
        </div>
        """,
        unsafe_allow_html=True
    )
    with st.expander("How do we calculate 'susceptible'?"):
        st.write(
            "Susceptible = Enrollment × (1 − MMR immune rate). "
            "This assumes vaccine-induced immunity is high and natural immunity is uncommon in this population."
        )

    # ---------------------------------------------------------------------
    # 4) Core simulation (R₀ fixed)
    # ---------------------------------------------------------------------
    initial_infected = st.number_input("Initial infected students", 1, 50, 1, help="Seed cases at Day 0. Used to shape the early curve, not the final size formula.")
    s_frac = (susceptible / enrollment) if enrollment > 0 else 0.0
    share_of_susceptibles_infected = _final_attack_share_on_susceptibles(R0_FIXED, s_frac)
    attack_rate_total = share_of_susceptibles_infected * s_frac  # share of the whole school infected
    total_cases = int(round(enrollment * attack_rate_total))
    total_cases = max(total_cases, 0)

    hosp_rate = HOSP_RATE_DEFAULT
    death_rate = DEATH_RATE_DEFAULT
    q_days = QUARANTINE_DAYS_DEFAULT

    hospitalizations = int(round(total_cases * hosp_rate))
    deaths = int(round(total_cases * death_rate))
    total_exposed = susceptible  # simplified: all susceptibles are exposed
    total_days_missed = int(round(total_exposed * q_days))

    # ---------------------------------------------------------------------
    # 5) Outbreak summary + interpretive expanders
    # ---------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Outbreak Summary")
    st.markdown(
        f"""
        <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:0.75rem; margin-bottom:0.5rem;'>
            {_metric_tile("Total Infected", f"{total_cases:,}", colors[-3])}
            {_metric_tile("Hospitalizations", f"{hospitalizations:,}", colors[-4])}
            {_metric_tile("Deaths", f"{deaths:,}", colors[-5])}
            {_metric_tile("Exposed (susceptible)", f"{total_exposed:,}", colors[-6])}
            {_metric_tile("Missed Days (total)", f"{total_days_missed:,}", colors[-7])}
            {_metric_tile("Attack Rate", f"{attack_rate_total*100:.1f}%", colors[-8])}
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("How to interpret these results"):
        st.write(
            "- **Total infected**: estimated number of students who become ill during the outbreak.\n"
            "- **Hospitalizations**: severe cases requiring hospital care (assumed 20%).\n"
            "- **Deaths**: rare, but possible (assumed 0.03%).\n"
            "- **Exposed**: students without immunity who could be quarantined if exposed.\n"
            "- **Missed days**: instruction days lost from quarantine (exposed × 21 days).\n"
            "- **Attack rate**: fraction of the entire school infected."
        )

    with st.expander("Model limitations"):
        st.write(
            "This simplified model assumes a constant R₀, no targeted interventions, and high vaccine effectiveness. "
            "It does not account for weekends/holidays beyond the calendar display, heterogeneous mixing, or behavior changes."
        )

    # ---------------------------------------------------------------------
    # 6) Daily cases curve (fixed y-axis at 20)
    # ---------------------------------------------------------------------
    days = np.arange(0, SIM_DAYS)
    # A simple unimodal curve shape (gamma-like) anchored by total_cases
    # We also nudge the first few days using 'initial_infected' to make early growth visible.
    dist = (days**5) * np.exp(-days / 2.0)
    dist[0] = max(dist[0], 1e-6 + initial_infected)  # gentle seed at day 0
    dist = dist / dist.sum() if dist.sum() > 0 else dist
    daily = dist * total_cases

    fig = go.Figure([
        go.Bar(
            x=days,
            y=daily,
            marker_color=colors[-2],
            hovertemplate='Day %{x}<br>Cases %{y:.0f}<extra></extra>'
        )
    ])
    fig.update_layout(
        xaxis=dict(title="Days since introduction", showgrid=False),
        yaxis=dict(title="Daily new cases (students)", showgrid=False, range=[0, EPI_Y_MAX]),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("What this curve means"):
        st.write(
            "The outbreak starts slowly, rises to a peak when many susceptibles are exposed, then declines as fewer susceptibles remain. "
            "Public health actions (exclusion, vaccination, event changes) can flatten or shorten this curve."
        )

    # ---------------------------------------------------------------------
    # 7) School calendar: exclusion (quarantine) days
    # ---------------------------------------------------------------------
    st.markdown("### School Calendar: Exclusion (Quarantine) Days")
    school_days, curr = [], datetime.today().date()
    # Next 30 weekdays
    while len(school_days) < 30:
        if curr.weekday() < 5:
            school_days.append(curr)
        curr += timedelta(days=1)

    exclusion_days = set(school_days[:q_days])  # first 21 school days shaded

    cal_html = "<div style='max-width:760px; margin:auto;'><table style='width:100%; text-align:center; border-collapse:collapse;'><tr>"
    cal_html += ''.join(
        f"<th style='padding:6px;border-bottom:1px solid #ccc'>{wd}</th>" for wd in ['Mon','Tue','Wed','Thu','Fri']
    ) + '</tr>'
    i = 0
    while i < len(school_days):
        week = '<tr>'
        wd0 = school_days[i].weekday()
        week += ''.join("<td style='padding:12px;border:1px solid #eee;background:#f7f7f7'></td>" for _ in range(wd0))
        for wd in range(wd0, 5):
            if i >= len(school_days):
                week += "<td style='padding:12px;border:1px solid #eee;background:#f7f7f7'></td>"
            else:
                d = school_days[i]
                style = 'background:#2f2e41; color:white;' if d in exclusion_days else 'background:#ffffff;'
                title = f"Quarantine Day {i+1}" if d in exclusion_days else ''
                week += f"<td title='{title}' style='padding:12px;border:1px solid #eee; {style}'>{d.strftime('%b %d')}</td>"
                i += 1
        week += '</tr>'
        cal_html += week
    cal_html += '</table></div>'
    st.markdown(cal_html, unsafe_allow_html=True)
    with st.expander("Why these days are shaded"):
        st.write(
            "Unvaccinated or under-vaccinated exposed students are excluded for 21 school days after last exposure. "
            "This display shows the next 30 weekdays, shading the quarantine window."
        )

    # ---------------------------------------------------------------------
    # 8) What if we vaccinate more? 
    # ---------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### What if we vaccinate more?")
    st.write("Adjust MMR coverage to see how outcomes change. Higher coverage reduces susceptibles and shrinks the outbreak.")

    mmr_counterfactual = st.slider("Counterfactual MMR (what-if)", 0.0, 1.0, min(0.95, max(immune, 0.90)), 0.01)
    susceptible_cf = max(0, int(round(enrollment * (1.0 - mmr_counterfactual))))
    s_frac_cf = (susceptible_cf / enrollment) if enrollment > 0 else 0.0
    share_on_susc_cf = _final_attack_share_on_susceptibles(R0_FIXED, s_frac_cf)
    attack_rate_total_cf = share_on_susc_cf * s_frac_cf
    total_cases_cf = int(round(enrollment * attack_rate_total_cf))
    hospitalizations_cf = int(round(total_cases_cf * hosp_rate))
    deaths_cf = int(round(total_cases_cf * death_rate))

    # Comparison tiles
    st.markdown(
        f"""
        <div style='display:flex; flex-wrap:wrap; justify-content:center; gap:0.75rem; margin-top:0.5rem;'>
            {_metric_tile("MMR now", f"{immune*100:.1f}%", colors[-4])}
            {_metric_tile("MMR (what-if)", f"{mmr_counterfactual*100:.1f}%", colors[-5])}
            {_metric_tile("Cases (now)", f"{total_cases:,}", colors[-6])}
            {_metric_tile("Cases (what-if)", f"{total_cases_cf:,}", colors[-7])}
            {_metric_tile("Hospitalizations (now)", f"{hospitalizations:,}", colors[-6])}
            {_metric_tile("Hospitalizations (what-if)", f"{hospitalizations_cf:,}", colors[-7])}
            {_metric_tile("Deaths (now)", f"{deaths:,}", colors[-6])}
            {_metric_tile("Deaths (what-if)", f"{deaths_cf:,}", colors[-7])}
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("How to interpret the 'what-if' comparison"):
        st.write(
            "Raising MMR coverage reduces the susceptible pool. With fewer people left to infect, the outbreak is smaller, "
            "hospitalizations and deaths drop, and the epi curve flattens. This tool shows magnitudes, not precise predictions."
        )

    # ---------------------------------------------------------------------
    # 9) Disclaimer
    # ---------------------------------------------------------------------
    st.markdown("""
    <div style='margin-top:0.75rem;'>
      <strong>Disclaimer:</strong> This is a simplified educational model using fixed parameters and homogenous mixing. 
      Real-world outbreaks vary with behavior, public health responses, and setting-specific factors. Consult ADHS for current guidance.
    </div>
    """, unsafe_allow_html=True)
