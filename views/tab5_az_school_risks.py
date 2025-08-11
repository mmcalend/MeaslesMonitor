import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# NEW: use your custom expander
from helpers import custom_expander

def tab5_view(df_schools):
    # --- Header ---
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.05rem; margin-top:0; margin-bottom:0.5em;'>
        Estimate the impact of measles on school communities, including infections, hospitalizations, absences, and more.<br>
        <em>Note: Schools with fewer than 20 kindergarten students are excluded from the selection list.</em>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Educational context section (custom dropdown) ---
    custom_expander(
        "Understanding Disease Transmission (Click to Learn More)",
        """
**Why is measles so contagious?**

Measles is one of the most contagious diseases known to humans. When an infected person coughs or sneezes, they release tiny droplets containing the virus that can remain in the air for up to 2 hours. If you're not immune and walk into a room where an infected person was, you have a 90% chance of getting sick!

**Key Concepts:**
- **R₀ (Basic Reproduction Number)**: The average number of people one infected person will infect  
- **Herd Immunity**: When enough people are vaccinated to protect the whole community  
- **Attack Rate**: The percentage of susceptible people who get infected during an outbreak  
- **Quarantine vs Isolation**: Isolation separates sick people; quarantine separates those who might be sick
        """,
        open=False
    )

    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Scientific Assumptions & Data Sources</h2>", unsafe_allow_html=True)

    # --- Assumptions list (plain text + custom dropdowns) ---
    assumptions_data = [
        {
            "title": "R₀: 12",
            "link": "https://pubmed.ncbi.nlm.nih.gov/28757186/",
            "link_text": "PubMed",
            "explanation": "R₀ (R-naught) is the basic reproduction number — how many people one infected person will infect on average in a fully susceptible population. Measles has an R₀ of ~12. For comparison: COVID-19 original strain ≈ 2–3, seasonal flu ≈ 1.3."
        },
        {
            "title": "MMR Rate: ADHS 2024–25",
            "link": "https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage",
            "link_text": "ADHS",
            "explanation": "MMR vaccination rate for kindergarten students in Arizona. Two doses are ~97% effective; coverage is reported annually by schools."
        },
        {
            "title": "Hospitalization Rate: 20%",
            "link": "https://www.nfid.org/infectious-disease/measles/",
            "link_text": "NFID",
            "explanation": "About 1 in 5 people with measles need hospital care. Complications include pneumonia, encephalitis, and severe diarrhea."
        },
        {
            "title": "Death Rate: 0.03%",
            "link": "https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease",
            "link_text": "UChicago",
            "explanation": "Fatal outcomes are rare but possible, often due to complications like pneumonia or encephalitis. Risk is higher in <5 and >20 years."
        },
        {
            "title": "Isolation: 4 days",
            "link": "https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/infectious-disease-epidemiology/school-childcare/measles-protocol.pdf",
            "link_text": "Protocol",
            "explanation": "Stay home from 4 days before rash onset through 4 days after rash onset (most contagious window)."
        },
        {
            "title": "Quarantine: 21 days",
            "link": "https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/infectious-disease-epidemiology/school-childcare/mmr-guidance.pdf",
            "link_text": "ADHS",
            "explanation": "Unvaccinated exposed individuals are excluded for 21 days after last exposure given measles’ incubation period."
        }
    ]

    for a in assumptions_data:
        st.markdown(f"- **{a['title']}** — [{a['link_text']}]({a['link']})")
        custom_expander("What does this mean?", a["explanation"])

    # --- Simulation Mode & School Details ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)

    mode = st.radio("", ["Select a School", "Enter Custom Values"], horizontal=True)

    if mode == "Select a School":
        sel = st.selectbox("School:", df_schools["SCHOOL NAME"].sort_values())
        data = df_schools[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment = int(data["ENROLLED"])
        immune = float(data["IMMUNE_MMR"])
    else:
        enrollment = st.number_input("Total Students", 1, 1000, 500)
        immune = st.slider("MMR Immunization Rate", 0.0, 1.0, 0.85, help="Drag to see how vaccination rates affect outbreak size")

    susceptible = enrollment * (1 - immune)

    # Neutral metrics (no backgrounds)
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>School Details</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Students", f"{enrollment:,}")
    c2.metric("MMR Coverage", f"{immune*100:.1f}%")
    c3.metric("Susceptible Students", f"{int(susceptible):,}")

    # Explanations via custom dropdowns (no backgrounds)
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        custom_expander("What does this mean?",
                        "Total kindergarten students enrolled at the school. Kindergarten is used because coverage is recently verified and contact rates are high.")
    with cc2:
        status = "Above herd immunity threshold" if immune >= 0.917 else "Below herd immunity threshold"
        custom_expander("💉 What does this mean?",
                        f"This is the share immune to measles (usually via vaccination). **Current status:** {status}.")
    with cc3:
        risk = "Low risk" if susceptible < enrollment * 0.1 else ("Moderate risk" if susceptible < enrollment * 0.2 else "High risk")
        custom_expander("🎯 What does this mean?",
                        f"Students who could get measles if exposed = Total × (1 − vaccination). **Risk level:** {risk}.")

    # Simple inline note (no background box)
    if immune < 0.917:
        st.markdown("**Heads up:** Vaccination is below the ~91.7% herd immunity threshold; the community is vulnerable to spread.")
    else:
        st.markdown("**Good news:** Coverage is above the ~91.7% herd immunity threshold; large outbreaks are less likely.")

    # --- Simulation Calculations ---
    R0 = 12
    initial = st.number_input("Initial Infected Students", 1, 50, 1,
                              help="How many students are infected when measles is first introduced to the school?")

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

    # --- Daily Cases Chart (unchanged, chart background remains transparent) ---
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Estimated Daily Measles Cases</h2>", unsafe_allow_html=True)

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
            hovertemplate='Day %{x}<br>Cases: %{y:.1f}<br>Cumulative: %{customdata:.0f}<extra></extra>',
            customdata=np.cumsum(daily)
        )
    ])
    fig.update_layout(
        xaxis=dict(title="Days since Introduction", showgrid=False),
        yaxis=dict(title="Daily New Cases (students)", showgrid=False, range=[0, 20]),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    st.markdown("""
This bar chart shows the projected number of new measles cases per school day over 90 days after introduction.
The curve rises, peaks around ~Day 12, then tapers as susceptibles decline. Hover to see exact and cumulative values.
    """)

    # --- Interactive Timeline (custom dropdown) ---
    def _timeline_md(day_idx: int) -> str:
        return f"""
**Day {day_idx}:**
- New cases today: {daily[day_idx]:.1f} students  
- Total cases so far: {np.cumsum(daily)[day_idx]:.0f} students  
- Remaining susceptible: {susceptible - np.cumsum(daily)[day_idx]:.0f} students  

**What's happening?**  
{ "The outbreak is just beginning. Most students are still susceptible." if day_idx < 5 else
  "Cases are rising rapidly as the virus spreads through the school." if day_idx < 15 else
  "The outbreak is peaking. Many susceptible students have been exposed." if day_idx < 25 else
  "The outbreak is winding down. Few susceptible students remain." }
        """

    timeline_day = st.slider("Explore the timeline: Day", 0, 30, 0)
    custom_expander("Interactive Disease Timeline", _timeline_md(timeline_day))

    # --- School Calendar (kept minimal; cells render the visualization) ---
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>School Calendar: Exclusion (Quarantine) Days</h2>", unsafe_allow_html=True)

    school_days, curr = [], datetime.today().date()
    while len(school_days) < 30:
        if curr.weekday() < 5:
            school_days.append(curr)
        curr += timedelta(days=1)
    exclusion_days = set(school_days[:q_days])

    cal_html = "<div style='max-width:680px; margin:auto;'><table style='width:100%; text-align:center; border-collapse:collapse;'><tr>"
    cal_html += ''.join(
        f"<th style='padding:6px;border-bottom:1px solid #ccc'>{wd}</th>" for wd in ['Mon','Tue','Wed','Thu','Fri']
    ) + '</tr>'

    i = 0
    while i < len(school_days):
        week = '<tr>'
        wd0 = school_days[i].weekday()
        week += ''.join("<td style='padding:12px;border:1px solid #eee;'></td>" for _ in range(wd0))
        for wd in range(wd0, 5):
            if i >= len(school_days):
                week += "<td style='padding:12px;border:1px solid #eee;'></td>"
            else:
                d = school_days[i]
                style = 'font-weight:bold; text-decoration:underline;' if d in exclusion_days else ''
                title = f"Quarantine Day {i+1}" if d in exclusion_days else ''
                week += f"<td title='{title}' style='padding:12px;border:1px solid #eee; {style}'>{d.strftime('%b %d')}</td>"
                i += 1
        week += '</tr>'
        cal_html += week
    cal_html += '</table></div>'

    st.markdown(cal_html, unsafe_allow_html=True)

    st.markdown("""
Confirmed measles cases are excluded from school from symptom onset through 4 days after rash onset.
Unvaccinated or incompletely vaccinated exposed students are excluded for 21 days after last exposure.
The calendar highlights those exclusion days.
    """)

    # --- Outbreak Summary (plain list + custom dropdown explanations) ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Outbreak Summary</h2>", unsafe_allow_html=True)

    summary_data = [
        {
            "title": "Total Infected",
            "value": f"{int(total_cases):,}",
            "explanation": f"Estimated total infected = attack rate ({attack*100:.1f}%) × susceptible ({int(susceptible):,}). Depends on R₀ and susceptibility."
        },
        {
            "title": "Hospitalizations",
            "value": f"{int(total_cases*hosp_rate):,}",
            "explanation": f"~20% of measles cases require hospitalization due to complications (e.g., pneumonia, encephalitis)."
        },
        {
            "title": "Deaths",
            "value": f"{int(total_cases*death_rate):,}",
            "explanation": "Fatal in ~0.03% of cases (≈3 in 10,000), usually from complications; risk varies by age and health status."
        },
        {
            "title": "Exposed Students",
            "value": f"{int(noninfected):,}",
            "explanation": "Unvaccinated students exposed but not infected still require 21 days of exclusion due to incubation period."
        },
        {
            "title": "Total Missed Days",
            "value": f"{int(total_days_missed):,}",
            "explanation": f"Infected isolation days ({int(isolate_missed):,}) + exposed quarantine days ({int(quarantine_missed):,})."
        },
        {
            "title": "Attack Rate",
            "value": f"{attack*100:.1f}%",
            "explanation": f"Share of susceptibles infected during the outbreak. With R₀=12 and {susceptible/enrollment*100:.1f}% susceptible."
        }
    ]

    # Show as simple bulleted list + custom dropdowns (no backgrounds)
    for item in summary_data:
        st.markdown(f"- **{item['title']}:** {item['value']}")
        custom_expander(f"Understanding {item['title']}", item['explanation'])

    # --- Educational Comparison Tool (custom dropdown) ---
    st.markdown("---")
    comparison_rates = [0.70, 0.85, 0.92, 0.95]
    comparison_rows = []
    for rate in comparison_rates:
        comp_susceptible = enrollment * (1 - rate)
        comp_s_frac = comp_susceptible / enrollment if enrollment else 0
        comp_z = 0.0001
        for _ in range(50):
            comp_z = 1 - np.exp(-R0 * comp_z * comp_s_frac)
        comp_attack = min(comp_z, 1.0)
        comp_cases = comp_attack * comp_susceptible
        comparison_rows.append({
            'Vaccination Rate': f"{rate*100:.0f}%",
            'Total Cases': int(comp_cases),
            'Hospitalizations': int(comp_cases * 0.2)
        })
    comp_df = pd.DataFrame(comparison_rows)

    custom_expander(
        "Compare Different Scenarios",
        "**See how vaccination rates affect outbreak size:**\n\n" +
        comp_df.to_markdown(index=False) + "\n\n" +
        "*Notice how vaccination rates above ~92% dramatically reduce outbreak size!*",
        open=False
    )

    # --- Disclaimer (custom dropdown, no background) ---
    custom_expander(
        "Educational Disclaimer",
        """
This simulator is for educational purposes and uses simplified assumptions with fixed parameters, assuming no additional interventions.  
Real outbreaks involve complex factors (behavior changes, public health response, seasonality).  
School-day calculations exclude weekends/holidays. For real-world guidance, consult ADHS and local public health authorities.
        """,
        open=False
    )
