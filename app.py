# --- app.py ---
from config import set_page_config, inject_custom_styles, render_logo_and_title
set_page_config()
inject_custom_styles()
render_logo_and_title()

import streamlit as st
from views import (
    tab1_case_trajectory,
    tab2_outbreak_map,
    tab3_then_vs_now,
    tab4_demographic_lens,
    tab5_az_school_risks
)
from data import load_all_data

# --- Load Data ---
df, df19, dfdetails, mmr, df_schools = load_all_data()
df_schools["IMMUNE_MMR"] = df_schools["IMMUNE_MMR"].clip(0, 1)
df_schools["Susceptible"] = df_schools["ENROLLED"] * (1 - df_schools["IMMUNE_MMR"])


# --- Define Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Case Trajectory",
    "Outbreak Map",
    "Then vs. Now",
    "Demographics",
    "AZ School Risks"
])

with tab1:
    tab1_case_trajectory.tab1_view(df)

with tab2:
    tab2_outbreak_map.tab2_view(df)

with tab3:
    tab3_then_vs_now.tab3_view(df, df19, mmr)

with tab4:
    tab4_demographic_lens.tab4_view(dfdetails)

with tab5:
    tab5_az_school_risks.tab5_view(df_schools)


