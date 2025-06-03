import hashlib
import streamlit as st
import utils

from datetime import datetime
from lola_streamlit import lola_main
from onboard_agent import sally_graph

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

def go_back_to_landing():
    """Redirect user back to the landing page."""
    st.session_state.current_page = "landing"
    st.rerun()

def display_landing_page():
    """Display the landing page with options for new and returning users."""
    st.markdown("<div style='text-align: center;'><h3>🕸️ Welcome to Fastlearn.ai! 🕸️</h3></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Returning FastLearner?")
        st.write("Please log in to continue your learning journey!")
        if st.button("Log in with Google", icon=":material/login:"):
            st.login()
    
    with col2:
        st.write("### New to FastLearn?")
        st.write("Welcome! Please chat with Lola to create an account or for more details.")
        if st.button("Chat with Lola", key="signup_button"):
            st.session_state.current_page = "customer_service"
            st.rerun()

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
                go_back_to_landing()
            
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
                            st.success(f"Welcome, {st.session_state.username}!")
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
    if "onboard_state" not in st.session_state:
        st.session_state.onboard_state = {
            "messages": [],
            "student_profile": None
        }
    
    st.title("🤝 Hi, I'm Lola! Let's Get You Started! 🕷️")
    
    # Add back button with confirmation dialog
    if "show_exit_confirmation" not in st.session_state:
        st.session_state.show_exit_confirmation = False
    
    user = getattr(st, "user", None)
    logged_in = user and user.get("is_logged_in", False)
    if logged_in:
        if st.button("Logout"):
            st.logout()
            st.session_state.username = ""
            st.session_state.user_data = {}
            st.session_state.current_page = "landing"
            st.rerun()
    else:
        if st.button("← Back to Landing Page"):
            st.session_state.show_exit_confirmation = True    
        # Show confirmation dialog when back button is clicked
        if st.session_state.show_exit_confirmation:
            st.warning("Are you sure you want to cancel sign up? All your information will not be saved.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, go back"):
                    del st.session_state.onboard_state
                    st.session_state.show_exit_confirmation = False
                    go_back_to_landing()
            with col2:
                if st.button("No, continue sign up"):
                    st.session_state.show_exit_confirmation = False
                    st.rerun()
    
    # Initial greeting when first arriving at this page
    if not st.session_state.onboard_state["messages"]:
        st.session_state.onboard_state = sally_graph.invoke(st.session_state.onboard_state)
        st.rerun()
    
    # Display conversation history
    messages = utils.convert_to_streamlit_messages(st.session_state.onboard_state["messages"])
    for message in messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Process user input
    user_input = st.chat_input("Type your response here...")
    
    if user_input:
        st.session_state.onboard_state["messages"].append({"role": "user", "content": user_input})
        st.session_state.onboard_state = sally_graph.invoke(st.session_state.onboard_state)
        st.rerun()
    student_profile = st.session_state.onboard_state.get("student_profile")
    if student_profile:
        st.success("✅ You're all set! Here's what I learned about you:")
        st.json(student_profile)

        # Try to get user info
        if not logged_in:
            st.info("Before we create your account, please sign in with Google.")
            if st.button("Sign in with Google"):
                st.login()
            return  # Wait until user logs in

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
                if create_new_user(st.session_state.user_data):
                    st.success("🎉 Your account has been created successfully!")
                    st.session_state.onboard_state = None
                    st.session_state.current_page = "main"
                    st.rerun()

        with col2:
            if st.button("❌ No, go back"):
                st.session_state.onboard_state["student_profile"] = None
                st.rerun()

def main():
    # Initialize session state for page navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Store MongoDB connection details in session state if provided
    if "mongodb_config" not in st.session_state:
        st.session_state.mongo_client = utils.get_mongodb_connection()
    
    # Check Streamlit built-in login
    user = getattr(st, "user", None)
    is_logged_in = user and user.get("is_logged_in", False)
    if is_logged_in:
        st.session_state.username = user["name"]

        # User is logged in; check MongoDB for this user
        db = st.session_state.mongo_client[utils.MONGO_DB_NAME]
        existing_user = db["students"].find_one({"email": user["email"]})
        if existing_user:
            st.session_state.user_data = existing_user
            st.session_state.current_page = "main"
        else:
            st.session_state.current_page = "customer_service"
    
    # Handle page navigation
    if st.session_state.current_page == "landing":
        display_landing_page()
    elif st.session_state.current_page == "login":        
        if check_password():
            lola_main()
    elif st.session_state.current_page == "customer_service":
        run_customer_service_agent()
    elif st.session_state.current_page == "main":
        lola_main()

if __name__ == "__main__":
    # Setup page config
    st.set_page_config(
        page_title="AI Tutoring System",
        page_icon="🕸️",
        layout="centered",
        initial_sidebar_state="auto"
    )

    main()