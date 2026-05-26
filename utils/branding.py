import streamlit as st
import os

ORANGE = "#FF6600"
DARK_BG = "#0E1117"
CARD_BG = "#1A1A1A"

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


def inject_css():
    """Inject ATK brand CSS — orange + black dark mode."""
    st.markdown(
        """
        <style>
        /* ── Metric labels → orange ── */
        [data-testid="stMetricLabel"] p {
            color: #FF6600 !important;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
        }
        [data-testid="stMetricDelta"] {
            color: #FF9955 !important;
        }

        /* ── Section headings → orange ── */
        h2, h3 { color: #FF6600 !important; }

        /* ── Sidebar → near-black ── */
        [data-testid="stSidebar"] {
            background-color: #111111 !important;
            border-right: 2px solid #FF6600;
        }
        [data-testid="stSidebarNav"] a {
            color: #DDDDDD !important;
        }
        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNav"] a[aria-selected="true"] {
            color: #FF6600 !important;
            font-weight: 700;
        }

        /* ── Primary + submit buttons → orange ── */
        .stButton > button,
        .stFormSubmitButton > button {
            background-color: #FF6600 !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background-color: #CC5200 !important;
        }

        /* ── Expanders → orange left border ── */
        details summary {
            border-left: 3px solid #FF6600;
            padding-left: 8px;
        }

        /* ── Dataframe borders ── */
        [data-testid="stDataFrame"] > div {
            border: 1px solid #333333 !important;
            border-radius: 6px;
        }

        /* ── Horizontal rule ── */
        hr { border-color: #FF6600 !important; opacity: 0.25; }

        /* ── Progress bars ── */
        .stProgress > div > div > div {
            background-color: #FF6600 !important;
        }

        /* ── Top header bar ── */
        header[data-testid="stHeader"] {
            background-color: #0E1117 !important;
            border-bottom: 2px solid #FF6600;
        }

        /* ── Metric card background ── */
        [data-testid="metric-container"] {
            background-color: #1A1A1A;
            border: 1px solid #333333;
            border-radius: 8px;
            padding: 12px 16px !important;
        }

        /* ── Warning / info boxes ── */
        [data-testid="stAlert"] {
            border-left: 4px solid #FF6600 !important;
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
