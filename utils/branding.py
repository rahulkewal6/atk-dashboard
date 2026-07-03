import streamlit as st
import os

ORANGE = "#FF6600"
DARK_BG = "#0E1117"
CARD_BG = "#1A1A1A"

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


def inject_css():
    """Inject ATK brand CSS — light content, dark sidebar, orange accents."""
    st.markdown(
        """
        <style>
        /* ── Metric labels → orange, values dark ── */
        [data-testid="stMetricLabel"] p {
            color: #FF6600 !important;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] { color: #1A1D23 !important; }
        [data-testid="stMetricDelta"] { color: #BA7517 !important; }

        /* ── Headings → dark, clean ── */
        h1 { font-weight: 700 !important; letter-spacing: -0.02em; color: #1A1D23 !important; }
        h2, h3 { font-weight: 600 !important; letter-spacing: -0.01em; color: #1A1D23 !important; }
        html, body, [data-testid="stAppViewContainer"] * { -webkit-font-smoothing: antialiased; }

        /* ── Sidebar → dark ── */
        [data-testid="stSidebar"] {
            background-color: #16181D !important;
            border-right: 1px solid #22242B;
        }
        [data-testid="stSidebar"] * { color: #C9CCD3; }
        [data-testid="stSidebarNav"] a { color: #C9CCD3 !important; }
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNav"] a[aria-selected="true"] {
            color: #FF7D2B !important;
            font-weight: 600;
        }

        /* ── Primary + submit buttons → orange ── */
        .stButton > button,
        .stFormSubmitButton > button {
            background-color: #FF6600 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover { background-color: #E65C00 !important; }

        /* ── Dataframe borders ── */
        [data-testid="stDataFrame"] > div {
            border: 1px solid #E6E8EC !important;
            border-radius: 8px;
        }

        /* ── Horizontal rule ── */
        hr { border-color: #E6E8EC !important; opacity: 1; }

        /* ── Progress bars ── */
        .stProgress > div > div > div { background-color: #FF6600 !important; }

        /* ── Top header bar ── */
        header[data-testid="stHeader"] { background-color: transparent !important; }

        /* ── Warning / info boxes ── */
        [data-testid="stAlert"] { border-left: 4px solid #FF6600 !important; }

        /* ════════ Cards & components (light) ════════ */

        /* Bordered containers → white cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1px solid #E6E8EC !important;
            background: #FFFFFF;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }
        /* Sidebar containers stay dark */
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: #22242B; border-color: #2E313A !important; box-shadow: none;
        }

        /* Expanders → white rounded cards */
        [data-testid="stExpander"] {
            border: 1px solid #E6E8EC !important;
            border-radius: 12px !important;
            background: #FFFFFF;
            margin-bottom: 6px;
        }
        [data-testid="stExpander"] summary {
            border-left: none !important;
            padding: 10px 14px !important;
            font-weight: 600;
        }
        [data-testid="stExpander"] summary:hover { color: #FF6600 !important; }

        /* Popover trigger → quiet outline button */
        [data-testid="stPopover"] > div > button,
        [data-testid="stPopover"] button[data-testid^="stPopoverButton"] {
            background: #FFFFFF !important;
            color: #4B5563 !important;
            border: 1px solid #D7DAE0 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        [data-testid="stPopover"] > div > button:hover {
            border-color: #FF6600 !important;
            color: #FF6600 !important;
            background: rgba(255,102,0,0.06) !important;
        }

        /* Inputs → rounded */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stDateInput"] input,
        [data-testid="stSelectbox"] > div > div { border-radius: 8px !important; }

        /* Lead card header */
        .atk-lead-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 4px 0; }
        .atk-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; flex: none; }
        .atk-num {
            color: #9AA0A6; font-size: 0.82rem; font-weight: 700;
            font-variant-numeric: tabular-nums; min-width: 28px;
        }
        .atk-company { font-size: 1.05rem; font-weight: 600; color: #1A1D23; }
        .atk-exh { color: #6B7280; font-size: 0.84rem; font-weight: 500; }
        .atk-pill {
            padding: 3px 12px; border-radius: 999px;
            font-size: 0.74rem; font-weight: 600; white-space: nowrap;
        }

        /* Clickable stat-card buttons on the Leads page (light) */
        .st-key-stat_red button, .st-key-stat_design_prog button,
        .st-key-stat_quote_prog button, .st-key-stat_design_client button,
        .st-key-stat_quote_client button, .st-key-stat_won button {
            background: #FFFFFF !important;
            border: 1px solid #E6E8EC !important;
            border-radius: 12px !important;
            padding: 12px 6px !important;
            font-size: 0.86rem !important;
            font-weight: 700 !important;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
            white-space: normal !important;
            line-height: 1.25 !important;
        }
        .st-key-stat_red button           { border-top: 3px solid #E24B4A !important; color: #A32D2D !important; }
        .st-key-stat_design_prog button   { border-top: 3px solid #EF9F27 !important; color: #854F0B !important; }
        .st-key-stat_quote_prog button    { border-top: 3px solid #D85A30 !important; color: #993C1D !important; }
        .st-key-stat_design_client button { border-top: 3px solid #639922 !important; color: #3B6D11 !important; }
        .st-key-stat_quote_client button  { border-top: 3px solid #378ADD !important; color: #185FA5 !important; }
        .st-key-stat_won button           { border-top: 3px solid #639922 !important; color: #3B6D11 !important; }
        .st-key-stat_red button:hover           { background: #FCEBEB !important; }
        .st-key-stat_design_prog button:hover   { background: #FAEEDA !important; }
        .st-key-stat_quote_prog button:hover    { background: #FAECE7 !important; }
        .st-key-stat_design_client button:hover,
        .st-key-stat_won button:hover           { background: #EAF3DE !important; }
        .st-key-stat_quote_client button:hover  { background: #E6F1FB !important; }

        /* Compact lead rows (containers keyed lead_*) */
        [class*="st-key-lead_"] {
            padding: 6px 14px !important;
        }
        [class*="st-key-lead_"] [data-testid="stVerticalBlock"] {
            gap: 0.3rem !important;
        }
        [class*="st-key-lead_"] [data-testid="stExpander"] {
            border: none !important;
            background: transparent;
            margin: 0;
        }
        [class*="st-key-lead_"] [data-testid="stExpander"] summary {
            padding: 2px 0 !important;
            font-size: 0.78rem;
            color: #8A8F98;
        }

        /* Filter pills → chip look */
        [data-testid="stPills"] button {
            border-radius: 999px !important;
            font-size: 0.8rem !important;
        }
        [data-testid="stPills"] button[kind="pillsActive"],
        [data-testid="stPills"] button[aria-checked="true"] {
            background: #FF6600 !important;
            color: #fff !important;
            border-color: #FF6600 !important;
        }

        /* Status summary tiles */
        .atk-stats { display: flex; gap: 12px; flex-wrap: wrap; margin: 4px 0 14px; }
        .atk-stat {
            flex: 1; min-width: 130px; border-radius: 12px; padding: 12px 16px;
            border: 1px solid #E6E8EC; background: #FFFFFF;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }
        .atk-stat .n { font-size: 1.5rem; font-weight: 800; line-height: 1.1; }
        .atk-stat .l {
            font-size: 0.76rem; color: #6B7280; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.04em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_logo():
    """Show ATK logo in sidebar if logo.png exists in assets/, else text fallback."""
    if os.path.exists(_LOGO_PATH):
        st.sidebar.image(_LOGO_PATH, use_container_width=True)
    else:
        st.sidebar.markdown(
            "<div style='text-align:center; padding:12px 0;'>"
            "<span style='color:#FF6600; font-size:1.4rem; font-weight:700;'>ATK</span>"
            "<span style='color:#FFFFFF; font-size:1.4rem;'> Exhibitions</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.sidebar.markdown(
        "<hr style='border-color:#FF6600; opacity:0.3; margin:4px 0 12px;'>",
        unsafe_allow_html=True,
    )
