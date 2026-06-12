import streamlit as st

st.set_page_config(
    page_title="ATK Sales Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("home.py",                title="Home",       icon="🏠", default=True),
    st.Page("pages/0_Tasks.py",       title="Tasks",      icon="📋"),
    st.Page("pages/1_Leads.py",       title="Leads",      icon="🎯"),
    st.Page("pages/2_Follow_Ups.py",  title="Follow Ups", icon="📅"),
    st.Page("pages/3_Sequences.py",   title="Sequences",  icon="✉️"),
    st.Page("pages/4_Reports.py",     title="Reports",    icon="📊"),
    st.Page("pages/5_Calendar.py",    title="Calendar",   icon="🗓️"),
    st.Page("pages/6_Database.py",    title="Database",   icon="🗂️"),
    st.Page("pages/7_List_Maker.py",  title="List Maker", icon="🕷️"),
])
pg.run()
