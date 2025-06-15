import streamlit as st
import utils

# Page registry mapping page names to their display functions
PAGE_REGISTRY = {
    "landing": None,  # Will be handled directly
    "customer_service": lambda: __import__("customer_service").display_customer_service(),
    "csa_chat": lambda: __import__("csa_chat").run_csa_chat(),
    "main": lambda: __import__("lola_streamlit").lola_main(),
    "simple_ide": lambda: __import__("simple_ide").display_simple_ide(),
    "whiteboard": lambda: __import__("whiteboard").display_interactive_whiteboard()
}

def get_page_title(page_name: str) -> str:
    """Get the title for a given page."""
    titles = {
        "landing": "Welcome to Lola - Your AP CSA Learning Assistant",
        "customer_service": "Talk to Lola - Customer Service",
        "csa_chat": "Learn AP CSA with Lola",
        "main": "Lola - Learning Hub",
        "simple_ide": "Lola - Code Practice",
        "whiteboard": "Lola - Whiteboard"
    }
    return titles.get(page_name, "Lola - AP CSA Learning Assistant")

def display_landing():
    """Display the landing page."""
    # Check if user is logged in after Google authentication
    if getattr(st, "user", None) and st.user.get("is_logged_in", False):
        utils.go_to_page("customer_service")
        return

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
        
        # Show Google login button
        if st.button("🔐 Log in with Google", use_container_width=True):
            st.login()
    
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
        
        if st.button("Chat with Lola - I speak 中文 or your preferred language!", key="chat_button", use_container_width=True, type="primary"):
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

def main():
    """Main entry point for the application."""
    # Initialize session state for page navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "landing"
    
    # Set page title
    st.set_page_config(
        page_title=get_page_title(st.session_state.current_page),
        page_icon="🕸️",
        layout="wide"
    )
    
    # Get current page
    current_page = st.session_state.current_page
    
    # Display the appropriate page
    if current_page == "landing":
        display_landing()
    else:
        # Lazy load and display the requested page
        page_display = PAGE_REGISTRY.get(current_page)
        if page_display:
            page_display()
        else:
            st.error(f"Page '{current_page}' not found")
            st.session_state.current_page = "landing"
            st.rerun()

if __name__ == "__main__":
    main()
