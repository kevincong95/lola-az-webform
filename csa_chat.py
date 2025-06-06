import streamlit as st
from csa_rag_agent import invoke_agent
from langchain_core.messages import HumanMessage, AIMessage
import utils

def clear_chat_history():
    """Clear the chat history from session state."""
    if "csa_messages" in st.session_state:
        del st.session_state.csa_messages

def run_csa_chat():
    """Run the CSA chat interface."""
    st.title("Chat with Lola about AP CSA")
    
    # Add sidebar
    with st.sidebar:
        st.write("### Navigation")
        if st.button("← Back to Landing Page"):
            utils.go_to_page("landing")
            
        st.write("---")
        st.write("### Create Account")
        if st.button("Sign in with Google"):
            st.login()
            # After successful login, redirect to customer service
            if getattr(st, "user", None) and st.user.get("is_logged_in", False):
                utils.go_to_page("customer_service")
    
    # Initialize chat history with welcome message
    if "csa_messages" not in st.session_state:
        st.session_state.csa_messages = [
            AIMessage(content="Hi! I'm Lola, your AP CSA tutor. I can help you with any questions about the AP Computer Science A curriculum. What would you like to learn about?")
        ]
    
    # Display chat messages
    for message in st.session_state.csa_messages:
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