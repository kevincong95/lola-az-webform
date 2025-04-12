import streamlit as st
import tempfile
import json
import os
from lesson_plan import lesson_graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

st.title("🎓 AI-Powered Tutoring System")
st.write("Cassie will teach you interactively!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "state" not in st.session_state:
    st.session_state.state = {
        "topic": "",
        "messages": [],
        "template_path": None,
        "template": None,
        "lesson_plan": None
    }

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

# ------------------ Start Lesson ------------------
with st.sidebar:
    st.header("Lesson Setup")
    user_topic = st.text_input("Enter the topic you want to learn:", key="topic_input")
    
    # Optional template upload
    template_file = st.file_uploader("Optional: Upload a lesson template (JSON file)", type=["json"])
    
    if st.button("Start Lesson") and user_topic:
        # Reset state for new lesson
        st.session_state.messages = []
        st.session_state.state = {
            "topic": user_topic,
            "messages": [],
            "template_path": None,
            "template": None,
            "lesson_plan": None
        }
        
        # Handle template if uploaded
        if template_file is not None:
            # Create a temporary file to store the uploaded template
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
                tmp_file.write(template_file.getvalue())
                template_path = tmp_file.name
            
            # Read the template to add to state
            try:
                with open(template_path, 'r') as f:
                    template_content = json.load(f)
                st.session_state.state["template"] = template_content
                st.session_state.state["template_path"] = template_path
            except Exception as e:
                st.error(f"Error loading template: {e}")
        
        # Add initial message
        initial_message = f"I want to learn about {user_topic}"
        st.session_state.messages.append({"role": "user", "content": initial_message})
        
        # Update Langgraph state with initial message
        st.session_state.state["messages"] = [HumanMessage(content=initial_message)]
        
        # Invoke the graph with initial state
        new_state = lesson_graph.invoke(st.session_state.state)
        st.session_state.state = new_state
        
        # Convert Langgraph messages to Streamlit format
        st.session_state.messages = convert_to_streamlit_messages(new_state["messages"])
        
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
    
    # Update with user's message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Update Langgraph state
    current_state = st.session_state.state.copy()
    current_state["messages"] = convert_to_langgraph_messages(st.session_state.messages)
    
    # Continue the graph with the user's input
    new_state = lesson_graph.invoke(current_state)
    st.session_state.state = new_state
    
    # Convert back to Streamlit format for display
    st.session_state.messages = convert_to_streamlit_messages(new_state["messages"])
    
    # Display assistant's response
    with st.chat_message("assistant"):
        latest_ai_message = new_state["messages"][-1]
        if isinstance(latest_ai_message, AIMessage):
            st.write(latest_ai_message.content)
    
    st.rerun()

# Cleanup temporary files when the app is closed
def cleanup_temp_files():
    if st.session_state.state.get("template_path") and os.path.exists(st.session_state.state["template_path"]):
        try:
            os.remove(st.session_state.state["template_path"])
        except:
            pass

# Register cleanup function
import atexit
atexit.register(cleanup_temp_files)