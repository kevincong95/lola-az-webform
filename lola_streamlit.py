import hashlib
import streamlit as st
import utils

from datetime import datetime, timedelta
from langchain_core.messages import AIMessage, HumanMessage

from landing_page import go_back_to_landing
from lola_graph import primary_graph

# ============================================
# Authentication Functions
# ============================================
def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Initialize session state for authentication
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    
    if st.session_state.authentication_status:
        return True
    
    # If not authenticated, show login form in a container
    # This container will be emptied/replaced after successful login
    with st.container():
        if not st.session_state.authentication_status:
            st.header("Login")
            if st.button("← Back to Landing Page"):
                go_back_to_landing()
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                # Connect to MongoDB
                client = utils.get_mongodb_connection()
                
                if client is None:
                    st.error("Could not connect to database. Please try again later.")
                    return False
                
                try:
                    # Access your database and collection
                    users_collection = client[utils.MONGO_DB_NAME]['students']
                    # Find the user
                    user = users_collection.find_one({"username": username})
                    
                    if user:
                        # Hash the input password with the same method as stored in your DB
                        # This example assumes passwords are stored with SHA-256
                        # Adjust according to your actual password storage method
                        hashed_password = hashlib.sha256(password.encode()).hexdigest()
                        
                        # For hashed passwords (better security)
                        stored_password = user['password_hash']
                        is_password_correct = (hashed_password == stored_password)
                        
                        if is_password_correct:
                            st.session_state.authentication_status = True
                            st.session_state.username = username
                            st.session_state.login_time = datetime.now()
                            
                            # Store user data in session state for later use
                            st.session_state.user_data = {
                                "username": user.get('username', username),
                                "last_login": user.get('last_login', st.session_state.login_time),
                                "current_topic": user.get('current_topic', 'What is a computer?'),
                                "previous_topic": user.get('previous_topic', '')
                            }
                            
                            # Use success message temporarily before rerun
                            st.success(f"Welcome, {st.session_state.username}!")
                            # Rerun to clear the login form and show main app
                            st.rerun()
                        else:
                            st.error("Password is incorrect")
                            return False
                    else:
                        st.error("Username not found")
                        return False
                        
                except Exception as e:
                    st.error(f"Authentication error: {e}")
                    return False
                finally:
                    # Close MongoDB connection
                    client.close()
    
    return st.session_state.authentication_status

# Function to start a new session
def start_new_session(current_topic, previous_topic, session_type):
    # Reset state for new session
    squads_ready = st.session_state.state["squads_ready"] or st.session_state.login_time - st.session_state.user_data["last_login"] < timedelta(days = 2) or not previous_topic
    if not squads_ready:
        with st.chat_message('assistant'):
            st.write(f"Uh-oh! Looks like your squads have fallen asleep! We'll have to wake them up with a review on {previous_topic}.")
    st.session_state.messages = []
    st.session_state.state = {
        "user_topic": current_topic,
        "previous_topic": previous_topic,
        "messages": [],
        "session_type": session_type,
        "squads_ready": squads_ready,
        "subgraph_state": None,
        "next_step": None,
        "remaining_steps": 5
    }
    
    # Handle lesson sessions
    if session_type == "lesson":     
        # Prepare lesson state
        lesson_state = {
            "topic": current_topic,
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
    st.title("🎓 AI-Powered Tutoring System")
    st.write(f"Welcome back, {st.session_state.username}! Lola hasn't seen you since {st.session_state.user_data['last_login']}. ")
    user_topic = st.session_state.user_data['current_topic']
    previous_topic = st.session_state.user_data['previous_topic']
    st.write(f"Press 'Start Session' to begin your session on either {user_topic} or {previous_topic}.")

    # Add a small user info section at the top right
    with st.sidebar:
        st.info(f"Logged in as: {st.session_state.username}")
        
        # Add logout button at the top of sidebar
        if st.button("Logout"):
            # Clear authentication status and user data
            st.session_state.authentication_status = False
            st.session_state.username = ""
            st.session_state.user_data = {}
            st.session_state.messages = []
            # Rerun to show login page
            st.rerun()

    # Initialize session state
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
            "next_step": None
        }

    # ------------------ Start Session ------------------
    with st.sidebar:
        st.header("Session Setup")
        # user_topic = st.text_input("Enter the topic you want to learn:", key="topic_input")
        
        session_type = st.selectbox(
            "Session Type",
            ["lesson", "quiz"],
            index=0,
            key="session_type"
        )
        
        
        if st.button("Start Session") and user_topic:
            start_new_session(user_topic, previous_topic, session_type)
            st.rerun()

    # ------------------ Display Chat Messages ------------------
    for message in st.session_state.messages:
        if message["role"] != "system":  # Don't show system messages
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # ------------------ Handle User Input ------------------
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
                with st.chat_message("assistant"):
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
                # TODO: write message history to long term memory
                st.session_state.authentication_status = False
                st.session_state.username = ""
                st.session_state.user_data = {}
                st.session_state.messages = []
                # Rerun to show login page
                st.rerun()
            else:
                # User provided something else
                with st.chat_message("assistant"):
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
            with st.chat_message("assistant"):
                st.write(new_state["message"])
            st.session_state.messages.append({"role": "assistant", "content": new_state["message"]})
        
        # 2. Check for messages in subgraph state
        elif new_state.get("subgraph_state") and new_state["subgraph_state"].get("messages"):
            # Convert subgraph messages to Streamlit format
            latest_messages = new_state["subgraph_state"]["messages"]
            for msg in reversed(latest_messages):
                if isinstance(msg, AIMessage) and msg.content not in [m["content"] for m in st.session_state.messages if m["role"] == "assistant"]:
                    with st.chat_message("assistant"):
                        st.write(msg.content)
                    st.session_state.messages.append({"role": "assistant", "content": msg.content})
                    break
        
        st.rerun()
