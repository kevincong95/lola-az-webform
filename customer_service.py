import streamlit as st
import utils
from onboard_agent import sally_graph
from datetime import datetime
from utils import create_new_user, get_avatar_base64
import re

def initialize_onboard_state():
    """Initialize or reset the onboarding state."""
    if "onboard_state" not in st.session_state:
        st.session_state.onboard_state = {
            "messages": [],
            "student_profile": None,
            "awaiting_choice": False,
            "current_options": [],
            "button_counter": -1,
            "last_message_index": -1,
            "last_question_index": -1,
            "pending_response": None
        }
    return st.session_state.onboard_state

def reset_onboard_state():
    """Reset the onboarding state to initial values."""
    st.session_state.onboard_state["button_counter"] = -1
    st.session_state.onboard_state["last_message_index"] = -1
    st.session_state.onboard_state["last_question_index"] = -1
    st.session_state.onboard_state["pending_response"] = None
    st.session_state.onboard_state["awaiting_choice"] = False
    st.session_state.onboard_state["current_options"] = []

def display_header(user_name: str):
    """Display the header with user name and logout button."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style='text-align: left; margin-bottom: 2rem;'>
            <h1 style='color: #9747FF; font-size: 2rem; margin-bottom: 0.5rem;'>Nice to meet you {user_name}, I'm Lola!</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True, key="logout_button"):
            if "demo_user" in st.session_state:
                del st.session_state.demo_user
            st.session_state.username = ""
            st.session_state.user_data = {}
            reset_onboard_state()
            st.logout()
            utils.go_to_page("landing")

def is_question_message(content: str) -> bool:
    """Check if a message is a question message."""
    content_lower = content.lower()
    return (("are you a student interested in ap csa tutoring" in content_lower and "or are you a parent" in content_lower) or
            ("a)" in content_lower and "b)" in content_lower))

def extract_question_options(content: str) -> tuple[str, list[str]]:
    """Extract question text and options from a message."""
    if "are you a student interested in ap csa tutoring" in content.lower() and "or are you a parent" in content.lower():
        return content, [
            "I am a student interested in AP CSA tutoring",
            "I am a parent looking to enroll my student"
        ]
    
    lines = content.split('\n')
    question_lines = []
    options = []
    
    for line in lines:
        if any(line.strip().startswith(f"{chr(i)})") for i in range(97, 123)):
            option = line.strip()
            if option:
                # Strip any suffix enclosed in (*...*) from the option text
                option = re.sub(r'\s*\(\*[^)]*\*\)', '', option)
                options.append(option)
        else:
            question_lines.append(line)
    
    return '\n'.join(question_lines).strip(), options

def display_question_options(msg_idx: int, question_text: str, options: list[str], 
                           last_question_idx: int, messages: list, user_response: str = None):
    """Display question text and options as buttons, checkboxes, or highlighted text."""
    st.write(question_text)
    
    if options:
        # Check if this is a 'pick multiple' question
        is_multi = "pick multiple" in question_text.lower()
        if msg_idx == last_question_idx:
            st.session_state.onboard_state["current_options"] = options
            st.session_state.onboard_state["button_counter"] = len(options)
            st.session_state.onboard_state["last_message_index"] = msg_idx
            st.session_state.onboard_state["awaiting_choice"] = True

            if is_multi:
                # Use checkboxes for each option
                selected = st.session_state.onboard_state.get(f"multi_selected_{msg_idx}", [False]*len(options))
                new_selected = []
                for i, option in enumerate(options):
                    checked = st.checkbox(option, value=selected[i], key=f"multi_checkbox_{msg_idx}_{i}")
                    new_selected.append(checked)
                st.session_state.onboard_state[f"multi_selected_{msg_idx}"] = new_selected
                # Text input for clarification
                clarification = st.text_input(
                    "Additional:",
                    value=st.session_state.onboard_state.get(f"clarification_{msg_idx}", ""),
                    key=f"clarification_{msg_idx}"
                )
                st.session_state.onboard_state[f"clarification_{msg_idx}"] = clarification
                # Submit button
                if st.button("Submit", key=f"multi_submit_{msg_idx}"):
                    selected_options = [opt for opt, sel in zip(options, new_selected) if sel]
                    response = "; ".join(selected_options)
                    if clarification.strip():
                        response = f"{response}. {clarification.strip()}"
                    st.session_state.onboard_state["pending_response"] = response
            else:
                # Display options as buttons (single select)
                for i, option in enumerate(options):
                    button_key = f"choice_button_msg{msg_idx}_opt{i}"
                    if st.button(option, key=button_key):
                        st.session_state.onboard_state["pending_response"] = option
        else:
            # Display past options with highlighting
            for option in options:
                if option == user_response:
                    st.markdown(f"<div style='color: #9747FF; padding: 0.5rem; margin: 0.25rem 0;'>{option}</div>", 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='padding: 0.5rem; margin: 0.25rem 0;'>{option}</div>", 
                              unsafe_allow_html=True)

def display_account_creation(student_profile: dict, user: dict):
    """Display account creation options after profile completion."""
    st.success("✅ You're all set! Here's what I learned about you:")
    st.json(student_profile)

    user_name = user.get("name", "")
    user_email = user.get("email", "")

    st.write(f"You're signed in as **{user_name}** ({user_email}).")
    st.write("Would you like to create your AP CSA account with this information?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, create my account"):
            if not hasattr(st.session_state, "user_data"):
                st.session_state.user_data = student_profile
            st.session_state.user_data["username"] = user_name
            st.session_state.user_data["email"] = user_email
            creation_time = datetime.now()
            st.session_state.user_data["created_at"] = creation_time
            st.session_state.user_data["last_login"] = creation_time
            success, message = create_new_user(st.session_state.user_data)
            if success:
                st.success("🎉 Your account has been created successfully!")
                st.session_state.onboard_state = None
                st.session_state.current_page = "main"
                st.rerun()
            else:
                st.error(f"Error creating account: {message}")

    with col2:
        if st.button("❌ No, go back"):
            st.session_state.onboard_state["student_profile"] = None
            st.rerun()

def display_customer_service():
    """Handle the customer service agent conversation for onboarding new users."""
    user = getattr(st, "user", None) or st.session_state.get("demo_user", None)
    logged_in = user and user.get("is_logged_in", False)
    
    if not logged_in:
        st.login()
        if "onboard_state" in st.session_state:
            st.session_state.onboard_state["button_counter"] = -1
        return
    
    # Initialize state
    onboard_state = initialize_onboard_state()
    
    # Use columns to constrain the width of all content
    col1, content_col, col3 = st.columns([1, 3, 1])
    with content_col:
        # Header and logout in a row
        header_col, logout_col = st.columns([3, 1])
        with header_col:
            st.markdown(f"""
            <div style='text-align: left; margin-bottom: 2rem;'>
                <h1 style='color: #9747FF; font-size: 2rem; margin-bottom: 0.5rem;'>Nice to meet you {user.get("given_name", "")}, I'm Lola!</h1>
            </div>
            """, unsafe_allow_html=True)
        with logout_col:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            if st.button("🚪 Logout", use_container_width=True, key="logout_button"):
                if "demo_user" in st.session_state:
                    del st.session_state.demo_user
                st.session_state.username = ""
                st.session_state.user_data = {}
                reset_onboard_state()
                st.logout()
                utils.go_to_page("landing")
        
        # Get messages and check if we need initialization
        messages = utils.convert_to_streamlit_messages(onboard_state.get("messages", []))
        
        # If no messages, get initial greeting
        if not messages:
            try:
                # Get initial greeting and store it in state
                new_state = sally_graph.invoke(onboard_state)
                if new_state and new_state.get("messages"):
                    st.session_state.onboard_state = new_state
                    st.rerun()
                else:
                    st.error("Failed to get initial greeting. Please refresh the page.")
            except Exception as e:
                st.error(f"Error during initialization: {str(e)}")
        
        # Only display conversation and input if messages are present
        if messages:
            # Display conversation history
            lola_avatar = get_avatar_base64("assets/lola.png")
            
            # Find the most recent question
            last_question_idx = -1
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "assistant" and is_question_message(messages[i]["content"]):
                    last_question_idx = i
                    break
            
            # Update state for new question
            if last_question_idx != onboard_state.get("last_question_index", -1):
                onboard_state["last_question_index"] = last_question_idx
                onboard_state["awaiting_choice"] = True
                onboard_state["current_options"] = []
                onboard_state["button_counter"] = 0
                onboard_state["last_message_index"] = last_question_idx
                onboard_state["pending_response"] = None
            
            # Display conversation history
            for msg_idx, message in enumerate(messages):
                if message["role"] == "assistant":
                    with st.chat_message(message["role"], avatar=f"data:image/png;base64,{lola_avatar}"):
                        content = message["content"]
                        
                        if is_question_message(content):
                            question_text, options = extract_question_options(content)
                            user_response = None
                            if msg_idx + 1 < len(messages) and messages[msg_idx + 1]["role"] == "user":
                                user_response = messages[msg_idx + 1]["content"]
                            
                            display_question_options(msg_idx, question_text, options, last_question_idx, messages, user_response)
                        else:
                            st.write(content)
                            if msg_idx == len(messages) - 1:
                                onboard_state["awaiting_choice"] = False
                                onboard_state["current_options"] = []
                                onboard_state["button_counter"] = 0
                                onboard_state["last_message_index"] = msg_idx
                elif message["role"] == "user":
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
            
            # Chat input
            user_input = st.chat_input("Type your response here... (or select an option)", key="chat_input")
            if user_input:
                # If a chat input is submitted, treat it as the response (even if awaiting_choice is True)
                onboard_state["pending_response"] = user_input
            
            # Handle pending response
            if onboard_state.get("pending_response") is not None:
                response = onboard_state["pending_response"]
                onboard_state["pending_response"] = None
                
                # Add user message to state
                onboard_state["messages"].append({
                    "role": "user",
                    "content": response
                })
                
                try:
                    with st.spinner("Thinking..."):
                        new_state = sally_graph.invoke(onboard_state)
                        if new_state and new_state.get("messages"):
                            st.session_state.onboard_state = new_state
                            st.rerun()
                        else:
                            st.error("Failed to get agent response. Please try again.")
                except Exception as e:
                    st.error(f"Error getting agent response: {str(e)}")
                    onboard_state["messages"].append({
                        "role": "assistant",
                        "content": "I apologize, but I encountered an error. Please try again."
                    })
                    st.session_state.onboard_state = onboard_state
                    st.rerun()
            
            # Display account creation if profile is complete
            if onboard_state.get("student_profile"):
                display_account_creation(onboard_state["student_profile"], user)