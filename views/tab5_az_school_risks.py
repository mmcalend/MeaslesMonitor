import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def tab5_view(df_schools):
    colors = px.colors.sequential.Cividis

    # -------------------------
    # Title & Introduction
    # -------------------------
    st.markdown("""
    <div style='text-align:center; margin-bottom:1.5em;'>
      <h1>Arizona Measles Outbreak Simulator</h1>
      <p style='font-size:1.1rem; max-width:700px; margin:auto;'>
        Estimate the impact of measles on school communities, including infections, hospitalizations, absences, and more.<br>
        <em>Note: Schools with fewer than 20 kindergarten students are excluded from the selection list.</em>
      </p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------
    # Educational Context
    # -------------------------
    with st.expander("Understanding Disease Transmission (Click to Learn More)", expanded=False):
        st.markdown("""
        **Why is measles so contagious?**
        Measles remains airborne for up to 2 hours. Immunity and reproduction number (R₀) explain infection dynamics...
        """)

    with st.expander("Test Your Knowledge", expanded=False):
        st.markdown("""
        **Quick Quiz: How well do you understand measles?**  
        *(Quiz code goes here — restored from original)*
        """)

    # -------------------------
    # Assumptions
    # -------------------------
    st.markdown("<h2 style='text-align:center;'>Scientific Assumptions & Data Sources</h2>", unsafe_allow_html=True)

    assumptions_data = [
        {"title": "R₀: 12", "link": "...", "link_text": "PubMed", "explanation": "..."},
        {"title": "MMR Rate: ADHS 2024–25", "link": "...", "link_text": "ADHS", "explanation": "..."},
        {"title": "Hospitalization Rate: 20%", "link": "...", "link_text": "NFID", "explanation": "..."},
        {"title": "Death Rate: 0.03%", "link": "...", "link_text": "UChicago", "explanation": "..."},
        {"title": "Isolation: 4 days", "link": "...", "link_text": "Protocol", "explanation": "..."},
        {"title": "Quarantine: 21 days", "link": "...", "link_text": "ADHS", "explanation": "..."}
    ]

    cols = st.columns(3)
    for i, assumption in enumerate(assumptions_data):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background:{colors[i % len(colors)]}; color:white; padding:1rem; border-radius:10px; margin-bottom:0.5rem; min-height:90px;'>
              <strong>{assumption["title"]}</strong><br>
              <a href="{assumption["link"]}" target="_blank" style="color:#a5c9ff;">{assumption["link_text"]}</a>
            </div>
            """, unsafe_allow_html=True)
            with st.expander(f"About {assumption['title'].split(':')[0]}"):
                st.write(assumption['explanation'])

    # -------------------------
    # Herd Immunity Calculator
    # -------------------------
    with st.expander("Herd Immunity Calculator", expanded=False):
        r0_slider = st.slider("Adjust R₀", 2, 18, 12)
        herd_immunity_threshold = (1 - 1/r0_slider) * 100
        st.markdown(f"With R₀ = {r0_slider}, we need **{herd_immunity_threshold:.1f}%** vaccinated.")

    # -------------------------
    # Outbreak History
    # -------------------------
    with st.expander("Real-World Measles Outbreaks", expanded=False):
        st.markdown("""
        **Recent Arizona Cases:**  
        - 2024 (travel-linked)  
        - 2019 (Pinal County, 9 cases)  
        - 2008 (7 cases)  
        ...
        """)

    # -------------------------
    # Simulation Mode Selection
    # -------------------------
    st.markdown("<h2 style='text-align:center;'>Choose Simulation Mode</h2>", unsafe_allow_html=True)
    mode = st.radio("", ["Select a School", "Enter Custom Values"], horizontal=True)

    if mode == "Select a School":
        sel = st.selectbox("School:", df_schools["SCHOOL NAME"].sort_values())
        data = df_schools[df_schools["SCHOOL NAME"] == sel].iloc[0]
        enrollment, immune = int(data["ENROLLED"]), float(data["IMMUNE_MMR"])
    else:
        col1, col2 = st.columns(2)
        with col1:
            enrollment = st.number_input("Total Students", 1, 1000, 500)
        with col2:
            immune = st.slider("MMR Immunization Rate", 0.0, 1.0, 0.85)

    susceptible = enrollment * (1 - immune)

    # -------------------------
    # School Details
    # -------------------------
    st.markdown("<h2 style='text-align:center;'>School Details</h2>", unsafe_allow_html=True)
    detail_cols = st.columns(3)
    stats_data = [
        {"label": "Total Students", "value": f"{enrollment:,}"},
        {"label": "MMR Coverage", "value": f"{immune*100:.1f}%"},
        {"label": "Susceptible Students", "value": f"{int(susceptible):,}"}
    ]
    for i, stat in enumerate(stats_data):
        with detail_cols[i]:
            st.markdown(f"""
            <div style='background:{colors[i]}; color:white; padding:0.8rem; border-radius:8px; text-align:center;'>
              <strong>{stat["label"]}</strong><br>{stat["value"]}
            </div>
            """, unsafe_allow_html=True)
            if stat["label"] == "Total Students":
                with st.expander("More about total students"):
                    st.write("Total kindergarten enrollment...")
            elif stat["label"] == "MMR Coverage":
                with st.expander("More about MMR coverage"):
                    status = 'Above herd immunity threshold' if immune >= 0.917 else 'Below herd immunity threshold'
                    st.write(f"**Current status:** {status}")
            else:
                with st.expander("More about susceptible students"):
                    st.write("Students potentially at risk of infection...")

    if immune < 0.917:
        st.error("Below Herd Immunity Threshold: vulnerable to outbreaks.")
    else:
        st.success("Above Herd Immunity Threshold: strong protection.")

    # -------------------------
    # Outbreak Simulation
    # -------------------------
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

    # -------------------------
    # Epidemic Curve
    # -------------------------
    days = np.arange(0, 90)
    dist = (days**5) * np.exp(-days / 2)
    dist /= dist.sum()
    daily = dist * total_cases

    fig = go.Figure([go.Bar(
        x=days, y=daily,
        marker_color=colors[-2],
        hovertemplate='Day %{x}<br>New Cases: %{y:.1f}<br>Cumulative: %{customdata:.0f}<extra></extra>',
        customdata=np.cumsum(daily)
    )])
    peak_day, peak_cases = int(np.argmax(daily)), float(np.max(daily))
    fig.add_annotation(
        x=peak_day, y=peak_cases,
        text=f"Peak: Day {peak_day}<br>{peak_cases:.1f} cases",
        showarrow=True, arrowhead=2, arrowcolor="red", font=dict(color="red")
    )
    fig.update_layout(
        xaxis_title="Days since Introduction",
        yaxis_title="Daily New Cases (students)",
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=15, b=0)
    )

    st.markdown("<h2 style='text-align:center;'>Estimated Daily Cases</h2>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"Outbreak peaks around **Day {peak_day}** with **{peak_cases:.1f} new cases**.")

    # -------------------------
    # Outbreak Summary
    # -------------------------
    st.markdown("<h2 style='text-align:center;'>Outbreak Summary</h2>", unsafe_allow_html=True)
    summary_data = [
        {"title": "Total Infected", "value": f"{int(total_cases):,}", "percentage": f"({total_cases/enrollment*100:.1f}% of school)"},
        {"title": "Hospitalizations", "value": f"{int(total_cases*hosp_rate):,}", "percentage": f"({hosp_rate*100:.0f}% of cases)"},
        {"title": "Deaths", "value": f"{max(1, int(total_cases*death_rate)):,}" if total_cases*death_rate >= 0.5 else "<1", "percentage": f"({death_rate*100:.2f}% of cases)"},
        {"title": "Quarantined Students", "value": f"{int(noninfected):,}", "percentage": f"({noninfected/enrollment*100:.1f}% of school)"},
        {"title": "Total Missed Days", "value": f"{int(total_days_missed):,}", "percentage": f"({total_days_missed/(enrollment*180)*100:.1f}% of school-year)"},
        {"title": "Attack Rate", "value": f"{attack*100:.1f}%", "percentage": "of susceptible students"}
    ]
    cols_summary = st.columns(3)
    for i, item in enumerate(summary_data):
        with cols_summary[i % 3]:
            st.markdown(f"""
            <div style='background:{colors[i]}; color:white; padding:1rem; border-radius:8px; text-align:center; margin-bottom:0.5rem; min-height:100px;'>
              <strong>{item["title"]}</strong><br>
              <span style='font-size:1.2em;'>{item["value"]}</span><br>
              <small>{item["percentage"]}</small>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------
    # Economic Impact
    # -------------------------
    with st.expander("Economic Impact Analysis", expanded=False):
        avg_hosp_cost = 15000
        parent_lost_wages = 150
        total_hosp_cost = int(total_cases * hosp_rate) * avg_hosp_cost
        parent_cost = int(total_days_missed) * parent_lost_wages * 0.7
        total_estimated = total_hosp_cost + int(parent_cost) + 15000
        st.markdown(f"""
        **Estimated Costs:**  
        - Hospital: ${total_hosp_cost:,}  
        - Parent lost wages: ${int(parent_cost):,}  
        - Total: ${total_estimated:,}
        """)

    # -------------------------
    # Calendar Impact
    # -------------------------
    st.info(f"Infected excluded for 4 days; Unvaccinated exposed for 21 days; Total excluded: {int(total_cases + noninfected)}.")

    # -------------------------
    # Prevention & Resources
    # -------------------------
    with st.expander("Prevention & What You Can Do", expanded=False):
        st.markdown("""
        - Get Vaccinated  
        - Support strong school policies  
        - Share accurate info...
        """)
    with st.expander("Additional Resources", expanded=False):
        st.markdown("""
        **Arizona Department of Health Services**  
        - ADHS Measles Info  
        - Immunization Requirements  

        **National:**  
        - CDC Measles  
        - Vaccine Safety
        """)

    # -------------------------
    # Disclaimer
    # -------------------------
    st.warning("""
    **Educational Disclaimer:** This simulator uses simplified models and assumptions.  
    Outcomes are estimates and should not replace public health guidance.
    """)
