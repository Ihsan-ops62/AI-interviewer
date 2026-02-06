import streamlit as st

def inject_css():
    st.markdown("""
    <style>
        .stChatMessage { padding: 12px; border-radius: 8px; }
        .stButton button { width: 100%; }
        .title { font-size: 28px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)
