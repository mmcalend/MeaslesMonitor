import streamlit as st

def render_footer(url, label, color="#FFFFFF"):
    st.markdown(f"""
    <div class="footer">
        <a href="{url}" target="_blank" style="color: {color};">{label}</a>
    </div>
    """, unsafe_allow_html=True)

def apply_common_plot_layout(fig, title, colorbar=False):
    fig.update_layout(
        title=title,
        title_x=0.5,
        title_font=dict(size=18),
        xaxis_title_font=dict(size=16),
        yaxis_title_font=dict(size=16),
        xaxis_tickfont=dict(size=14),
        yaxis_tickfont=dict(size=14),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    if not colorbar:
        fig.update_layout(coloraxis_colorbar=dict(title="", tickvals=[]))
    return fig

def normalize(d):
    total = sum(d.values())
    return {k: v / total if total else 0 for k, v in d.items()}

def custom_expander(title, content_md, open=False):
    """
    Custom collapsible section with transparent background.
    """
    open_attr = "open" if open else ""
    html = f"""
    <details {open_attr} style="
        margin-bottom:1rem;
        background-color:transparent;
        border-radius:8px;
        padding:0.25rem;
        border: none;
    ">
      <summary style="
          font-weight:bold;
          cursor:pointer;
          color:white;
          font-size:1.05rem;
      ">{title}</summary>
      <div style="margin-top:0.75rem; color:white; line-height:1.5;">
        {content_md}
      </div>
    </details>
    """
    st.markdown(html, unsafe_allow_html=True)

