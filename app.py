import streamlit as st
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage

from interviewer import (
    new_interview,
    delete_interview,
    get_active,
    ask_question,
    check_timer
)

from support_chatbot import init_support_chat, render_support_chat

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI Professional Interviewer",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main content styling */
    .main-content {
        padding: 20px;
    }
    
    /* Floating chat container */
    .floating-chat {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 350px;
        max-height: 600px;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    /* Chat header */
    .chat-header {
        background: #4F46E5;
        color: white;
        padding: 12px 16px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Chat body */
    .chat-body {
        flex: 1;
        padding: 16px;
        overflow-y: auto;
        max-height: 400px;
    }
    
    /* Chat message styling */
    .chat-message {
        margin: 8px 0;
        padding: 10px;
        border-radius: 8px;
        max-width: 80%;
    }
    
    .user-message {
        background: #4F46E5;
        color: white;
        margin-left: auto;
    }
    
    .assistant-message {
        background: #f0f0f0;
        color: #333;
        margin-right: auto;
    }
    
    /* Close button */
    .close-btn {
        background: transparent;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 18px;
        padding: 0;
        margin: 0;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        padding: 20px 10px;
    }
    
    /* Interview container */
    .interview-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Timer styling */
    .timer {
        background: #4F46E5;
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        margin: 10px 0;
    }
    
    /* Hide element */
    .hidden {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STORAGE --------------------
if "interviews" not in st.session_state:
    st.session_state.interviews = {}

if "active_interview_id" not in st.session_state:
    st.session_state.active_interview_id = None

# Initialize support chatbot memory
init_support_chat(st.session_state)

if "show_support_chat" not in st.session_state:
    st.session_state.show_support_chat = False

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.title("📋 Interviews")
    
    # New Interview Button
    if st.button("➕ Start New Interview", use_container_width=True, type="primary"):
        new_interview(st.session_state)
    
    st.divider()
    
    # Interview List
    if st.session_state.interviews:
        st.subheader("Your Interviews")
        for iid, interview in st.session_state.interviews.copy().items():
            title = interview.get("company") or "New Interview"
            role = interview.get("role") or "No role specified"
            
            cols = st.columns([3, 1])
            
            with cols[0]:
                if st.button(f"**{title}**\n{role}", key=f"open_{iid}", use_container_width=True):
                    st.session_state.active_interview_id = iid
                    st.rerun()
            
            with cols[1]:
                if st.button("🗑️", key=f"del_{iid}", help=f"Delete {title}"):
                    delete_interview(st.session_state, iid)
                    if st.session_state.active_interview_id == iid:
                        st.session_state.active_interview_id = None
                    st.rerun()
    else:
        st.info("No interviews yet. Start a new one!")
    
    st.divider()
    
    # Support Chat Toggle - Only show if no active interview or interview is in setup stage
    interview = get_active(st.session_state)
    should_show_chat_toggle = True
    
    if interview and interview["stage"] == "interview":
        should_show_chat_toggle = False
    
    if should_show_chat_toggle:
        chat_status = "💬 Hide Support Chat" if st.session_state.show_support_chat else "💬 Show Support Chat"
        if st.button(chat_status, use_container_width=True, type="secondary"):
            st.session_state.show_support_chat = not st.session_state.show_support_chat
            st.rerun()
    else:
        # Show disabled state during active interview
        st.info("Support chat disabled during active interview")
    
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- FLOATING SUPPORT CHAT --------------------
# Only show chat if:
# 1. show_support_chat is True
# 2. There's no active interview OR interview is in setup stage
interview = get_active(st.session_state)
show_chat_condition = st.session_state.show_support_chat

if interview and interview["stage"] == "interview":
    show_chat_condition = False  # Hide chat during active interview

if show_chat_condition:
    st.markdown("""
    <div class="floating-chat">
        <div class="chat-header">
            <span>🤖 Support AI chatbot</span>
            <button class="close-btn" onclick="document.querySelector('.floating-chat').style.display='none'">×</button>
        </div>
    """, unsafe_allow_html=True)
    
    # Create a container for the chat messages
    chat_container = st.container(height=400)
    
    # Render chat inside the container
    with chat_container:
        render_support_chat(st.session_state)
    
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- MAIN CONTENT AREA --------------------
st.markdown('<div class="main-content">', unsafe_allow_html=True)

interview = get_active(st.session_state)

# -------------------- NO ACTIVE INTERVIEW --------------------
if not interview:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h1>🤖 AI Professional Interviewer</h1>
            <p style='font-size: 18px; color: #666; margin: 30px 0;'>
                Prepare for your next job interview with our AI-powered interviewer.
                Get realistic practice and instant feedback.
            </p>
            <div style='margin: 40px 0;'>
                <h3>🚀 How it works:</h3>
                <ol style='text-align: left; display: inline-block; margin: 20px auto;'>
                    <li>Click <strong>"Start New Interview"</strong> in the sidebar</li>
                    <li>Fill in your interview details</li>
                    <li>Practice for 15 minutes with our AI interviewer</li>
                    <li>Receive instant feedback</li>
                </ol>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

memory = interview["memory"]

# -------------------- SETUP STAGE --------------------
if interview["stage"] == "setup":
    st.title(" Interview Setup")
    
    with st.container():
        st.markdown('<div class="interview-container">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(" Candidate Information")
            with st.form(key="setup_form"):
                candidate_name = st.text_input(
                    "**Full Name**",
                    value=interview.get("candidate_name", ""),
                    placeholder="Enter your full name"
                )
                
                company = st.text_input(
                    "**Company Name**",
                    value=interview.get("company", ""),
                    placeholder="Enter company name"
                )
                
                role = st.text_input(
                    "**Position / Role**",
                    value=interview.get("role", ""),
                    placeholder="Enter the role you're applying for"
                )
                
                st.divider()
                
                interview_types = ["Technical", "Behavioral", "Situational", "Mixed"]
                current_type = interview.get("type") or "Technical"
                index = interview_types.index(current_type) if current_type in interview_types else 0
                
                interview_type = st.selectbox(
                    "**Interview Type**",
                    interview_types,
                    index=index,
                    help="Select the type of interview you want to practice"
                )
                
                skills = st.text_area(
                    "**Relevant Skills**",
                    value=interview.get("skills", ""),
                    placeholder="List your skills (comma-separated)\nExample: Python, Machine Learning, Data Analysis",
                    height=100
                )
                
                submitted = st.form_submit_button(" Start Interview", type="primary", use_container_width=True)
                
                if submitted:
                    if not candidate_name or not company or not role:
                        st.error("Please fill in all required fields: Name, Company, and Role")
                    else:
                        interview.update({
                            "candidate_name": candidate_name,
                            "company": company,
                            "role": role,
                            "type": interview_type,
                            "skills": skills,
                            "stage": "interview",
                            "start_time": datetime.now()
                        })
                        
                        # Automatically hide the support chat when interview starts
                        st.session_state.show_support_chat = False
                        
                        interview_desc = (
                            "This interview will include technical, behavioral, and situational questions."
                            if interview_type.lower() == "mixed"
                            else f"This is a {interview_type.lower()} interview."
                        )
                        
                        greeting = (
                            f"Hello {candidate_name}, welcome to the {interview_type.lower()} interview "
                            f"for the {role} position at {company}. "
                            f"I'm your AI interviewer today. "
                            f"{interview_desc} "
                            f"We will focus on your skills in {skills if skills else 'Python, AI, and ML'}. "
                            f"The interview will last 15 minutes. "
                            f"Are you ready to begin?"
                        )
                        
                        memory.chat_memory.add_ai_message(greeting)
                        st.rerun()
        
        with col2:
            st.subheader(" Preview")
            st.info("Review your information before starting:")
            
            info_data = {
                "Candidate": candidate_name or "Not set",
                "Company": company or "Not set",
                "Role": role or "Not set",
                "Interview Type": interview_type,
                "Skills": skills or "Not specified"
            }
            
            for key, value in info_data.items():
                st.markdown(f"**{key}:** {value}")
            
            if candidate_name and company and role:
                st.success(" All required fields are filled!")
            else:
                st.warning("Please fill all required fields")
        
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- INTERVIEW STAGE --------------------
elif interview["stage"] == "interview":
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(f"🎤 {interview['role']} Interview")
        st.markdown(f"**Company:** {interview['company']} | **Type:** {interview['type']}")
    
    with col2:
        # Timer
        if interview.get("start_time"):
            elapsed = datetime.now() - interview["start_time"]
            remaining = timedelta(minutes=15) - elapsed
            
            if remaining.total_seconds() > 0:
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                st.markdown(f'<div class="timer">⏱️ Time: {minutes}:{seconds:02d}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown('<div class="timer" style="background: #dc3545;">⏱️ Time\'s up!</div>', 
                           unsafe_allow_html=True)
    
    st.divider()
    
    # Chat messages container
    chat_container = st.container(height=500)
    
    with chat_container:
        for msg in memory.chat_memory.messages:
            role_type = "user" if isinstance(msg, HumanMessage) else "assistant"
            
            if role_type == "user":
                st.markdown(f"""
                <div style='text-align: right; margin: 10px 0;'>
                    <div style='background: #4F46E5; color: white; padding: 12px; 
                         border-radius: 15px 15px 0 15px; display: inline-block; max-width: 80%;'>
                        {msg.content}
                    </div>
                    <div style='font-size: 12px; color: #666; text-align: right; padding: 2px 10px;'>
                        👤 You
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align: left; margin: 10px 0;'>
                    <div style='background: #f0f0f0; color: #333; padding: 12px; 
                         border-radius: 15px 15px 15px 0; display: inline-block; max-width: 80%;'>
                        {msg.content}
                    </div>
                    <div style='font-size: 12px; color: #666; text-align: left; padding: 2px 10px;'>
                        🤖 AI Interviewer
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input at bottom
    if check_timer(interview):
        interview["stage"] = "feedback"
        st.error("⏰ The interview time has ended. Moving to feedback...")
        st.rerun()
    
    # Input area
    col_input, col_button = st.columns([5, 1])
    
    with col_input:
        user_input = st.chat_input("Type your answer here...", key="interview_input")
    
    with col_button:
        if st.button("Ask Support", use_container_width=True, type="secondary"):
            st.info("Support chat is disabled during active interviews. Please complete or end the interview first.")
    
    if user_input:
        memory.chat_memory.add_user_message(user_input)
        
        if any(x in user_input.lower() for x in ["stop", "exit", "finish", "end interview"]):
            interview["stage"] = "feedback"
            st.rerun()
        else:
            ask_question(interview, user_input)
        st.rerun()

# -------------------- FEEDBACK STAGE --------------------
elif interview["stage"] == "feedback":
    st.title("📊 Interview Feedback")
    st.markdown('<div class="interview-container">', unsafe_allow_html=True)
    
    with st.spinner("Generating your feedback..."):
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model="mistral:latest")
        
        history = memory.load_memory_variables({})["history"]
        
        feedback_prompt = (
            f"Please provide professional interview feedback for the candidate {interview['candidate_name']} "
            f"who interviewed for {interview['role']} at {interview['company']}. "
            f"The interview was {interview['type']} type focusing on {interview['skills']}. "
            "Provide specific feedback on: strengths, areas for improvement, and overall performance. "
            "Format it nicely with clear sections and bullet points."
        )
        
        feedback = llm.invoke(
            history + [HumanMessage(content=feedback_prompt)]
        )
    
    # Display feedback in a nice format
    st.markdown("### 🎯 Overall Performance")
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ **Strengths**")
        st.success(feedback.content.split("Strengths:")[1].split("Areas for Improvement:")[0] 
                  if "Strengths:" in feedback.content else "Good overall performance")
    
    with col2:
        st.markdown("### 📝 **Areas for Improvement**")
        st.warning(feedback.content.split("Areas for Improvement:")[1].split("Overall Performance:")[0] 
                  if "Areas for Improvement:" in feedback.content else "Keep practicing!")
    
    st.divider()
    
    st.markdown("### 📋 **Detailed Feedback**")
    st.markdown(feedback.content)
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 Start New Interview", use_container_width=True):
            new_interview(st.session_state)
            st.rerun()
    
    with col2:
        if st.button("📥 Download Feedback", use_container_width=True):
            # Create a downloadable text file
            feedback_text = f"""
            Interview Feedback Report
            =========================
            
            Candidate: {interview['candidate_name']}
            Position: {interview['role']}
            Company: {interview['company']}
            Interview Type: {interview['type']}
            Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            FEEDBACK:
            {feedback.content}
            """
            
            st.download_button(
                label="Download Now",
                data=feedback_text,
                file_name=f"interview_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col3:
        if st.button("🗑️ Delete Interview", use_container_width=True, type="secondary"):
            delete_interview(st.session_state, st.session_state.active_interview_id)
            st.session_state.active_interview_id = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)