import streamlit as st
from dotenv import load_dotenv
import os
import uuid

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.utilities import SerpAPIWrapper

# load env 
load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    st.error("SERPAPI_API_KEY not found in .env")
    st.stop()

st.set_page_config(page_title="AI Professional Interviewer", page_icon="🤖")

# session state
if "interviews" not in st.session_state:
    st.session_state.interviews = {}

if "active_interview_id" not in st.session_state:
    st.session_state.active_interview_id = None


# helpers
def create_interview():
    iid = str(uuid.uuid4())
    st.session_state.interviews[iid] = {
        "memory": ConversationBufferMemory(return_messages=True),
        "stage": "setup",
        "company": "",
        "role": "",
        "type": "",
        "web_context": ""
    }
    st.session_state.active_interview_id = iid
    st.rerun()

def delete_interview(iid):
    del st.session_state.interviews[iid]
    st.session_state.active_interview_id = None
    st.rerun()

def active_interview():
    return st.session_state.interviews[st.session_state.active_interview_id]


# websearching
def fetch_web_context(company, role, interview_type):
    with st.spinner("Searching..."):
        search = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)
        query = (
            f"{company} {role} {interview_type} interview questions "
            f"real candidate experience"
        )
        try:
            result = search.run(query)
            return result[:3500]
        except Exception:
            return ""
        

# chain main logic
def interviewer_chain(web_context, company, role, interview_type):
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            f"""
You are a senior professional human interviewer.

Company: {company}
Role: {role}
Interview Type: {interview_type}

Web Interview Research Context:
{web_context}

Behavior Rules:
- Ask EXACTLY ONE question at a time
- Sound professional, natural, and human
- Question sould be like as human interviewer
- Never ask multiple questions in one message
- Wait for the candidate's response before continuing
- Each new question must logically follow the last answer
- Gradually increase difficulty
- Stop ONLY if the user says: stop, exit, finish, enough
"""
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    llm = ChatOllama(model="deepseek-r1:1.5b")
    return prompt | llm


# Ask next question
def ask_next_question(interview, user_answer=""):
    chain = interviewer_chain(
        interview["web_context"],
        interview["company"],
        interview["role"],
        interview["type"]
    )

    history = interview["memory"].load_memory_variables({})["history"]
    container = st.empty()
    response = ""

    with st.spinner("preparing next question..."):
        for chunk in chain.stream({
            "input": user_answer,
            "history": history
        }):
            response += chunk.content
            container.markdown(response + "▌")

    container.markdown(response)
    interview["memory"].chat_memory.add_ai_message(response)


# app sidebar
with st.sidebar:
    st.title(" Interviews")

    if st.button("➕ Create Interview"):
        create_interview()

    st.divider()

    for iid, interview in st.session_state.interviews.items():
        label = interview["company"] or "New Interview"
        cols = st.columns([4, 1])

        if cols[0].button(label, key=f"open_{iid}"):
            st.session_state.active_interview_id = iid
            st.rerun()

        if cols[1].button("🗑", key=f"delete_{iid}"):
            delete_interview(iid)


# main UI
st.title("AI Professional Interviewer",text_alignment="center")

if not st.session_state.active_interview_id:
    st.info("Start new interview")
    st.stop()

interview = active_interview()
memory = interview["memory"]

# setup
if interview["stage"] == "setup":

    company = st.text_input("Company Name")
    role = st.text_input("Role / Position")
    interview_type = st.selectbox("Interview Type", ["Technical", "Behavioral", "HR"])

    if st.button("Start Interview"):
        if not company or not role:
            st.warning("Please fill all fields.")
        else:
            interview["company"] = company
            interview["role"] = role
            interview["type"] = interview_type

            interview["web_context"] = fetch_web_context(company, role, interview_type)

            greeting = (
                f"Good day. Thank you for taking the time to interview with us for the "
                f"{role} position at {company}. "
                f"To begin, could you please introduce yourself and summarize your "
                f"professional background?"
            )

            memory.chat_memory.add_ai_message(greeting)
            interview["stage"] = "interview"
            st.rerun()

# interview loop
elif interview["stage"] == "interview":

    for msg in memory.chat_memory.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    if user_input := st.chat_input("Your answer..."):

        with st.chat_message("user"):
            st.markdown(user_input)

        memory.chat_memory.add_user_message(user_input)

        # User stoping interviews detection
        if any(x in user_input.lower() for x in ["stop", "exit", "finish", "enough", "quit"]):
            interview["stage"] = "feedback"
            st.rerun()

        # Generate next interview question
        ask_next_question(interview, user_input)


# feedback

elif interview["stage"] == "feedback":

    st.subheader(" Interview Feedback")

    llm = ChatOllama(model="deepseek-r1:1.5b")
    history = memory.load_memory_variables({})["history"]

    feedback = llm.invoke(
        history + [
            HumanMessage(
                content="Provide a professional interview evaluation. Include strengths, weaknesses, communication skills, and improvement suggestions."
            )
        ]
    )

    st.success(feedback.content)
