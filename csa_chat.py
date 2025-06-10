import base64
import streamlit as st
import utils

from csa_rag_agent import invoke_agent
from langchain_core.messages import HumanMessage, AIMessage

def clear_chat_history():
    """Clear the chat history from session state."""
    if "csa_messages" in st.session_state:
        del st.session_state.csa_messages

def get_avatar_base64(image_path):
    """Convert image to base64 for avatar display."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def run_csa_chat():
    """Run the CSA chat interface."""
    
    # Add sidebar with logo and navigation
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
                base64.b64encode(open("assets/FullLogo.jpg", "rb").read()).decode()
            ), unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### Navigation")
        if st.button("🏠 Back to Home", use_container_width=True):
            utils.go_to_page("landing")
            
        st.write("---")
        st.write("### Create Account")
        if st.button("Sign in with Google"):
            st.login()
            # After successful login, redirect to customer service
            if getattr(st, "user", None) and st.user.get("is_logged_in", False):
                utils.go_to_page("customer_service")
    
    # Main chat interface with custom styling
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #9747FF; font-size: 2.5rem; margin-bottom: 0.5rem;'>Chat with Lola</h1>
        <p style='font-size: 1.1rem; color: #CCCCCC;'>Your AP Computer Science A tutor is here to help</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history with welcome message
    if "csa_messages" not in st.session_state:
        st.session_state.csa_messages = [
            AIMessage(content="Hi! I'm Lola, your AP CSA tutor. I can help you with any questions about the AP Computer Science A curriculum. What would you like to learn about?")
        ]
    
    # Get Lola's avatar
    lola_avatar = get_avatar_base64("assets/lola.png")
    
    # Display chat messages
    for message in st.session_state.csa_messages:
        if isinstance(message, AIMessage):
            with st.chat_message("assistant", avatar=f"data:image/png;base64,{lola_avatar}"):
                st.write(message.content)
        else:
            with st.chat_message(message.type):
                st.write(message.content)
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about AP CSA!"):
        # Add user message to chat history
        st.session_state.csa_messages.append(HumanMessage(content=prompt))
        
        # Get AI response and add to chat history
        with st.spinner("Thinking..."):
            response = invoke_agent(st.session_state.csa_messages)
            st.session_state.csa_messages = response  # Replace entire message history with updated one
        
        # Rerun to update the display
        st.rerun() 