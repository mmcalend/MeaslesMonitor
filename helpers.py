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
