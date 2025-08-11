import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Tunables (easy to adjust in one place)
R0_DEFAULT = 12
HOSP_RATE = 0.20
DEATH_RATE = 0.0003
QUARANTINE_DAYS = 21
ISOLATION_DAYS = 4
SIM_DAYS = 90

EPICURVE_Y_MAX = 50

def _plain_language_assumptions():
    st.markdown("""
**How to read these settings (plain language):**

- **R₀ (how contagious measles is):** higher R₀ → one sick person can infect more people. We use 12, a commonly cited estimate.
- **MMR immunization rate:** the share of students protected by the vaccine. Lower protection → more students at risk.
- **Hospitalization rate:** we assume ~20% of infections need hospital care.
- **Death rate:** we use ~0.03% as a rare but real risk.
- **Isolation:** students who get sick are out of school for **4 days after rash** starts.
- **Quarantine:** unvaccinated exposed students stay home for **21 days** after last exposure.
- **The curve shape:** we model a typical outbreak curve that rises, peaks, and falls as fewer students remain susceptible.
""")

def _gamma_like_distribution(days):
    # A simple unimodal distribution for daily cases timing
    dist = (days**5) * np.exp(-days / 2)
    dist_sum = dist.sum()
    return dist / dist_sum if dist_sum > 0 else dist

def _animated_epicurve(days, daily, y_max=EPICURVE_Y_MAX):
    # Build an animation that "reveals" the bars over time
    # Frame d shows bars up to day d (others set to 0)
    base_y = np.where(days <= 0, daily, 0)

    frames = []
    for d in range(len(days)):
        y_frame = np.where(days <= d, daily, 0)
        frames.append(go.Frame(
            data=[go.Bar(x=days, y=y_frame)],
            name=str(d)
        ))

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
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.02, y=1.12, xanchor="left", yanchor="top",
            buttons=[
                dict(label="▶ Play", method="animate", args=[None, {"frame": {"duration": 80, "redraw": True}, "fromcurrent": True, "transition": {"duration": 0}}]),
                dict(label="⏸ Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
            ],
        )],
        sliders=[dict(
            active=0,
            y=1.05,
            x=0.12,
            currentvalue=dict(prefix="Day ", visible=True, xanchor="right"),
            steps=[dict(method="animate", label=str(d), args=[[str(d)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}]) for d in range(len(days))]
        )]
    )
    return fig

def tab5_view(df_schools):
    # --- Header & Assumptions ---
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

    # Quick, plain-language helper block
    with st.expander("What do these assumptions mean? (plain language)", expanded=False):
        _plain_language_assumptions()

    # --- Simulation Mode & School Details ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)

    # Accessibility fix: provide a non-empty label and hide it visually
    mode = st.radio(
        "Simulation mode",
        ["Select a School", "Enter Custom Values"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if mode == "Select a School":
        sel = st.selectbox("School", df_schools["SCHOOL NAME"].sort_values(), index=0)
        data = df_schools[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment = int(data["ENROLLED"])
        immune = float(data["IMMUNE_MMR"])
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
    initial = st.number_input("Initial Infected Students", min_value=1, max_value=200, value=1, step=1)

    # Final size (attack rate) under simple homogeneous mixing (illustrative)
    # Fixed-point iteration on z (fraction infected among susceptibles)
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

    # --- Estimated Daily Measles Cases (animated epi-curve) ---
    days = np.arange(0, SIM_DAYS)
    dist = _gamma_like_distribution(days)
    daily = dist * total_cases

    fig = _animated_epicurve(days, daily, y_max=EPICURVE_Y_MAX)
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Estimated Daily Measles Cases</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="blocked-text">
      This animated chart shows the outbreak over {SIM_DAYS} days after measles is introduced into the school.
      The bars represent estimated new cases each day. The **y-axis is fixed** (max = {EPICURVE_Y_MAX} students/day) so changes come from the scenario, not the scale.
      Press **Play** to watch the outbreak grow and fade, or drag the slider to a specific day.
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
    summary_html = f"""
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
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    # --- Disclaimer ---
    st.markdown("""
    <div class="blocked-text">
      <strong>Disclaimer:</strong> This tool simplifies complex public health dynamics and assumes no extra interventions (like targeted vaccination, masking, or school closures). It also ignores holidays and behavior changes. Use for illustration and planning only; consult ADHS for real-time guidance and requirements.
    </div>
    """, unsafe_allow_html=True)

