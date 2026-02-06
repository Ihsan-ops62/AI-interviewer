import streamlit as st
from langchain_ollama import ChatOllama
from interviewer import new_interview, get_active  

# support chat initialization
def init_support_chat(session_state):
    if "support_messages" not in session_state:
        session_state.support_messages = []

    if "support_processing" not in session_state:
        session_state.support_processing = False


# support chat rendering
def render_support_chat(session_state):
    """
    Support chatbot that behaves like a customer support agent.
    Can act as an agent to start the interview if explicitly requested.
    """

    st.subheader("Support Chatbot")

    chat_container = st.container()

    # Display previous messages
    for msg in session_state.support_messages:
        role = msg["role"]
        align = "right" if role == "user" else "left"
        color = "#DCF8C6" if role == "user" else "#F5F5F5"

        chat_container.markdown(
            f"<div style='background:{color};padding:8px;border-radius:8px;"
            f"margin:4px 0;text-align:{align}'>"
            f"{msg['content']}</div>",
            unsafe_allow_html=True
        )

    # user input
    user_input = st.chat_input("Ask for any query related to the AI Professional Interviewer platform.")

    if user_input and not session_state.support_processing:
        session_state.support_processing = True

        # Save user message
        session_state.support_messages.append({
            "role": "user",
            "content": user_input
        })

        llm = ChatOllama(
            model="mistral:latest",
            temperature=0.4
        )

        # system prompt
        system_prompt = """
You are a professional human support agent for an AI interview platform.

Rules:
- Greet the user respectfully when they start a chat.
- Only answer questions about the AI Professional Interviewer platform features, setup, and usage.
- Do NOT answer questions outside the scope of the platform.
- if someone asks questions out of scope respond with "I'm sorry, but I can only assist with questions related to the AI Professional Interviewer platform." and do not provide any additional information.
- If asked "Who are you?", respond: "I am the AI Professional Interviewer platform support chatbot."
- If asked "How are you?", respond: "I pretty good, thanks for asking! How can I assist you today?"
- Help users with queries about the platform clearly and concisely.
- Keep answers short, to the point, and avoid extra explanations.
- Do not provide extra information unless specifically asked.
- Answer only what the user asks.
- Keep responses short, clear, and human-like.
- Do not proactively suggest starting an interview.
- Only trigger interview start if the user explicitly requests it and don't give explanations about the interview process unless asked.
- Provide guidance about the platform features when asked.
- Avoid generic overviews or repeated suggestions.
- Be friendly and approachable.
- Respond in plain text. Do not use HTML or markdown.
- Respect the app behavior:
    - Interviews last exactly 15 minutes
    - Setup, interview, feedback stages exist
    - New interviews can be started via user request
"""

        # Build conversation for LLM
        conversation = system_prompt.strip() + "\n\n"
        for msg in session_state.support_messages:
            conversation += f"{msg['role'].upper()}: {msg['content']}\n"

        # Call LLM
        with st.spinner("Support is responding..."):
            response = llm.invoke(conversation)

        assistant_text = response.content.strip()

        # Save assistant response
        session_state.support_messages.append({
            "role": "assistant",
            "content": assistant_text
        })

        # agent action: start interview
        trigger_keywords = ["start interview", "begin interview", "initiate interview"]
        if any(keyword in user_input.lower() for keyword in trigger_keywords):
            active = get_active(st.session_state)
            if not active:
                # Create a new interview
                new_interview(st.session_state)

                # Automatically set it as active so main app goes to setup
                st.session_state.active_interview_id = st.session_state.active_interview_id

                session_state.support_messages.append({
                    "role": "assistant",
                    "content": "Interview has been started successfully. You can now proceed with the setup."
                })
            else:
                session_state.support_messages.append({
                    "role": "assistant",
                    "content": "An interview is already active. You can continue with it."
                })

        session_state.support_processing = False
        st.rerun()