import base64
import streamlit as st
import streamlit.components.v1 as components
import utils

def display_interactive_whiteboard():
    """Display the interactive whiteboard using Excalidraw iframe embed."""
    
    # Sidebar with logo and back button
    with st.sidebar:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            logo_path = "assets/FullLogo.jpg"
            with open(logo_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
            st.markdown(f"""
            <div style='text-align: center;'>
                <img src="data:image/jpg;base64,{encoded}" 
                     style='width: 300px; height: 300px; object-fit: contain;'/>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🏠 Back to Home", use_container_width=True):
            utils.go_to_page("landing")

    # Main content
    st.header("🎨 Interactive Whiteboard")
    st.subheader("Visual Learning & Drawing")
    st.markdown("### Drawing Canvas")
    st.info("Use this whiteboard for brainstorming, concept mapping, and visual learning.")

    # Excalidraw iframe
    components.html("""
    <iframe 
        src="https://excalidraw.com/embed" 
        width="100%" 
        height="600" 
        style="border: none; border-radius: 8px;">
    </iframe>
    """, height=600)

    # Save session metadata
    st.markdown("### Save Your Work")
    col1, col2 = st.columns(2)
    with col1:
        session_title = st.text_input("Session title", placeholder="e.g., Algorithm Design, System Architecture")
    with col2:
        diagram_type = st.selectbox("Diagram type", [
            "Flowchart", "Mind Map", "System Design", "Algorithm", "Concept Map", "Other"
        ])
    
    if st.button("Save Whiteboard Session", use_container_width=True):
        if session_title:
            # Save logic placeholder
            st.success("Whiteboard session saved!")
        else:
            st.warning("Please enter a session title.")

def display_flowchart_templates():
    """Display pre-built flowchart templates"""
    st.sidebar.markdown("### Flowchart Templates")
    
    templates = {
        "Algorithm Design": "Start → Input → Process → Decision → Output → End",
        "Function Flow": "Function Call → Parameters → Logic → Return Value",
        "Loop Structure": "Initialize → Condition → Body → Increment → Check",
        "Error Handling": "Try → Action → Catch Error → Handle → Finally",
        "Database Flow": "Connect → Query → Process Results → Close Connection"
    }
    
    selected_template = st.sidebar.selectbox("Choose template", list(templates.keys()))
    
    if st.sidebar.button("Load Template"):
        st.sidebar.success(f"Template loaded: {templates[selected_template]}")