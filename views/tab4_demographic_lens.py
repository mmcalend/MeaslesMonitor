import streamlit as st
from helpers import normalize
from charts import (
    stacked_bar_chart,
    proportional_pictogram_bar,
    subset_proportional_pictogram_bar
)
from config import death_colors, age_colors, vaccine_colors

def tab4_view(dfdetails):
    row = dfdetails.iloc[0]
    total_cases = row["total_cases"]

    # Age group breakdown
    age_groups = normalize({
        "Under 5": row["age_under_5_years"],
        "5–19": row["age_5-19_years"],
        "20+": row["age_20+_years"],
        "Unknown": row["unknown_age"]
    })

    # Vaccine status breakdown
    vaccine_groups = normalize({
        "Unvaccinated or Unknown": row["unvaccinated_or_unknown"],
        "1 MMR Dose": row["one_mmr_dose"],
        "2 MMR Doses": row["two_mmr_doses"]
    })

    # Hospitalization proportions within each age group
    hosp_proportions_within_age = {
        "Under 5": row["age1_hosp"],
        "5–19": row["age2_hosp"],
        "20+": row["age3_hosp"],
        "Unknown": row["age4_hosp"]
    }

    # Outcomes: deaths, hospitalized, survived
    deaths = row["total_deaths"]
    hospitalized = row["hospitalized_cases"]
    death_groups = {
        "Deaths": deaths,
        "Hospitalized (Survived)": hospitalized - deaths,
        "Survived (Non-Hospitalized)": total_cases - hospitalized
    }

    # --- Death/hospitalization/survival ---
       st.markdown(
        "<h2 style='text-align: center; margin-bottom: 0.5rem;'>"
        "Measles Outcomes in 2025</h2>",
        unsafe_allow_html=True
    )
    
    fig = stacked_bar_chart(
        {k: v / total_cases for k, v in death_groups.items()},
        "",
        colors=death_colors
    )
    
    fig.update_traces(
        hovertemplate="<b>%{name}</b><br>%{x:.1f}%<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    # --- Age & hospitalization pictograms side-by-side ---
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.5rem;'>Age Distribution and Hospitalization Among Measles Cases</h2>", unsafe_allow_html=True)
    left, col1, col2, right = st.columns([2, 3, 3, 2])

    with col1:
        st.plotly_chart(proportional_pictogram_bar(age_groups, "", total_cases, colors=age_colors), use_container_width=False)

    with col2:
        hospitalized_age_data = {
            age: {"yes": hosp_proportions_within_age[age]}
            for age in hosp_proportions_within_age
        }
        st.plotly_chart(subset_proportional_pictogram_bar(hospitalized_age_data, "", colors=age_colors), use_container_width=False)

    # --- Vaccination pictogram ---
    st.markdown("<h2 style='text-align: center; margin-bottom: 0.5rem;'>Measles Cases by Vaccination Status</h2>", unsafe_allow_html=True)
    st.plotly_chart(stacked_bar_chart(vaccine_groups, "", colors=vaccine_colors), use_container_width=True)

    # --- Explanatory Markdown ---
    st.markdown("""
    <div style='text-align: left; font-size: 1.1rem; line-height: 1.5; margin: 1rem auto;'>
        The graphs above show demographics of 2025 measles cases in the United States:
        <ul>
            <li>Measles Outcomes: % hospitalized, not hospitalized, or died</li>
            <li>Cases by Age Group: under 5, 5–19, 20+, unknown</li>
            <li>Hospitalization Proportion by Age Group: proportion of hospitalized cases within each age group</li>
            <li>Cases by Vaccination Status</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size: 0.8rem;'>
        <a href='https://www.cdc.gov/measles/data-research/index.html' target='_blank'>
        Data Source: CDC Measles Cases and Outbreaks</a>
    </div>
    """, unsafe_allow_html=True) 
