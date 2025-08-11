# --- app.py ---
import streamlit as st
import streamlit.components.v1 as components

components.html(
    """
    <script>
      const sendWidth = () => {
        const w = window.innerWidth;
        window.parent.location = window.parent.location.pathname + "?_w=" + w;
      };
      window.addEventListener("load", sendWidth);
      window.addEventListener("resize", sendWidth);
    </script>
    """,
    height=0,
    width=0,
)

params = st.query_params
try:
    width = int(params.get("_w", [9999])[0])
except Exception:
    width = 9999
is_mobile = width < 768
st.session_state['is_mobile'] = is_mobile

st.set_page_config(
    page_title="ASU Health Observatory",
    layout="centered" if is_mobile else "wide",
    page_icon="🧬",
)

from config import inject_custom_styles, render_logo_and_title
inject_custom_styles()
render_logo_and_title()

from views import (
    tab1_case_trajectory,
    tab2_outbreak_map,
    tab3_then_vs_now,
    tab4_demographic_lens,
    tab5_az_school_risks,
)
from data import load_all_data


(df, df19, dfdetails, mmr, df_schools, df_us_cdc) = load_all_data()


df_schools["IMMUNE_MMR"] = df_schools["IMMUNE_MMR"].clip(0, 1)
df_schools["Susceptible"] = df_schools["ENROLLED"] * (1 - df_schools["IMMUNE_MMR"])

PAGES = {
    "Case Trajectory": lambda: tab1_case_trajectory.tab1_view(df, df_us_cdc=df_us_cdc),
    "Outbreak Map": lambda: tab2_outbreak_map.tab2_view(df),
    "Then vs. Now": lambda: tab3_then_vs_now.tab3_view(df, df19, mmr),
    "Demographics": lambda: tab4_demographic_lens.tab4_view(dfdetails),
    "AZ School Risks": lambda: tab5_az_school_risks.tab5_view(df_schools),
}

if is_mobile:
    choice = st.sidebar.selectbox("Jump to", list(PAGES.keys()))
    PAGES[choice]()
else:
    tabs = st.tabs(list(PAGES.keys()))
    for tab_obj, name in zip(tabs, PAGES.keys()):
        with tab_obj:
            PAGES[name]()
