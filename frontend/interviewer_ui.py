import streamlit as st
from api import (
    create_interview, get_interviews,
    start_interview, interview_chat, get_chat
)

def interview_page(token):
    st.subheader("🎤 Interviews")

    interviews = get_interviews(token) or []

    with st.expander("➕ Create Interview"):
        data = {
            "candidate_name": st.text_input("Candidate Name"),
            "company": st.text_input("Company"),
            "role": st.text_input("Role"),
            "interview_type": st.selectbox(
                "Type", ["Technical", "Behavioral", "HR"]
            ),
            "skills": st.text_area("Skills")
        }
        if st.button("Create"):
            create_interview(token, data)
            st.rerun()

    if not interviews:
        st.info("No interviews yet.")
        return

    interview = st.selectbox(
        "Select Interview",
        interviews,
        format_func=lambda i: f"{i['company']} - {i['role']}"
    )

    if interview["stage"] == "setup":
        if st.button("▶ Start Interview"):
            start_interview(token, interview["interview_id"])
            st.rerun()

    chat = get_chat(token, interview["interview_id"]) or []

    for msg in chat:
        st.chat_message(msg["role"]).write(msg["message"])

    prompt = st.chat_input("Your answer...")
    if prompt:
        res = interview_chat(token, interview["interview_id"], prompt)
        st.chat_message("assistant").write(res["message"])
        st.rerun()
