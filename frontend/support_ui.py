import streamlit as st
from api import support_chat, get_support

def support_page(token):
    st.subheader("🆘 Support")

    history = get_support(token) or []
    for msg in history:
        st.chat_message(msg["role"]).write(msg["message"])

    text = st.chat_input("Ask support...")
    if text:
        res = support_chat(token, text)
        st.chat_message("assistant").write(res["message"])
        st.rerun()
