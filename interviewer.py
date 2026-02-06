import uuid
from datetime import datetime, timedelta
import streamlit as st
import os
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.utilities import SerpAPIWrapper

# Load environment variables
load_dotenv()
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    st.error("SERPAPI_API_KEY not found in .env")
    st.stop()


# interview management
def new_interview(session_state):
    interview_id = str(uuid.uuid4())
    session_state.interviews[interview_id] = {
        "id": interview_id,
        "memory": ConversationBufferMemory(return_messages=True),
        "stage": "setup",
        "candidate_name": "",
        "company": "",
        "role": "",
        "type": "",
        "skills": "",
        "start_time": None,
        "question_style": ""
    }
    session_state.active_interview_id = interview_id
    st.rerun()


def delete_interview(session_state, interview_id):
    if interview_id in session_state.interviews:
        del session_state.interviews[interview_id]
    session_state.active_interview_id = None
    st.rerun()


def get_active(session_state):
    iid = session_state.active_interview_id
    if not iid or iid not in session_state.interviews:
        return None
    return session_state.interviews[iid]


# question style building
def build_question_style(interview):
    """
    Run ONCE at interview start.
    Extracts patterns, topics, and difficulty progression.
    If web search fails, fallback to generic question style.
    """
    search = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)
    query = f"{interview['role']} interview questions {interview['skills']} {interview['type']} interview"

    try:
        raw_results = search.run(query)
        if not raw_results:
            raise ValueError("No search results")
        raw_results = raw_results[:2000]
    except Exception:
        raw_results = ""
        st.warning("⚠️ Web search failed. Using default question style.")

    llm = ChatOllama(model="mistral:latest", temperature=0.3)

    # Prompt for extracting question style
    prompt = f"""
You are analyzing interview questions for preparation.

From the text below, extract:
- Common question styles
- Typical difficulty progression
- Key technical and behavioral focus areas

DO NOT list actual questions.
Summarize patterns only.

Text:
{raw_results if raw_results else 'No search results available, use generic patterns for a human-like interview.'}
"""

    with st.spinner("Preparing interview structure..."):
        style = llm.invoke(prompt).content

    interview["question_style"] = style


# question asking
def ask_question(interview, user_answer=""):
    """
    Ask a natural, human-like follow-up question based on the candidate's answer.
    Avoid repetition and keep it engaging.
    """
    system_prompt = f"""
You are a professional, friendly human interviewer named Ihsan.
- Speak naturally and conversationally.
- Listen to the candidate's last answer and react appropriately.
- Ask ONE question at a time.
- Questions should be clear, concise, and relevant.
- Questions should be engaging and follow a natural difficulty progression.
- Encourage elaboration on examples and projects.
- Avoid repeating previous questions or apologies.
- Reference interview context but make questions sound human.
- Question should be relevant to the candidate's skills and the role.

Interview Context:
- Company: {interview['company']}
- Role: {interview['role']}
- Interview Type: {interview['type']}
- Candidate Skills: {interview['skills']}
- Reference for question style: {interview['question_style']}
"""

    # Build prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    llm = ChatOllama(model="mistral:latest", streaming=True, temperature=0.7)

    chain = prompt | llm
    history = interview["memory"].load_memory_variables({})["history"]
    question = ""

    with st.spinner("Thinking..."):
        for chunk in chain.stream({
            "input": user_answer,
            "history": history
        }):
            question += chunk.content

    # Add small human-like filler if first question
    if not user_answer:
        question = f"Hi {interview.get('candidate_name','Candidate')}, nice to meet you! Let's get started. {question}"
    else:
        question = f"Interesting, thanks for sharing! {question}"

    # Add question to memory
    interview["memory"].chat_memory.add_ai_message(question)


# check timer
def check_timer(interview):
    if not interview.get("start_time"):
        return False
    return (datetime.now() - interview["start_time"]) > timedelta(minutes=15)