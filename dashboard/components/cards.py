import streamlit as st

def render_kpi_card(title: str, value_str: str, subtext: str = "", delta_str: str = None, color_accent: str = "#10b981"):
    """Render a styled KPI metric card with rich visual styling."""
    delta_html = f'<div style="color: {color_accent}; font-size: 0.85rem; margin-top: 4px;">{delta_str}</div>' if delta_str else ""
    sub_html = f'<div style="color: #9ca3af; font-size: 0.8rem; margin-top: 4px;">{subtext}</div>' if subtext else '<div style="height: 16px;"></div>'

    card_html = (
        f'<div style="background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); '
        f'border-left: 4px solid {color_accent}; border-radius: 8px; padding: 16px; margin-bottom: 12px; '
        f'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">'
        f'<div style="color: #cbd5e1; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>'
        f'<div style="color: #f8fafc; font-size: 1.7rem; font-weight: 700; margin-top: 6px;">{value_str}</div>'
        f'{delta_html}'
        f'{sub_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

def render_source_provenance_footer(dataset_name: str, url: str, latest_period: str):
    """Render data provenance banner at the bottom of pages."""
    st.markdown("---")
    footer_html = (
        f'<div style="background: rgba(15, 23, 42, 0.8); padding: 12px 18px; border-radius: 6px; border: 1px solid #334155; font-size: 0.8rem; color: #94a3b8;">'
        f'<strong>Official Data Provenance:</strong> Sourced directly from Eurostat Dissemination API '
        f'(Dataset: <code>{dataset_name}</code>) | '
        f'<strong>Latest Available Data:</strong> <span style="color: #38bdf8; font-weight: 600;">{latest_period}</span> | '
        f'<a href="{url}" target="_blank" style="color: #38bdf8; text-decoration: none;">View Official Eurostat Source ↗</a>'
        f'</div>'
    )
    st.markdown(footer_html, unsafe_allow_html=True)
