import streamlit as st
from csa_rag_agent import invoke_agent
from langchain_core.messages import HumanMessage, AIMessage
import utils

def clear_chat_history():
    """Clear the chat history from session state."""
    if "csa_messages" in st.session_state:
        del st.session_state.csa_messages
    if "show_exit_dialog" in st.session_state:
        del st.session_state.show_exit_dialog

def run_csa_chat():
    """Run the CSA chat interface."""
    st.title("Chat with Lola about AP CSA")
    
    # Initialize session state for exit dialog
    if "show_exit_dialog" not in st.session_state:
        st.session_state.show_exit_dialog = False
    
    # Handle back button
    if st.button("← Back to Landing Page"):
        st.session_state.show_exit_dialog = True
    
    # Show exit dialog if back button was pressed
    if st.session_state.show_exit_dialog:
        st.warning("Do you really want to pause the chat? We can pick up where we left off if you like!")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Exit, save chat history"):
                utils.go_to_page("landing")
        with col2:
            if st.button("Exit, clear chat history"):
                clear_chat_history()
                utils.go_to_page("landing")
        with col3:
            if st.button("Continue Chatting"):
                st.session_state.show_exit_dialog = False
                st.rerun()
        return
    
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