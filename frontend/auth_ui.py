import streamlit as st
from api import login, register

def auth_page():
    st.markdown("<div class='title'>AI Professional Interviewer</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = login({"username": u, "password": p})
            if "token" in res:
                st.session_state.token = res["token"]
                st.session_state.user = res["user"]
                st.rerun()
            else:
                st.error(res.get("detail", "Login failed"))

    with tab2:
        u = st.text_input("Username", key="ru")
        e = st.text_input("Email")
        f = st.text_input("Full name")
        p = st.text_input("Password", type="password", key="rp")
        if st.button("Register"):
            res = register({
                "username": u,
                "email": e,
                "full_name": f,
                "password": p
            })
            if "token" in res:
                st.success("Account created. Please login.")
            else:
                st.error(res.get("detail", "Registration failed"))
