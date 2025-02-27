import streamlit as st
from cassie_graph import lesson_graph

st.title("🎓 AI-Powered Tutoring System")
st.write("Cassie will teach you interactively!")

# Initialize session state
if "lesson_state" not in st.session_state:
    st.session_state.lesson_state = {
        "topic": "",
        "lesson_plan": [],
        "current_step": 0,
        "current_question": "",
        "attempts": 0,
        "summary": "",
        "messages": [],
        "user_answer": "",
        "awaiting_answer": False
    }

# ------------------ Start Lesson ------------------
user_topic = st.text_input("Enter the topic you want to learn:")

if st.button("Start Lesson") and user_topic:
    # Initialize new lesson
    st.session_state.lesson_state["topic"] = user_topic
    
    lesson_state = lesson_graph.invoke(st.session_state.lesson_state)
    st.session_state.lesson_state = lesson_state

# ------------------ Display Chat Messages ------------------
# Only display messages up to the current index
for msg in st.session_state.lesson_state['messages']:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ------------------ Handle User Input ------------------
if st.session_state.lesson_state.get('awaiting_answer', False):
    user_answer = st.chat_input("Your answer:")
    
    if user_answer:
        current_state = st.session_state.lesson_state.copy()
        current_state["user_answer"] = user_answer
        print(current_state)
        
        # Continue the graph with the user's answer
        new_state = lesson_graph.invoke(current_state)
        st.session_state.lesson_state = new_state
        st.rerun()

# Display summary if lesson is complete
if "summary" in st.session_state.lesson_state and st.session_state.lesson_state["summary"]:
    st.write("### 📝 Lesson Summary")
    st.write(st.session_state.lesson_state["summary"])