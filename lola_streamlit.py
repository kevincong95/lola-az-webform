import streamlit as st
import utils

from datetime import datetime, timedelta
from langchain_core.messages import AIMessage, HumanMessage

from lola_graph import primary_graph

lola_avatar = utils.get_avatar_base64("assets/lola.png")

# Function to start a new session
def start_new_session(nextTopic, previous_topic, session_type):
    # Reset state for new session
    squads_ready = st.session_state.state["squads_ready"] or st.session_state.login_time - st.session_state.user_data["last_login"] < timedelta(days = 2) or not previous_topic
    if not squads_ready:
        with st.chat_message('assistant', avatar=f"data:image/png;base64,{lola_avatar}"):
            st.write(f"Uh-oh! Looks like your squads have fallen asleep! We'll have to wake them up with a review on {previous_topic}.")
    st.session_state.messages = []
    st.session_state.state = {
        "user_topic": nextTopic,
        "previous_topic": previous_topic,
        "messages": [],
        "session_type": session_type,
        "squads_ready": squads_ready,
        "subgraph_state": None,
        "next_step": None,
        "remaining_steps": 5,
        "user_profile": st.session_state.user_data
    }
    
    # Handle lesson sessions
    if session_type == "lesson":     
        # Prepare lesson state
        lesson_state = {
            "topic": nextTopic,
            "messages": [],
            "lesson_plan": None,
            "summary": None
        }
        st.session_state.state["subgraph_state"] = lesson_state
    # Update primary graph state with initial message and invoke it
    new_state = primary_graph.invoke(st.session_state.state)
    st.session_state.state = new_state
    
    # Preserve messages across graph calls
    if new_state.get("subgraph_state") and new_state["subgraph_state"].get("messages"):
        st.session_state.messages = utils.convert_to_streamlit_messages(new_state["subgraph_state"]["messages"])
    else:
        # Handle the initial greeting from the primary graph
        if new_state.get("message"):
            st.session_state.messages.append({"role": "assistant", "content": new_state["message"]})

def lola_main():
    if not hasattr(st.session_state, "login_time"):
        st.session_state.login_time = datetime.now()
    
    # Add sidebar with logo and user info
    with st.sidebar:
        # Display logo centered
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style='text-align: center;'>
                <img src="data:image/jpg;base64,{}" 
                     style='width: 300px; height: 300px; object-fit: contain;'/>
            </div>
            """.format(
                __import__('base64').b64encode(open("assets/FullLogo.jpg", "rb").read()).decode()
            ), unsafe_allow_html=True)
        st.markdown("---")
        
        st.info(f"Logged in as: {st.session_state.user_data['username']}")
        
        # Initialize logout confirmation state if not exists
        if "show_logout_confirmation" not in st.session_state:
            st.session_state.show_logout_confirmation = False
            
        if not st.session_state.show_logout_confirmation:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.show_logout_confirmation = True
                st.rerun()
        else:
            st.warning("Hey, if you're busy and need a break, I get it. Don't worry, all your progress will be saved!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, log out"):
                    # First call Streamlit's logout
                    st.logout()
                    
                    # Then clear our session state
                    if "demo_user" in st.session_state:
                        del st.session_state.demo_user
                    st.session_state.user_data = {}
                    st.session_state.messages = []
                    st.session_state.state = None
                    st.session_state.current_page = "landing"
                    st.session_state.show_logout_confirmation = False
            with col2:
                if st.button("No, return to session"):
                    st.session_state.show_logout_confirmation = False
                    st.rerun()
    
    # Main content with custom styling
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #9747FF; font-size: 2.5rem; margin-bottom: 0.5rem;'>AI-Powered Tutoring System</h1>
        <p style='font-size: 1.1rem; color: #CCCCCC;'>Welcome back! Ready to continue your learning journey?</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_topic = st.session_state.user_data.get('nextTopic', "Computer Fundamentals")
    previous_topic = st.session_state.user_data.get('previous_topic', "")
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1E1E2E, #2E2E3E); padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #9747FF;'>
        <p style='color: #CCCCCC; margin-bottom: 0.5rem;'>Welcome back, <strong style='color: #9747FF;'>{st.session_state.get('user_data', {}).get('name', 'Student')}</strong>!</p>
        <p style='color: #CCCCCC; margin-bottom: 0.5rem;'>Lola hasn't seen you since {st.session_state.get('user_data', {}).get('last_login', st.session_state.get('login_time', datetime.now()))}</p>
        <p style='color: #CCCCCC; margin: 0;'>Ready to begin your session on <strong style='color: #9747FF;'>'{user_topic}'</strong>? Just hit 'Start Session'!</p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "state" not in st.session_state:
        st.session_state.state = {
            "user_topic": user_topic,
            "previous_topic": previous_topic,
            "messages": [],
            "squads_ready": False,
            "subgraph_state": None,
            "session_type": "lesson",
            "next_step": None,
            "user_profile": st.session_state.user_data
        }

    with st.sidebar:
        st.header("Session Setup")
        session_type = st.selectbox(
            "Session Type",
            ["lesson", "quiz"],
            index=0,
            key="session_type"
        )
        if st.button("Start Session") and user_topic:
            start_new_session(user_topic, previous_topic, session_type)
            st.rerun()

    for message in st.session_state.messages:
        if message["role"] != "system":  # Don't show system messages
            with st.chat_message(message["role"], avatar=f"data:image/png;base64,{lola_avatar}" if message["role"] == "assistant" else None):
                st.write(message["content"])
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.write(user_input)
        
        # Special handling for choice after summary
        if st.session_state.state.get("awaiting_user_choice", False):
            user_choice = user_input.lower()
            if "continue" in user_choice:
                # User wants to continue with recommended session
                new_session_type = st.session_state.state.get("recommended_session_type", "lesson")
                user_topic = st.session_state.state.get("user_topic", "")
                
                # Display confirmation message
                with st.chat_message("assistant", avatar=f"data:image/png;base64,{lola_avatar}"):
                    message = f"Great! Let's proceed with the {new_session_type}."
                    st.write(message)
                st.session_state.messages.append({"role": "assistant", "content": message})
                
                # Clear awaiting_user_choice flag BEFORE starting a new session
                st.session_state.state["awaiting_user_choice"] = False
                
                # Start a new session using the recommended session type
                start_new_session(user_topic, previous_topic, new_session_type)
                
                st.rerun()
                    
            elif "exit" in user_choice:
                # User wants to exit; clear authentication status and user data
                if "demo_user" in st.session_state:
                    del st.session_state.demo_user
                st.session_state.user_data = {}
                st.session_state.messages = []
                utils.go_to_page("landing")
            else:
                # User provided something else
                with st.chat_message("assistant", avatar=f"data:image/png;base64,{lola_avatar}"):
                    st.write("I didn't understand your choice. Please reply with 'Continue' to proceed with the recommended session or 'Exit' to end this session.")
                st.session_state.messages.append({"role": "assistant", "content": "I didn't understand your choice. Please reply with 'Continue' to proceed with the recommended session or 'Exit' to end this session."})
            
            # Important: Skip graph invocation when handling user choice
            st.rerun()
        
        # Update state with user's message
        current_state = st.session_state.state.copy()
        
        # Update subgraph state with the user's message
        if current_state.get("subgraph_state") and current_state["subgraph_state"].get("messages"):
            # If we have existing subgraph messages, append to them
            current_messages = current_state["subgraph_state"]["messages"]
            current_messages.append(HumanMessage(content=user_input))
            current_state["subgraph_state"]["messages"] = current_messages
            
            # For quiz sessions, update user_answer
            if current_state.get("session_type") == "quiz" and "awaiting_answer" in current_state["subgraph_state"]:
                current_state["subgraph_state"]["user_answer"] = user_input
        else:
            # If we don't have messages yet, create them
            if "subgraph_state" not in current_state or current_state["subgraph_state"] is None:
                # Initialize subgraph state based on session type
                if current_state.get("session_type") == "lesson":
                    current_state["subgraph_state"] = {
                        "topic": current_state.get("user_topic", ""),
                        "messages": [HumanMessage(content=user_input)]
                    }
                else:  # quiz
                    current_state["subgraph_state"] = {
                        "topic": current_state.get("user_topic", ""),
                        "messages": [HumanMessage(content=user_input)],
                        "summary": None
                    }
        
        # Continue the graph with the user's input
        new_state = primary_graph.invoke(current_state)
        st.session_state.state = new_state
        
        # Priority order for finding messages to display:
        # 1. Check direct message from state
        if new_state.get("message"):
            with st.chat_message("assistant", avatar=f"data:image/png;base64,{lola_avatar}"):
                st.write(new_state["message"])
            st.session_state.messages.append({"role": "assistant", "content": new_state["message"]})
        
        # 2. Check for messages in subgraph state
        elif new_state.get("subgraph_state") and new_state["subgraph_state"].get("messages"):
            latest_messages = new_state["subgraph_state"]["messages"]
            for msg in reversed(latest_messages):
                if isinstance(msg, AIMessage) and msg.content not in [m["content"] for m in st.session_state.messages if m["role"] == "assistant"]:
                    with st.chat_message("assistant", avatar=f"data:image/png;base64,{lola_avatar}"):
                        st.write(msg.content)
                    st.session_state.messages.append({"role": "assistant", "content": msg.content})
                    break
        
        st.rerun()