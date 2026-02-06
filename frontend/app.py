import streamlit as st
from styles import inject_css
from auth_ui import auth_page
from interviewer_ui import interview_page
from support_ui import support_page

st.set_page_config(
    page_title="AI Interviewer",
    page_icon="🎤",
    layout="wide"
)

inject_css()

if "token" not in st.session_state:
    auth_page()
    st.stop()

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Interviews", "Support", "Logout"]
)

if page == "Logout":
    st.session_state.clear()
    st.rerun()

elif page == "Interviews":
    interview_page(st.session_state.token)

elif page == "Support":
    support_page(st.session_state.token)
