import hashlib
import streamlit as st
import utils

from datetime import datetime
from lola_streamlit import lola_main

def create_new_user(username, password, user_data):
    """Create a new user in the database with provided information."""
    client = utils.get_mongodb_connection()
    if client is None:
        return False, "Could not connect to database."
    
    try:
        db = client[utils.MONGO_DB_NAME]
        users_collection = db['students']
        
        # Check if username already exists
        if users_collection.find_one({"username": username}):
            return False, "Username already exists. Please choose another."
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user document with additional info
        user_document = {
            "username": username,
            "password_hash": hashed_password,
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "user_type": user_data.get("user_type", "student"),
            "grade_level": user_data.get("grade_level", ""),
            "learning_goals": user_data.get("learning_goals", []),
            "coding_experience": user_data.get("coding_experience", "none"),
            "current_topic": user_data.get("recommended_topic", "What is a computer?"),
            "previous_topic": "",
            "parent_email": user_data.get("parent_email", ""),
            "interests": user_data.get("interests", [])
        }
        
        # Insert the new user
        users_collection.insert_one(user_document)
        return True, "User created successfully!"
    
    except Exception as e:
        return False, f"Error creating user: {e}"
    
    finally:
        client.close()

def go_back_to_landing():
    """Redirect user back to the landing page."""
    st.session_state.current_page = "landing"
    st.rerun()

def display_landing_page():
    """Display the landing page with options for new and returning users."""
    st.write("### 🕸️ Welcome to Fastlearn.ai! 🕸️")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Returning FastLearner?")
        st.write("Please log in to continue your learning journey!")
        if st.button("Log in with username", key="login_button", icon=":material/login:"):
            st.session_state.current_page = "login"
            st.rerun()
        if st.button("Log in with Google", icon=":material/login:"):
            st.login()
    
    with col2:
        st.write("### New to FastLearn?")
        st.write("Welcome! Currently I can tutor AP Comp Sci A, are you interested in more details?")
        if st.button("Chat with Lola", key="signup_button"):
            st.session_state.current_page = "customer_service"
            st.rerun()

# Authentication Functions
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
            
            username = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Log in with username and password"):
                # Connect to MongoDB
                client = utils.get_mongodb_connection()
                
                if client is None:
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

def run_customer_service_agent():
    """Handle the customer service agent conversation for onboarding new users."""
    if "cs_state" not in st.session_state:
        st.session_state.cs_state = {
            "step": 0,
            "data": {},
            "conversation": []
        }
    
    st.title("🤝 Let's Get You Started!")
    
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
            st.session_state.messages = []
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
                    del st.session_state.cs_state
                    st.session_state.show_exit_confirmation = False
                    go_back_to_landing()
            with col2:
                if st.button("No, continue sign up"):
                    st.session_state.show_exit_confirmation = False
                    st.rerun()
    
    # Display conversation history
    for message in st.session_state.cs_state["conversation"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Handle the conversation flow based on current step
    current_step = st.session_state.cs_state["step"]
    
    # Initial greeting when first arriving at this page
    if current_step == 0:
        greeting = """
        Are you taking AP CSA at school, or are you wondering if it is the right course for you? Why not join us for free to give it a try? \n
        Or are you are a parent and have questions about the AP CSA course? Just let me know! \n
        Welcome again and it’s a pleasure to meet you,
        """
        if logged_in:
            greeting += f"{user['name']}!"
        else:
            greeting += " may I know who you are?"
        st.session_state.cs_state["conversation"].append({"role": "assistant", "content": greeting})
        st.session_state.cs_state["step"] = 1
        st.rerun()
    
    # Process user input
    user_input = st.chat_input("Type your response here...")
    
    if user_input:
        # Add user message to conversation
        st.session_state.cs_state["conversation"].append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process based on current step
        if current_step == 1:  # Who is using the platform
            if "student" in user_input.lower():
                st.session_state.cs_state["data"]["user_type"] = "student"
                response = "Great! As a student, you'll be using our platform directly. What grade are you currently in at school?"
            elif "parent" in user_input.lower():
                st.session_state.cs_state["data"]["user_type"] = "parent"
                response = "Thanks for helping your child get set up! What grade is your child currently in at school?"
            else:
                response = "I'm not sure I understood. Could you clarify if you're a student who will be using the platform, or a parent setting up an account for your child?"
                st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
                st.rerun()
                return
                
            st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
            st.session_state.cs_state["step"] = 2
            
        elif current_step == 2:  # Grade level
            # Try to extract grade information
            grade_info = user_input.lower()
            st.session_state.cs_state["data"]["grade_level"] = grade_info
            
            response = f"Thanks for sharing that information. What are your main learning goals with programming and computer science? For example: basic computer skills, web development, game creation, preparing for AP Computer Science, etc."
            st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
            st.session_state.cs_state["step"] = 3
            
        elif current_step == 3:  # Learning goals
            st.session_state.cs_state["data"]["learning_goals"] = user_input
            
            response = "That's helpful to know! How would you describe your previous coding experience? (No experience, beginner, some experience, or experienced)"
            st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
            st.session_state.cs_state["step"] = 4
            
        elif current_step == 4:  # Coding experience
            st.session_state.cs_state["data"]["coding_experience"] = user_input
            
            # Determine recommended starting topic based on experience
            experience = user_input.lower()
            if "no" in experience or "none" in experience:
                recommended_topic = "What is a computer?"
            elif "beginner" in experience:
                recommended_topic = "Introduction to Programming Concepts"
            elif "some" in experience:
                recommended_topic = "Variables and Data Types"
            else:
                recommended_topic = "Functions and Control Flow"
                
            st.session_state.cs_state["data"]["recommended_topic"] = recommended_topic
            
            response = "Great! What topics or areas of technology interest you the most? (For example: robots, games, apps, websites, art, music, etc.)"
            st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
            st.session_state.cs_state["step"] = 5
            
        elif current_step == 5:  # Interests
            st.session_state.cs_state["data"]["interests"] = user_input
            
            # If parent, ask for email
            if st.session_state.cs_state["data"].get("user_type") == "parent":
                response = "Would you like to provide an email address where we can send progress updates about your child's learning? (This is optional)"
                st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
                st.session_state.cs_state["step"] = 6
            else:
                # Skip to account creation for students
                st.session_state.cs_state["step"] = 7
                account_creation_message = "Now let's create your account! Please choose a username and password."
                st.session_state.cs_state["conversation"].append({"role": "assistant", "content": account_creation_message})
                st.rerun()
                
        elif current_step == 6:  # Parent email (optional)
            if "@" in user_input and "." in user_input:
                st.session_state.cs_state["data"]["parent_email"] = user_input
                response = "Email saved. Thank you! Now let's create an account for your child."
            else:
                response = "No problem! Let's move on to creating an account for your child."
                
            st.session_state.cs_state["conversation"].append({"role": "assistant", "content": response})
            st.session_state.cs_state["step"] = 7
            
        elif current_step == 7:  # Show account creation form
            # This is a transition step - no direct processing here
            pass
            
        st.rerun()
    
    # After conversation reaches account creation step, show the form
    if current_step >= 7:
        st.divider()
        st.subheader("Create Your Account")
        
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username", key="new_username")
            new_password = st.text_input("Create a Password", type="password", key="new_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            submit_button = st.form_submit_button("Create Account")
            
            if submit_button:
                if not new_username or not new_password:
                    st.error("Please provide both username and password.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Create the new user
                    success, message = create_new_user(new_username, new_password, st.session_state.cs_state["data"])
                    
                    if success:
                        st.success("Account created successfully!")
                        
                        # Set up the user session
                        st.session_state.authentication_status = True
                        st.session_state.username = new_username
                        
                        # Setup user data for the main app
                        recommended_topic = st.session_state.cs_state["data"].get("recommended_topic", "What is a computer?")
                        st.session_state.user_data = {
                            "username": new_username,
                            "last_login": datetime.now(),
                            "current_topic": recommended_topic,
                            "previous_topic": ""
                        }
                        
                        # Reset onboarding state
                        final_message = f"Your account has been created! Based on your experience level, we recommend starting with the topic '{recommended_topic}'. You'll be redirected to the main application in a moment."
                        st.session_state.cs_state["conversation"].append({"role": "assistant", "content": final_message})
                        
                        # Add delay with a progress bar
                        progress_bar = st.progress(0)
                        import time
                        for i in range(100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)
                        
                        # Clear CS state and redirect to main app
                        del st.session_state.cs_state
                        st.session_state.current_page = "main"
                        st.rerun()
                    else:
                        st.error(message)

def main():
    # Initialize session state for page navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Store MongoDB connection details in session state if provided
    if "mongodb_config" not in st.session_state:
        st.session_state.mongodb_config = {
            "uri": utils.CONNECTION_STRING,
            "db_name": utils.MONGO_DB_NAME,
            "users_collection": "students"
        }
    
    # Check Streamlit built-in login
    user = getattr(st, "user", None)

    is_logged_in = user and user.get("is_logged_in", False)

    if is_logged_in:
        st.session_state.username = user["name"]

        # User is logged in; check MongoDB for this user
        client = utils.get_mongodb_connection()
        db = client[utils.MONGO_DB_NAME]
        
        existing_user = db["students"].find_one({"email": user["email"]})
        if existing_user:
            st.session_state.user_profile = existing_user
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