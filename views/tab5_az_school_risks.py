import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def tab5_view(df_schools):
    # --- Custom CSS for better styling ---
    st.markdown("""
    <style>
    .info-dropdown {
        margin-top: 5px;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    .educational-note {
        background: #e8f4fd;
        border-left: 4px solid #1f77b4;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .warning-note {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .blocked-text {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Header & Educational Introduction ---
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1 style='margin-bottom:0.2em;'>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.1rem; margin-top:0; margin-bottom:0.5em;'>
        Estimate the impact of measles on school communities, including infections, hospitalizations, absences, and more.<br>
        <em>Note: Schools with fewer than 20 kindergarten students are excluded from the selection list.</em>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Educational context section
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

    # --- Enhanced Assumptions with Dropdowns ---
    assumptions_data = [
        {
            "title": "R₀: 12",
            "link": "https://pubmed.ncbi.nlm.nih.gov/28757186/",
            "link_text": "PubMed",
            "bg_color": "#2f2e41",
            "explanation": "R₀ (R-naught) is the basic reproduction number - how many people one infected person will infect on average in a completely susceptible population. Measles has an R₀ of 12, making it one of the most contagious diseases. For comparison: COVID-19 original strain ≈ 2-3, Seasonal flu ≈ 1.3."
        },
        {
            "title": "MMR Rate: ADHS 2024–25",
            "link": "https://www.azdhs.gov/preparedness/epidemiology-disease-control/immunization/#reports-immunization-coverage",
            "link_text": "ADHS",
            "bg_color": "#3d3c5a",
            "explanation": "MMR (Measles, Mumps, Rubella) vaccination rate for kindergarten students in Arizona. The MMR vaccine is about 97% effective after two doses. Arizona requires this data to be reported annually by schools."
        },
        {
            "title": "Hospitalization Rate: 20%",
            "link": "https://www.nfid.org/infectious-disease/measles/",
            "link_text": "NFID",
            "bg_color": "#47465c",
            "explanation": "About 1 in 5 people with measles need hospital care. Complications can include pneumonia (lung infection), brain swelling, and severe diarrhea. Children under 5 and adults over 20 are at highest risk for complications."
        },
        {
            "title": "Death Rate: 0.03%",
            "link": "https://www.uchicagomedicine.org/forefront/pediatrics-articles/measles-is-still-a-very-dangerous-disease",
            "link_text": "UChicago",
            "bg_color": "#4e4d6b",
            "explanation": "While rare in developed countries with good healthcare, measles can be fatal. Deaths usually occur from complications like pneumonia or brain swelling (encephalitis). The death rate is higher in children under 5 and adults over 20."
        },
        {
            "title": "Isolation: 4 days",
            "link": "https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/infectious-disease-epidemiology/school-childcare/measles-protocol.pdf",
            "link_text": "Protocol",
            "bg_color": "#5A4E7A",
            "explanation": "People with measles must stay home from 4 days before the rash appears until 4 days after the rash appears. This is when they're most contagious. The rash typically appears 2-3 days after symptoms begin."
        },
        {
            "title": "Quarantine: 21 days",
            "link": "https://www.azdhs.gov/documents/preparedness/epidemiology-disease-control/infectious-disease-epidemiology/school-childcare/mmr-guidance.pdf",
            "link_text": "ADHS",
            "bg_color": "#6d6b85",
            "explanation": "Unvaccinated people exposed to measles must be excluded from school for 21 days after their last exposure (the measles incubation period). This prevents them from spreading the disease if they become infected, since symptoms can take up to 21 days to appear."
        }
    ]

    # Display assumptions with dropdowns
    cols = st.columns(3)
    for i, assumption in enumerate(assumptions_data):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:{assumption["bg_color"]}; color:white; padding:1rem; border-radius:10px; margin-bottom:0.5rem;'>
              <strong>{assumption["title"]}</strong><br>
              <a href="{assumption["link"]}" target="_blank" style="color:#a5c9ff;">{assumption["link_text"]}</a>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("What does this mean?"):
                st.markdown(assumption['explanation'])

    # --- Interactive Learning Section ---
    st.markdown("---")
    with st.expander("Try This: Herd Immunity Calculator", expanded=False):
        st.markdown("**Calculate the vaccination rate needed for herd immunity:**")
        herd_immunity_threshold = (1 - 1/12) * 100  # (1 - 1/R₀) × 100
        st.markdown(f"""
        With R₀ = 12, we need **{herd_immunity_threshold:.1f}%** of the population vaccinated to achieve herd immunity.
        
        **Formula**: Herd Immunity Threshold = (1 - 1/R₀) × 100
        
        This means if {herd_immunity_threshold:.1f}% of students are vaccinated, an outbreak is unlikely to spread widely even if measles is introduced.
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
    
    # Enhanced School Details with explanatory dropdowns
    st.markdown(f"""
    <div style='text-align:center; margin-bottom:1em;'>
      <h2 style='margin-bottom:0.3em;'>School Details</h2>
    </div>
    """, unsafe_allow_html=True)
    
    detail_cols = st.columns(3)
    
    with detail_cols[0]:
        st.markdown(f"""
        <div style='background:#393855; color:white; padding:0.8rem; border-radius:8px; text-align:center;'>
          <strong>Total Students:</strong><br>{enrollment:,}
        </div>
        """, unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown("This is the total number of kindergarten students enrolled at the school. Kindergarten students are often used in outbreak modeling because they have the most recent vaccination data and spend lots of time in close contact.")
    
    with detail_cols[1]:
        st.markdown(f"""
        <div style='padding:0.8rem; border-radius:8px; text-align:center;'>
          <strong>MMR Coverage:</strong><br>{immune*100:.1f}%
        </div>
        """, unsafe_allow_html=True)
        with st.expander("💉 What does this mean?"):
            st.markdown(f"""
            This is the percentage of students who are immune to measles (usually through vaccination). 
            
            **Current status**: {'Above herd immunity threshold' if immune >= 0.917 else 'Below herd immunity threshold'}
            
            Arizona requires 95% MMR coverage, but allows exemptions for medical, religious, or personal beliefs.
            """)
    
    with detail_cols[2]:
        st.markdown(f"""
        <div style='background:#5a5977; color:white; padding:0.8rem; border-radius:8px; text-align:center;'>
          <strong>Susceptible Students:</strong><br>{int(susceptible):,}
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🎯 What does this mean?"):
            st.markdown(f"""
            These are students who could get measles if exposed - calculated as: Total Students × (1 - Vaccination Rate)
            
            **Risk level**: {'Low risk' if susceptible < enrollment * 0.1 else 'Moderate risk' if susceptible < enrollment * 0.2 else 'High risk'}
            
            The more susceptible students, the faster and larger an outbreak can become.
            """)

    # Show vaccination impact
    if immune < 0.917:
        st.markdown("""
        <div class="warning-note">
          <strong>Below Herd Immunity Threshold:</strong> With vaccination rates below 91.7%, this school community is vulnerable to measles outbreaks. Even a single case could lead to widespread transmission.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="educational-note">
          <strong>Above Herd Immunity Threshold:</strong> This school has strong community protection! High vaccination rates make large outbreaks unlikely.
        </div>
        """, unsafe_allow_html=True)

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
    
    # --- Enhanced Daily Cases Chart with Fixed Y-Axis ---
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
    
    # Fixed y-axis at 20 as requested
    fig.update_layout(
        xaxis=dict(title="Days since Introduction", showgrid=False),
        yaxis=dict(title="Daily New Cases (students)", showgrid=False, range=[0, 20]),
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    
    st.markdown("""
    <div class="blocked-text">
      This bar chart shows the projected number of new measles cases per school day over a 90-day period following the introduction of the virus into the school.
      The curve follows a gamma distribution: it rises gradually as the outbreak grows, peaks around Day 12 when most susceptible students have been exposed, then tapers off as fewer susceptibles remain.
      Hover over each bar to see exact numbers and cumulative cases.
    </div>
    """, unsafe_allow_html=True)

    # --- Interactive Timeline ---
    with st.expander("Interactive Disease Timeline", expanded=False):
        timeline_day = st.slider("Explore the timeline: Day", 0, 30, 0)
        st.markdown(f"""
        **Day {timeline_day}:**
        - New cases today: {daily[timeline_day]:.1f} students
        - Total cases so far: {np.cumsum(daily)[timeline_day]:.0f} students
        - Remaining susceptible: {susceptible - np.cumsum(daily)[timeline_day]:.0f} students
        
        **What's happening?**
        {
        "The outbreak is just beginning. Most students are still susceptible." if timeline_day < 5 else
        "Cases are rising rapidly as the virus spreads through the school." if timeline_day < 15 else
        "The outbreak is peaking. Many susceptible students have been exposed." if timeline_day < 25 else
        "The outbreak is winding down. Few susceptible students remain."
        }
        """)

    # --- School Calendar: Exclusion (Quarantine) Days ---
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>School Calendar: Exclusion (Quarantine) Days</h2>", unsafe_allow_html=True)
    
    school_days, curr = [], datetime.today().date()
    while len(school_days) < 30:
        if curr.weekday() < 5:
            school_days.append(curr)
        curr += timedelta(days=1)
    exclusion_days = set(school_days[:q_days])
    
    # Fixed-width container for calendar
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
    
    st.markdown("""
    <div class="blocked-text">
      Confirmed measles cases must be kept out of school from symptom onset through 4 days after rash onset.
      Unvaccinated or incompletely vaccinated exposed students are excluded for 21 days after last exposure.
      This calendar shows the next 30 school weekdays with shaded cells marking quarantine days. The dark cells represent days when unvaccinated students would be excluded from school.
    </div>
    """, unsafe_allow_html=True)

    # --- Enhanced Outbreak Summary with Explanatory Dropdowns ---
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin:0.75em 0 0.5em;'>Outbreak Summary</h2>", unsafe_allow_html=True)
    
    # Create the summary cards
    summary_data = [
        {
            "title": "Total Infected",
            "value": f"{int(total_cases):,}",
            "bg_color": colors[-3],
            "explanation": f"This is the estimated total number of students who would get measles during the outbreak. It's calculated using the attack rate ({attack*100:.1f}%) multiplied by susceptible students ({int(susceptible):,}). The attack rate depends on how contagious measles is (R₀=12) and how many students are susceptible."
        },
        {
            "title": "Hospitalizations",
            "value": f"{int(total_cases*hosp_rate):,}",
            "bg_color": colors[-4],
            "explanation": f"About 20% of measles cases require hospitalization due to complications like pneumonia, severe diarrhea, or brain swelling. This represents {int(total_cases*hosp_rate):,} students who would likely need hospital care. Children under 5 are at highest risk for severe complications."
        },
        {
            "title": "Deaths",
            "value": f"{int(total_cases*death_rate):,}",
            "bg_color": colors[-5],
            "explanation": f"While rare in countries with good healthcare, measles can be fatal in about 0.03% of cases (roughly 3 in 10,000). Deaths usually result from complications like pneumonia or brain inflammation. This estimate shows the statistical risk, though actual outcomes depend on medical care quality and individual health factors."
        },
        {
            "title": "Exposed Students",
            "value": f"{int(noninfected):,}",
            "bg_color": colors[-6],
            "explanation": f"These are unvaccinated students who were exposed to measles but didn't get infected. They still must be quarantined for 21 days as a precaution because measles symptoms can take up to 21 days to appear. Even though they're not sick, they miss school to prevent potential spread."
        },
        {
            "title": "Total Missed Days",
            "value": f"{int(total_days_missed):,}",
            "bg_color": colors[-7],
            "explanation": f"This combines school days missed by infected students (isolation: {int(isolate_missed):,} days) and exposed unvaccinated students (quarantine: {int(quarantine_missed):,} days). Each infected student misses 4 days, each exposed unvaccinated student misses 21 days. This represents the total educational disruption."
        },
        {
            "title": "Attack Rate",
            "value": f"{attack*100:.1f}%",
            "bg_color": colors[-8],
            "explanation": f"The attack rate is the percentage of susceptible people who get infected during an outbreak. It depends on how contagious the disease is (R₀) and the proportion of susceptible people. With R₀=12 and {susceptible/enrollment*100:.1f}% of students susceptible, {attack*100:.1f}% of susceptible students would likely get measles."
        }
    ]
    
    # Display summary cards in two rows
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
            
            with st.expander(f"Understanding {item['title']}"):
                st.markdown(item['explanation'])

    # --- Educational Comparison Tool ---
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
        st.markdown("*Notice how vaccination rates above 92% dramatically reduce outbreak size!*")

    # --- Disclaimer ---
    st.markdown("""
    <div class="blocked-text">
      <strong>Educational Disclaimer:</strong> This simulator is designed for educational purposes to help understand disease transmission dynamics. 
      It uses simplified mathematical models with fixed parameters and assumes no additional public health interventions during an outbreak. 
      Real outbreaks involve complex factors including behavior changes, public health responses, and seasonal variations. 
      The model excludes holidays and weekends from school day calculations. For actual outbreak response and guidance, 
      always consult the Arizona Department of Health Services (ADHS) and local public health authorities.
    </div>
    """, unsafe_allow_html=True)
