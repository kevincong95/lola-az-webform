import hashlib
import streamlit as st
import utils
import base64
from datetime import datetime
from lola_streamlit import lola_main
from onboard_agent import sally_graph
from csa_chat import run_csa_chat

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

# Authentication Functions
def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Initialize session state for authentication
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = False
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    if st.session_state.authentication_status or (getattr(st, "user", None) and st.user.get("is_logged_in", False)):
        return True
    
    # If not authenticated, show login form in a container
    # This container will be emptied/replaced after successful login
    with st.container():
        if not st.session_state.authentication_status:
            st.header("Login")
            if st.button("← Back to Landing Page"):
                utils.go_to_page("landing")
            
            username = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Log in with username and password"):
                client = st.session_state.mongo_client
                if not client:
                    st.error("Could not connect to database. Please try again later.")
                    return False
                
                try:
                    # Access your database and collection
                    users_collection = client[utils.MONGO_DB_NAME]['students']
                    # Find the user
                    user = users_collection.find_one({
                        "$or": [
                            {"username": username},
                            {"email": username}
                        ]
                    })
                    
                    if user:
                        # Hash the input password with the same method as stored in your DB, such as SHA-256
                        hashed_password = hashlib.sha256(password.encode()).hexdigest()
                        stored_password = user['password_hash']
                        is_password_correct = (hashed_password == stored_password)
                        
                        if is_password_correct:
                            st.session_state.authentication_status = True
                            st.session_state.login_time = datetime.now()
                            st.session_state.user_data = user
                            
                            # Use success message temporarily before rerun
                            st.success(f"Welcome, {st.session_state.get('username', 'User')}!")
                            st.rerun()
                        else:
                            st.error("Password is incorrect")
                            return False
                    else:
                        st.error("Username/email not found")
                        return False
                        
                except Exception as e:
                    st.error(f"Authentication error: {e}")
                    return False
    
    return st.session_state.authentication_status

def run_customer_service_agent():
    """Handle the customer service agent conversation for onboarding new users."""
    user = getattr(st, "user", None) or st.session_state.get("demo_user", None)
    logged_in = user and user.get("is_logged_in", False)
    if not logged_in:
        st.login()
    else:
        if "onboard_state" not in st.session_state:
            st.session_state.onboard_state = {
                "messages": [],
                "student_profile": None
            }
        
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
            if st.button("🚪 Logout", use_container_width=True):
                # Clear demo user data
                if "demo_user" in st.session_state:
                    del st.session_state.demo_user
                st.session_state.username = ""
                st.session_state.user_data = {}
                st.logout()
                utils.go_to_page("landing")
        
        # Add back button with confirmation dialog
        if "show_exit_confirmation" not in st.session_state:
            st.session_state.show_exit_confirmation = False
        
        # Initial greeting when first arriving at this page
        if not st.session_state.onboard_state["messages"]:
            st.session_state.onboard_state = sally_graph.invoke(st.session_state.onboard_state)
            st.rerun()
        
        # Display conversation history
        lola_avatar = get_avatar_base64("assets/lola.png")
        messages = utils.convert_to_streamlit_messages(st.session_state.onboard_state["messages"])
        for message in messages:
            if message["role"] == "assistant":
                with st.chat_message(message["role"], avatar=f"data:image/png;base64,{lola_avatar}"):
                    st.write(message["content"])
            elif message["role"] == "user":
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
        # Process user input
        user_input = st.chat_input("Type your response here...")
        
        if user_input:
            st.session_state.onboard_state["messages"].append({"role": "user", "content": user_input})
            with st.spinner("Thinking..."):
                st.session_state.onboard_state = sally_graph.invoke(st.session_state.onboard_state)
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
