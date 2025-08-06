import streamlit as st
from datetime import datetime


def set_page_config():
    st.set_page_config(
        page_title="ASU Health Observatory",
        layout="wide",
        page_icon="🧬"
    )


def inject_custom_styles():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald&display=swap');
    * {{ font-family: 'Oswald', sans-serif !important; }}

    /* Footer styling */
    .footer {{
        background-color: #000;
        padding: 8px 12px;
        border-radius: 6px;
        width: fit-content;
        font-size: 10px;
    }}
    .footer a {{
        color: #FFF;
        text-decoration: none;
    }}
    .footer a:hover {{
        text-decoration: underline;
    }}

    /* Tab list styling */
    div[data-baseweb="tab-list"] button {{
        --tab-background-color: #F0F0F0;
        font-size: 16px;
    }}
    div[data-baseweb="tab-list"] button[aria-selected="true"] {{
        color: #6A4C93 !important;
        border-bottom: 3px solid #6A4C93 !important;
    }}
    div[data-baseweb="tab-list"] button:hover:not([aria-selected="true"]) {{
        background-color: #B497BD !important;
        color: black !important;
    }}

    /* Blocked text styling */
    .blocked-text {{
        text-align: center;
        font-size: 1.1rem;
        line-height: 1.5;
        margin: 1rem auto;
        width: 100%;
        padding: 0 1rem;
    }}

    /* Plotly legend text */
    .js-plotly-plot .plotly .legend .groups .trace .legendtext {{
        font-size: 16px !important;
    }}

    /* Last refreshed banner */
    .last-refreshed {{
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 0.8rem;
    }}

    /* Tooltip CSS: hover on desktop, focus on mobile */
    [title] {{
      position: relative;
      cursor: help;
      outline: none;
    }}
    [title]:hover::after,
    [title]:focus::after {{
      content: attr(title);
      position: absolute;
      top: -1.5em;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0,0,0,0.8);
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      white-space: nowrap;
      z-index: 10;
      pointer-events: none;
    }}
    [title]:hover::before,
    [title]:focus::before {{
      content: "";
      position: absolute;
      top: calc(-1.5em - 6px);
      left: 50%;
      transform: translateX(-50%);
      border: 6px solid transparent;
      border-bottom-color: rgba(0,0,0,0.8);
      z-index: 10;
      pointer-events: none;
    }}
    </style>
    <div class="last-refreshed">Last refreshed: {datetime.now():%Y-%m-%d}</div>
    """, unsafe_allow_html=True)


def render_logo_and_title():
    st.markdown("""
    <div style='text-align: left;'>
        <img src="https://github.com/mmcalend/USMeaslesData/blob/main/Logo.jpg?raw=true"
             alt="ASU Health Observatory Logo"
             style="width: 200px; max-width: 100%; height: auto;">
    </div>
    <h1 style='text-align: center;'>The Measles Monitor</h1>
    <p style='font-size:1.1rem; margin-top:0; margin-bottom:0.5em;'>
        <span tabindex="0" title="Zoom in or use full-screen for best mobile viewing">Mobile users:</span> please use the zoom and full screen features for best viewing.
    </p>
    """, unsafe_allow_html=True)


# Color palettes
death_colors = ["#6A4C93", "#9B8CC2", "#595959"]
age_colors = ["#440154", "#31688E", "#35B779", "#FDE725"]
vaccine_colors = ["#3B528B", "#21918C", "#5DC863"]



