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

        /* ════════ Modern UI layer ════════ */

        /* Cleaner system font + rendering */
        html, body, [data-testid="stAppViewContainer"] * {
            -webkit-font-smoothing: antialiased;
        }
        h1 { font-weight: 800 !important; letter-spacing: -0.02em; }
        h2, h3 { font-weight: 700 !important; letter-spacing: -0.01em; }

        /* Bordered containers → soft cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border: 1px solid #2A2D34 !important;
            background: #14171D;
            box-shadow: 0 2px 10px rgba(0,0,0,0.25);
        }

        /* Expanders → rounded cards, no harsh borders */
        [data-testid="stExpander"] {
            border: 1px solid #2A2D34 !important;
            border-radius: 12px !important;
            background: #14171D;
            margin-bottom: 6px;
        }
        [data-testid="stExpander"] summary {
            border-left: none !important;
            padding: 10px 14px !important;
            font-weight: 600;
        }
        [data-testid="stExpander"] summary:hover {
            color: #FF6600 !important;
        }

        /* Popover trigger → quiet outline button (not orange) */
        [data-testid="stPopover"] > div > button,
        [data-testid="stPopover"] button[data-testid^="stPopoverButton"] {
            background: transparent !important;
            color: #CCCCCC !important;
            border: 1px solid #3A3E46 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        [data-testid="stPopover"] > div > button:hover {
            border-color: #FF6600 !important;
            color: #FF6600 !important;
            background: rgba(255,102,0,0.08) !important;
        }

        /* Inputs → rounded, subtle */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stDateInput"] input,
        [data-testid="stSelectbox"] > div > div {
            border-radius: 8px !important;
        }

        /* Lead card header */
        .atk-lead-head {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            padding: 4px 0;
        }
        .atk-dot {
            width: 11px; height: 11px;
            border-radius: 50%;
            display: inline-block;
            flex: none;
        }
        .atk-company {
            font-size: 1.08rem;
            font-weight: 700;
            color: #FFFFFF;
        }
        .atk-exh {
            color: #8A8F98;
            font-size: 0.84rem;
            font-weight: 500;
        }
        .atk-pill {
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 600;
            white-space: nowrap;
        }

        /* Status summary chips */
        .atk-stats {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin: 4px 0 14px;
        }
        .atk-stat {
            flex: 1;
            min-width: 130px;
            border-radius: 12px;
            padding: 12px 16px;
            border: 1px solid #2A2D34;
            background: #14171D;
        }
        .atk-stat .n {
            font-size: 1.5rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .atk-stat .l {
            font-size: 0.76rem;
            color: #8A8F98;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
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
