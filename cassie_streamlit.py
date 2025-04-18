import streamlit as st
import tempfile
import json
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from lola_graph import primary_graph

st.title("🎓 AI-Powered Tutoring System")
st.write("Lola will guide your learning experience!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "state" not in st.session_state:
    st.session_state.state = {
        "user_topic": "",
        "messages": [],
        "template_path": None,
        "subgraph_state": None,
        "session_type": "lesson",
        "next_step": None
    }

# Store template file in session state so it persists
if "template_file" not in st.session_state:
    st.session_state.template_file = None

# Convert Streamlit chat format to Langgraph format
def convert_to_langgraph_messages(streamlit_messages):
    langgraph_messages = []
    for msg in streamlit_messages:
        if msg["role"] == "user":
            langgraph_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langgraph_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system":
            langgraph_messages.append(SystemMessage(content=msg["content"]))
    return langgraph_messages

# Convert Langgraph format to Streamlit chat format
def convert_to_streamlit_messages(langgraph_messages):
    streamlit_messages = []
    for msg in langgraph_messages:
        if isinstance(msg, HumanMessage):
            streamlit_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            streamlit_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            streamlit_messages.append({"role": "system", "content": msg.content})
    return streamlit_messages

# Function to start a new session
def start_new_session(topic, session_type, template_file=None):
    # Reset state for new session
    st.session_state.messages = []
    st.session_state.state = {
        "user_topic": topic,
        "messages": [],
        "session_type": session_type,
        "subgraph_state": None,
        "next_step": None
    }
    
    # Handle template if uploaded (for lesson sessions)
    if template_file is not None and session_type == "lesson":
        # Create a temporary file to store the uploaded template
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            tmp_file.write(template_file.getvalue())
            template_path = tmp_file.name
        
        # Read the template to add to state
        try:
            with open(template_path, 'r') as f:
                template_content = json.load(f)
                
            # Prepare lesson state
            lesson_state = {
                "topic": topic,
                "messages": [],
                "template": template_content,
                "template_path": template_path,
                "lesson_plan": None
            }
            st.session_state.state["subgraph_state"] = lesson_state
        except Exception as e:
            st.error(f"Error loading template: {e}")
    
    # Add initial message
    initial_message = f"I want to {'learn about' if session_type == 'lesson' else 'take a quiz on'} {topic}"
    st.session_state.messages.append({"role": "user", "content": initial_message})
    st.session_state.state["messages"].append(HumanMessage(content=initial_message))
    
    # Update primary graph state with initial message and invoke it
    new_state = primary_graph.invoke(st.session_state.state)
    st.session_state.state = new_state
    
    # Preserve messages across graph calls
    if new_state.get("subgraph_state") and new_state["subgraph_state"].get("messages"):
        st.session_state.messages = convert_to_streamlit_messages(new_state["subgraph_state"]["messages"])
    else:
        # Handle the initial greeting from the primary graph
        if new_state.get("message"):
            st.session_state.messages.append({"role": "assistant", "content": new_state["message"]})

# ------------------ Start Session ------------------
with st.sidebar:
    st.header("Session Setup")
    user_topic = st.text_input("Enter the topic you want to learn:", key="topic_input")
    
    session_type = st.selectbox(
        "Session Type",
        ["lesson", "quiz"],
        index=0,
        key="session_type"
    )
    
    # Optional template upload for lesson plans
    template_file = st.file_uploader("Optional: Upload a lesson template (JSON file)", type=["json"])
    
    # Store template file in session state so it persists
    if template_file is not None:
        st.session_state.template_file = template_file
    
    if st.button("Start Session") and user_topic:
        start_new_session(user_topic, session_type, st.session_state.template_file)
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
        current_state = st.session_state.state.copy()
        
        if "continue" in user_choice:
            # User wants to continue with recommended session
            new_session_type = current_state.get("recommended_session_type", "lesson")
            user_topic = current_state.get("user_topic", "")
            
            # Display confirmation message
            with st.chat_message("assistant"):
                message = f"Great! Let's proceed with the {new_session_type}."
                st.write(message)
            st.session_state.messages.append({"role": "assistant", "content": message})
            
            # Start a new session using the recommended session type
            # Pass the stored template file from session state
            start_new_session(user_topic, new_session_type, st.session_state.template_file)
            
            # Clear awaiting_user_choice flag
            st.session_state.state["awaiting_user_choice"] = False
            
            st.rerun()
                
        elif "exit" in user_choice:
            # User wants to exit
            with st.chat_message("assistant"):
                st.write("Thank you for your time! The session has ended. You can start a new session whenever you're ready.")
            st.session_state.messages.append({"role": "assistant", "content": "Thank you for your time! The session has ended. You can start a new session whenever you're ready."})
            
            # Reset state
            st.session_state.state = {
                "user_topic": "",
                "messages": [],
                "subgraph_state": None,
                "session_type": "lesson",
                "next_step": None,
                "awaiting_user_choice": False
            }
        else:
            # User provided something else
            with st.chat_message("assistant"):
                st.write("I didn't understand your choice. Please reply with 'Continue' to proceed with the recommended session or 'Exit' to end this session.")
            st.session_state.messages.append({"role": "assistant", "content": "I didn't understand your choice. Please reply with 'Continue' to proceed with the recommended session or 'Exit' to end this session."})
    
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
                    "correct_answers": 0,
                    "mistakes": 0,
                    "awaiting_answer": False,
                    "user_answer": user_input
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

# Cleanup temporary files when the app is closed
def cleanup_temp_files():
    if st.session_state.state.get("subgraph_state") and st.session_state.state["subgraph_state"].get("template_path") and os.path.exists(st.session_state.state["subgraph_state"]["template_path"]):
        try:
            os.remove(st.session_state.state["subgraph_state"]["template_path"])
        except:
            pass

# Register cleanup function
import atexit
atexit.register(cleanup_temp_files)