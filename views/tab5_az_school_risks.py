import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def tab5_view(df_schools):
    # --- Palette (Cividis) ---
    cividis = px.colors.sequential.Cividis  # light -> dark
    # choose darker, high-contrast swatches for card backgrounds
    c_bg1, c_bg2, c_bg3, c_bg4, c_bg5, c_bg6 = cividis[-2], cividis[-3], cividis[-4], cividis[-5], cividis[-6], cividis[-7]

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

    # Educational context section (FIX: use "with", not "if")
    with st.expander("Understanding Disease Transmission (Click to Learn More)", expanded=False):
        st.markdown("""
        **Why is measles so contagious?**
        
        Measles is one of the most contagious diseases known to humans. When an infected person coughs or sneezes, they release tiny droplets containing the virus that can remain in the air for up to 2 hours. If you're not immune and walk into a room where an infected person was, you have a 90% chance of getting sick!
        
        **Key Concepts:**
        - **R₀ (Basic Reproduction Number)**: The average number of people one infected person will infect
        - **Herd Immunity**: When enough people are vaccinated to protect the whole community
        - **Attack Rate**: The percentage of susceptible people who get infected during an outbreak
        - **Quarantine vs Isolation**: Isolation separates sick people; quarantine separates those who might be sick
        """)

    st.markdown("""
    <div style='text-align:center; margin-bottom:1em;'>
      <h2 style='text-align:center; margin:0.75em 0 0.5em;'>Scientific Assumptions & Data Sources</h2>
    </div>
    """, unsafe_allow_html=True)

    # --- Assumptions (use Cividis backgrounds) ---
    assumptions_data = [
        {
            "title": "R₀: 12",
            "link": "https://pubmed.ncbi.nlm.nih.gov/28757186/",
            "link_text": "PubMed",
            "bg_color": c_bg1,
            "explanation": "R₀ is the basic reproduction number. Measles has an R₀ around 12—extremely contagious."
        },
        {
            "title": "MMR Rate: ADHS 2024–25",
            "link": "https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage",
            "link_text": "ADHS",
            "bg_color": c_bg2,
            "explanation": "Arizona kindergarten MMR coverage; two doses are ~97% effective."
        },
        {
            "title": "Hospitalization Rate: 20%",
            "link": "https://www.nfid.org/infectious-disease/measles/",
            "link_text": "NFID",
            "bg_color": c_bg3,
            "explanation": "Roughly 1 in 5 measles cases require hospital care."
        },
        {
            "title": "Death Rate: 0.03%",
            "link": "https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease",
            "link_text": "UChicago",
            "bg_color": c_bg4,
            "explanation": "About 3 in 10,000 cases are fatal; risk varies by age and health."
        },
        {
            "title": "Isolation: 4 days",
            "link": "https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/infectious-disease-epidemiology/school-childcare/measles-protocol.pdf",
            "link_text": "Protocol",
            "bg_color": c_bg5,
            "explanation": "Isolation from 4 days before rash through 4 days after rash onset."
        },
        {
            "title": "Quarantine: 21 days",
            "link": "https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/infectious-disease-epidemiology/school-childcare/mmr-guidance.pdf",
            "link_text": "ADHS",
            "bg_color": c_bg6,
            "explanation": "Unvaccinated exposed students excluded for 21 days after last exposure."
        }
    ]

    cols = st.columns(3)
    for i, assumption in enumerate(assumptions_data):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:{assumption["bg_color"]}; color:white; padding:1rem; border-radius:10px; margin-bottom:0.5rem;'>
              <strong>{assumption["title"]}</strong><br>
              <a href="{assumption["link"]}" target="_blank" style="color:#ffffff;">{assumption["link_text"]}</a>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Learn more about {assumption['title'].split(':')[0]}", key=f"assumption_{i}"):
                st.info(assumption['explanation'])

    # --- Interactive Learning Section (FIX expander) ---
    st.markdown("---")
    with st.expander("Try This: Herd Immunity Calculator", expanded=False):
        st.markdown("**Calculate the vaccination rate needed for herd immunity:**")
        herd_immunity_threshold = (1 - 1/12) * 100
        st.markdown(f"""
        With R₀ = 12, we need **{herd_immunity_threshold:.1f}%** of the population vaccinated to achieve herd immunity.
        
        **Formula**: Herd Immunity Threshold = (1 - 1/R₀) × 100
        """)

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
        immune = st.slider("MMR Immunization Rate", 0.0, 1.0, 0.85, help="Drag to see how vaccination rates affect outbreak size")

    susceptible = enrollment * (1 - immune)
    
    # --- School Details (Cividis backgrounds) ---
    st.markdown("""
    <div style='text-align:center; margin-bottom:1em;'>
      <h2 style='margin-bottom:0.3em;'>School Details</h2>
    </div>
    """, unsafe_allow_html=True)
    
    detail_cols = st.columns(3)
    with detail_cols[0]:
        st.markdown(f"""
        <div style='background:{c_bg2}; color:white; padding:0.8rem; border-radius:8px; text-align:center;'>
          <strong>Total Students:</strong><br>{enrollment:,}
        </div>
        """, unsafe_allow_html=True)
        if st.button("Learn about Total Students", key="total_students"):
            st.info("Count of kindergarten students used for modeling due to recent vaccination reporting and close contact patterns.")
    
    with detail_cols[1]:
        st.markdown(f"""
        <div style='background:{c_bg3}; color:white; padding:0.8rem; border-radius:8px; text-align:center;'>
          <strong>MMR Coverage:</strong><br>{immune*100:.1f}%
        </div>
        """, unsafe_allow_html=True)
        if st.button("Learn about MMR Coverage", key="mmr_coverage"):
            status = 'Above herd immunity threshold' if immune >= 0.9167 else 'Below herd immunity threshold'
            st.info(f"Percentage immune to measles (typically via vaccination). Current status: {status}.")
    
    with detail_cols[2]:
        st.markdown(f"""
        <div style='background:{c_bg4}; color:white; padding:0.8rem; border-radius:8px; text-align:center;'>
          <strong>Susceptible Students:</strong><br>{int(susceptible):,}
        </div>
        """, unsafe_allow_html=True)
        if st.button("Learn about Susceptible Students", key="susceptible_students"):
            risk_level = 'Low risk' if susceptible < enrollment * 0.1 else 'Moderate risk' if susceptible < enrollment * 0.2 else 'High risk'
            st.info(f"Students who could get measles if exposed: Total × (1 − Vaccination Rate). Risk level: {risk_level}.")

    # Herd immunity note
    if immune < 0.9167:
        st.markdown("**Below Herd Immunity Threshold:** With vaccination rates below ~91.7%, this school community is vulnerable to measles outbreaks.")
    else:
        st.markdown("**Above Herd Immunity Threshold:** High vaccination rates make large outbreaks unlikely.")

    # --- Simulation Calculations ---
    R0 = 12
    initial = st.number_input("Initial Infected Students", 1, 50, 1, help="How many students are infected when measles is first introduced to the school?")
    
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
    
    # --- Daily Cases Chart (Cividis color) ---
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Estimated Daily Measles Cases</h2>", unsafe_allow_html=True)
    
    days = np.arange(0, 90)
    dist = (days**5) * np.exp(-days / 2)
    dist /= dist.sum()
    daily = dist * total_cases
    
    bar_color = cividis[-2]
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
        yaxis=dict(title="Daily New Cases (students)", showgrid=False, range=[0, 15]),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=15, b=0)
    )
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    
    st.markdown("""
    This bar chart shows projected new measles cases per school day over 90 days after introduction.
    The curve rises, peaks around Day ~12, then tapers as susceptibles decline. Hover for exact values.
    """)

    # --- Interactive Timeline (FIX expander) ---
    with st.expander("Interactive Disease Timeline", expanded=False):
        timeline_day = st.slider("Explore the timeline: Day", 0, 30, 0)
        stage_description = (
            "The outbreak is just beginning. Most students are still susceptible." if timeline_day < 5 else
            "Cases are rising rapidly as the virus spreads through the school." if timeline_day < 15 else
            "The outbreak is peaking. Many susceptible students have been exposed." if timeline_day < 25 else
            "The outbreak is winding down. Few susceptible students remain."
        )
        st.markdown(f"""
        **Day {timeline_day}:**
        - New cases today: {daily[timeline_day]:.1f} students
        - Total cases so far: {np.cumsum(daily)[timeline_day]:.0f} students
        - Remaining susceptible: {susceptible - np.cumsum(daily)[timeline_day]:.0f} students
        
        **What's happening?** {stage_description}
        """)

    # --- School Calendar: Exclusion (Quarantine) Days ---
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
        week += ''.join("<td style='padding:12px;border:1px solid #eee;background:#f0f0f0'></td>" for _ in range(wd0))
        for wd in range(wd0, 5):
            if i >= len(school_days):
                week += "<td style='padding:12px;border:1px solid #eee;background:#f0f0f0'></td>"
            else:
                d = school_days[i]
                style = f'background:{cividis[-2]}; color:white; ' if d in exclusion_days else ''
                title = f"Quarantine Day {i+1}" if d in exclusion_days else ''
                week += f"<td title='{title}' style='padding:12px;border:1px solid #eee;{style}'>{d.strftime('%b %d')}</td>"
                i += 1
        week += '</tr>'
        cal_html += week
    cal_html += '</table></div>'
    
    st.markdown(cal_html, unsafe_allow_html=True)
    
    st.markdown("""
    Confirmed cases are excluded from school from symptom onset through 4 days after rash onset.
    Unvaccinated or incompletely vaccinated exposed students are excluded for 21 days after last exposure.
    The calendar shades exclusion days for the next 30 weekdays.
    """)

    # --- Outbreak Summary (Cividis) ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Outbreak Summary</h2>", unsafe_allow_html=True)

    colors = cividis
    summary_data = [
        {
            "title": "Total Infected",
            "value": f"{int(total_cases):,}",
            "bg_color": colors[-3],
            "explanation": f"Estimated infections = attack rate ({attack*100:.1f}%) × susceptibles ({int(susceptible):,})."
        },
        {
            "title": "Hospitalizations",
            "value": f"{int(total_cases*hosp_rate):,}",
            "bg_color": colors[-4],
            "explanation": "Approx. 20% of cases require hospitalization."
        },
        {
            "title": "Deaths",
            "value": f"{int(total_cases*death_rate):,}",
            "bg_color": colors[-5],
            "explanation": "Approx. 0.03% fatality risk; varies by age and access to care."
        },
        {
            "title": "Exposed Students",
            "value": f"{int(noninfected):,}",
            "bg_color": colors[-6],
            "explanation": "Unvaccinated exposed but not infected; excluded for 21 days."
        },
        {
            "title": "Total Missed Days",
            "value": f"{int(total_days_missed):,}",
            "bg_color": colors[-7],
            "explanation": f"Isolation ({int(isolate_missed):,}) + quarantine ({int(quarantine_missed):,}) days."
        },
        {
            "title": "Attack Rate",
            "value": f"{attack*100:.1f}%",
            "bg_color": colors[-8],
            "explanation": f"Depends on R₀ and susceptible share ({susceptible/enrollment*100:.1f}%)."
        }
    ]
    
    cols1 = st.columns(3)
    cols2 = st.columns(3)
    all_cols = cols1 + cols2
    
    for i, item in enumerate(summary_data):
        with all_cols[i]:
            st.markdown(f"""
            <div style='background:{item["bg_color"]}; color:white; padding:1rem; border-radius:8px; text-align:center; margin-bottom:0.5rem;'>
              <strong>{item["title"]}</strong><br>{item["value"]}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Learn about {item['title']}", key=f"summary_{i}"):
                st.info(item['explanation'])

    # --- Educational Comparison Tool (FIX expander) ---
    st.markdown("---")
    with st.expander("Compare Different Scenarios", expanded=False):
        st.markdown("**See how vaccination rates affect outbreak size:**")
        comparison_rates = [0.70, 0.85, 0.92, 0.95]
        comparison_data = []
        for rate in comparison_rates:
            comp_susceptible = enrollment * (1 - rate)
            comp_s_frac = comp_susceptible / enrollment if enrollment else 0
            comp_z = 0.0001
            for _ in range(50):
                comp_z = 1 - np.exp(-R0 * comp_z * comp_s_frac)
            comp_attack = min(comp_z, 1.0)
            comp_cases = comp_attack * comp_susceptible
            comparison_data.append({
                'Vaccination Rate': f"{rate*100:.0f}%",
                'Total Cases': int(comp_cases),
                'Hospitalizations': int(comp_cases * 0.2)
            })
        comp_df = pd.DataFrame(comparison_data)
        st.dataframe(comp_df, hide_index=True)
        st.markdown("*Vaccination rates above ~92% dramatically reduce outbreak size.*")

    # --- Disclaimer ---
    st.markdown("""
    **Educational Disclaimer:** This simulator simplifies real-world dynamics. Parameters are fixed and assume no additional public health interventions or seasonality. For guidance on real outbreaks, consult ADHS and local public health authorities.
    """)
