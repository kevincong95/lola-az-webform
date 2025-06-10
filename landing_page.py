import base64, hashlib, os
import streamlit as st
import utils

from csa_chat import run_csa_chat
from datetime import datetime
from lola_streamlit import lola_main
from onboard_agent import sally_graph

def get_avatar_base64(image_path):
    """Convert image to base64 for avatar display."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def create_new_user(user_data, password = None):
    """Create a new user in the database with provided information."""
    client = st.session_state.mongo_client
    if client is None:
        return False, "Could not connect to database."
    
    try:
        db = client[utils.MONGO_DB_NAME]
        users_collection = db['students']
        
        # Check if email already exists
        if users_collection.find_one({"email": user_data.get("email", "")}):
            return False, "Email already exists. Please choose another."
        
        # Hash the password
        if password:
            user_data["password_hash"] = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert the new user
        users_collection.insert_one(user_data)
        return True, "User created successfully!"
    
    except Exception as e:
        return False, f"Error creating user: {e}"

def display_landing_page():
    """Display the landing page with options for new and returning users."""
    
    # Add sidebar with logo and login
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
        
        st.markdown("### Ready to FastLearn?")
        st.write("Please log in to onboard your account or continue your learning journey!")
        if st.button("🔐 Log in with Google", use_container_width=True):
            # For demo purposes, simulate login
            st.session_state.demo_user = {
                "name": "Demo User",
                "email": "demo@example.com",
                "is_logged_in": True
            }
            utils.go_to_page("customer_service")
    
    # Main content with Lola's avatar
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Lola's circular avatar with custom CSS
        st.markdown("""
        <div style='text-align: center; margin: 3rem 0;'>
            <img src="data:image/png;base64,{}" 
                 style='width: 150px; height: 150px; border-radius: 50%; object-fit: cover;'/>
        </div>
        """.format(
            __import__('base64').b64encode(open("assets/lola.png", "rb").read()).decode()
        ), unsafe_allow_html=True)
        
        st.markdown("""
        <style>
        @keyframes typewriter {
            0% { 
                width: 0;
                border-right: 2px solid #9747FF;
            }
            70% { 
                width: 100%;
                border-right: 2px solid #9747FF;
            }
            100% { 
                width: 100%;
                border-right: transparent;
            }
        }
        
        .typewriter-text {
            white-space: nowrap;
            overflow: hidden;
            border-right: 2px solid transparent;
            width: 0;
            animation: typewriter 4s ease-in-out infinite;
            font-family: 'Courier New', monospace;
            display: inline-block;
            min-width: 660px;
        }
        </style>
        
        <div style='text-align: center; margin: 2rem 0;'>
            <h2 style='color: #9747FF; margin-bottom: 0.5rem; font-size: 2.5rem;'>Hi! I am Lola</h2>
            <div style='height: 2rem; display: flex; justify-content: center; align-items: center;'>
                <p class='typewriter-text' style='color: #CCCCCC; font-size: 1.3rem; margin: 0;'>
                    Allow me to spin the perfect coding lesson for you!
                </p>
            </div>
            <div style='display: flex; justify-content: center; align-items: center; margin: 0.5rem 0;'>
                <h2 style='color: #9747FF; font-size: 1.6rem; font-weight: normal; font-style: italic; white-space: nowrap; margin: 0;'>
                    How? What makes me special? Let's chat to get all your questions answered.
                </h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Chat with Lola", key="chat_button", use_container_width=True, type="primary"):
            utils.go_to_page("csa_chat")
    
    # Add learning tools section
    st.markdown("---")  # Add a separator
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0;'>
        <h2 style='color: #9747FF; font-size: 2rem;'>Learning Tools</h2>
        <p style='color: #CCCCCC; font-size: 1.2rem;'>Access our interactive tools to enhance your learning experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    tool_col1, tool_col2 = st.columns(2)
    with tool_col1:
        if st.button("💻 Code Playground", use_container_width=True, type="secondary"):
            utils.go_to_page("simple_ide")
    with tool_col2:
        if st.button("🎨 Interactive Whiteboard", use_container_width=True, type="secondary"):
            utils.go_to_page("whiteboard")

def run_customer_service_agent():
    """Handle the customer service agent conversation for onboarding new users."""
    user = getattr(st, "user", None) or st.session_state.get("demo_user", None)
    logged_in = user and user.get("is_logged_in", False)
    if not logged_in:
        st.login()
        # Set button counter to -1 when logged out
        if "onboard_state" in st.session_state:
            st.session_state.onboard_state["button_counter"] = -1
    else:
        if "onboard_state" not in st.session_state:
            st.session_state.onboard_state = {
                "messages": [],
                "student_profile": None,
                "awaiting_choice": False,
                "current_options": [],
                "button_counter": -1,  # Initialize to -1
                "last_message_index": -1,  # Track the last message index for button keys
                "last_question_index": -1,  # Track the index of the last question
                "pending_response": None  # Track pending responses
            }
        # Ensure button_counter exists and is -1 if not logged in
        elif "button_counter" not in st.session_state.onboard_state:
            st.session_state.onboard_state["button_counter"] = -1
        # Ensure last_message_index exists
        if "last_message_index" not in st.session_state.onboard_state:
            st.session_state.onboard_state["last_message_index"] = -1
        # Ensure last_question_index exists
        if "last_question_index" not in st.session_state.onboard_state:
            st.session_state.onboard_state["last_question_index"] = -1
        # Ensure pending_response exists
        if "pending_response" not in st.session_state.onboard_state:
            st.session_state.onboard_state["pending_response"] = None
        
        # Get user's name
        user_name = user.get("given_name", "")
        
        # Create columns for header and logout button
        col1, col2 = st.columns([3, 1])
        
        # Main content with custom styling in first column
        with col1:
            st.markdown(f"""
            <div style='text-align: left; margin-bottom: 2rem;'>
                <h1 style='color: #9747FF; font-size: 2rem; margin-bottom: 0.5rem;'>Nice to meet you {user_name}, I'm Lola!</h1>
            </div>
            """, unsafe_allow_html=True)
        
        # Logout button in second column
        with col2:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # Add some padding
            if st.button("🚪 Logout", use_container_width=True, key="logout_button"):
                # Clear demo user data and reset button counter to -1
                if "demo_user" in st.session_state:
                    del st.session_state.demo_user
                st.session_state.username = ""
                st.session_state.user_data = {}
                st.session_state.onboard_state["button_counter"] = -1
                st.session_state.onboard_state["last_message_index"] = -1
                st.session_state.onboard_state["last_question_index"] = -1
                st.session_state.onboard_state["pending_response"] = None
                st.logout()
                utils.go_to_page("landing")
        
        # Initial greeting when first arriving at this page
        if not st.session_state.onboard_state["messages"]:
            st.session_state.onboard_state = sally_graph.invoke(st.session_state.onboard_state)
            st.rerun()
        
        # Display conversation history
        lola_avatar = get_avatar_base64("assets/lola.png")
        messages = utils.convert_to_streamlit_messages(st.session_state.onboard_state["messages"])
        
        # Find the most recent question
        last_question_idx = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "assistant":
                content = messages[i]["content"].lower()
                # Check for both the initial role question and regular MCQs
                if ("are you a student interested in ap csa tutoring" in content and "or are you a parent" in content) or \
                   ("a)" in content and "b)" in content):
                    last_question_idx = i
                    break
        
        # Only update last_question_index if we found a new question
        if last_question_idx != st.session_state.onboard_state["last_question_index"]:
            # Reset all state when transitioning to a new question
            st.session_state.onboard_state["last_question_index"] = last_question_idx
            st.session_state.onboard_state["awaiting_choice"] = True
            st.session_state.onboard_state["current_options"] = []
            st.session_state.onboard_state["button_counter"] = 0
            st.session_state.onboard_state["last_message_index"] = last_question_idx
            st.session_state.onboard_state["pending_response"] = None
        
        # Display conversation history
        for msg_idx, message in enumerate(messages):
            if message["role"] == "assistant":
                with st.chat_message(message["role"], avatar=f"data:image/png;base64,{lola_avatar}"):
                    content = message["content"]
                    
                    # Check if this is a question message
                    if ("are you a student interested in ap csa tutoring" in content.lower() and "or are you a parent" in content.lower()) or \
                       ("a)" in content.lower() and "b)" in content.lower()):
                        
                        # For the initial role question, create options
                        if "are you a student interested in ap csa tutoring" in content.lower() and "or are you a parent" in content.lower():
                            question_text = content
                            options = [
                                "I am a student interested in AP CSA tutoring",
                                "I am a parent looking to enroll my student"
                            ]
                        else:
                            # Extract options and question text for regular multiple choice
                            lines = content.split('\n')
                            question_lines = []
                            options = []
                            
                            for line in lines:
                                if any(line.strip().startswith(f"{chr(i)})") for i in range(97, 123)):  # a) through z)
                                    option = line.strip()
                                    if option:
                                        options.append(option)
                                else:
                                    question_lines.append(line)
                            
                            # Display question without options
                            question_text = '\n'.join(question_lines).strip()
                        
                        # Display question text
                        st.write(question_text)
                        
                        if options:
                            # Find user's response to this question
                            user_response = None
                            if msg_idx + 1 < len(messages) and messages[msg_idx + 1]["role"] == "user":
                                user_response = messages[msg_idx + 1]["content"]
                            
                            # Only show buttons for the most recent question
                            if msg_idx == last_question_idx:
                                # Update state before displaying buttons
                                st.session_state.onboard_state["current_options"] = options
                                st.session_state.onboard_state["button_counter"] = len(options)
                                st.session_state.onboard_state["last_message_index"] = msg_idx
                                st.session_state.onboard_state["awaiting_choice"] = True
                                
                                # Display options as buttons
                                st.write("Please select your answer:")
                                for i, option in enumerate(options):
                                    # Create unique key using message index and option index
                                    button_key = f"choice_button_msg{msg_idx}_opt{i}"
                                    
                                    if st.button(option, use_container_width=True, key=button_key):
                                        st.session_state.onboard_state["pending_response"] = option
                            else:
                                # Display past options with highlighting
                                st.write("Options:")
                                for option in options:
                                    if option == user_response:
                                        # Highlight the selected option with purple text
                                        st.markdown(f"<div style='color: #9747FF; padding: 0.5rem; margin: 0.25rem 0;'>{option}</div>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<div style='padding: 0.5rem; margin: 0.25rem 0;'>{option}</div>", unsafe_allow_html=True)
                    else:
                        # Display regular message
                        st.write(content)
                        # Only reset state if this is the most recent message
                        if msg_idx == len(messages) - 1:
                            st.session_state.onboard_state["awaiting_choice"] = False
                            st.session_state.onboard_state["current_options"] = []
                            st.session_state.onboard_state["button_counter"] = 0
                            st.session_state.onboard_state["last_message_index"] = msg_idx
            elif message["role"] == "user":
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
        # Always show chat input at the bottom, but disable it for MCQ
        user_input = st.chat_input("Type your response here..." if not st.session_state.onboard_state["awaiting_choice"] else "Please select an option above...", 
                                  key="chat_input",
                                  disabled=st.session_state.onboard_state["awaiting_choice"])
        if user_input and not st.session_state.onboard_state["awaiting_choice"]:
            st.session_state.onboard_state["pending_response"] = user_input
        
        # Handle any pending response (from either button click or chat input)
        if st.session_state.onboard_state["pending_response"] is not None:
            response = st.session_state.onboard_state["pending_response"]
            # Clear the pending response immediately
            st.session_state.onboard_state["pending_response"] = None
            
            # Update state with the response
            st.session_state.onboard_state["messages"].append({
                "role": "user",
                "content": response
            })
            
            # Get agent's response
            with st.spinner("Thinking..."):
                st.session_state.onboard_state = sally_graph.invoke(st.session_state.onboard_state)
            
            # Single rerun point for all responses
            st.rerun()

        student_profile = st.session_state.onboard_state.get("student_profile")
        if student_profile:
            st.success("✅ You're all set! Here's what I learned about you:")
            st.json(student_profile)

            # If user is logged in, ask for confirmation to create account
            user_name = user.get("name", "")
            user_email = user.get("email", "")

            st.write(f"You're signed in as **{user_name}** ({user_email}).")
            st.write("Would you like to create your AP CSA account with this information?")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, create my account"):
                    # Save to MongoDB and session_state
                    if not hasattr(st.session_state, "user_data"):
                        st.session_state.user_data = student_profile
                    st.session_state.user_data["username"] = user_name
                    st.session_state.user_data["email"] = user_email
                    creation_time = datetime.now()
                    st.session_state.user_data["created_at"] = creation_time
                    st.session_state.user_data["last_login"] = creation_time
                    st.session_state.user_data["current_topic"] = "What is a computer?"
                    st.session_state.user_data["previous_topic"] = ""
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

def main():
    """Main function to handle page routing."""
    # Initialize session state for page navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Store MongoDB connection details in session state if provided
    if "mongodb_config" not in st.session_state:
        st.session_state.mongo_client = utils.get_mongodb_connection()
    
    # Check Streamlit built-in login or demo user
    user = getattr(st, "user", None) or st.session_state.get("demo_user", None)
    is_logged_in = user and user.get("is_logged_in", False)
    
    # Handle authentication and page routing
    if is_logged_in:
        if "username" not in st.session_state:
            st.session_state.username = user["name"]
            # User is logged in; check MongoDB for this user
            if st.session_state.mongo_client:
                db = st.session_state.mongo_client[utils.MONGO_DB_NAME]
                existing_user = db["students"].find_one({"email": user["email"]})
                if existing_user:
                    st.session_state.user_data = existing_user
                    st.session_state.current_page = "main"
                else:
                    st.session_state.current_page = "customer_service"
            else:
                st.session_state.current_page = "customer_service"
    
    # Handle page navigation
    if st.session_state.current_page == "landing":
        display_landing_page()
    elif st.session_state.current_page == "customer_service":
        run_customer_service_agent()
    elif st.session_state.current_page == "csa_chat":
        run_csa_chat()
    elif st.session_state.current_page == "main":
        lola_main()
    elif st.session_state.current_page == "simple_ide":
        from simple_ide import display_simple_ide
        display_simple_ide()
    elif st.session_state.current_page == "whiteboard":
        from whiteboard import display_interactive_whiteboard
        display_interactive_whiteboard()

if __name__ == "__main__":
    main()
