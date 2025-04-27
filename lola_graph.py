import time

from typing import Annotated, Literal, Optional, Union, Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END

from cassie_graph import lesson_graph, LessonState
from dud_graph import dud_graph, DudState

class PrimaryState(MessagesState):
    """Global state for the tutoring assistant."""
    awaiting_user_choice: bool
    user_topic: str  # Topic for the session
    session_type: Literal["lesson", "quiz"]  # Tracks subgraph type
    subgraph_state: Union[LessonState, DudState, None]  # Active subgraph state
    next_step: Optional[Literal["cassie_entry", "dud_entry", "summarize_and_route"]]
    recommended_session_type: Literal["lesson", "quiz"]


llm = ChatOpenAI(temperature=0, model_name="gpt-4")

@tool
def fetch_user_profile(state: PrimaryState):
    """Placeholder: Fetches user profile information."""
    return {"name": "Alex", "current_level": 2, "next_topic": "Loops in Python"}

@tool
def fetch_lesson_plan(state: PrimaryState):
    """Placeholder: Retrieves the lesson plan for the next topic."""
    return {"lesson_overview": "Loops help us repeat actions efficiently. Let's explore 'for' and 'while' loops!"}

def primary_assistant(state: PrimaryState):
    """Handles user messages and determines the next step."""
    
    # Prepare default states if needed
    if not state.get('subgraph_state'):
        topic = state.get("user_topic", "what is a computer")
        session_type = state.get("session_type", "lesson")
        
        if session_type == "lesson":
            default_state = {
                "topic": topic,
                "messages": state.get("messages", []),
                "template": None,
                "template_path": None,
                "lesson_plan": None
            }
        else:  # quiz
            default_state = {
                "topic": topic,
                "messages": state.get("messages", []),
                "correct_answers": 0,
                "mistakes": 0,
                "awaiting_answer": False,
                "current_question": "",
                "user_answer": ""
            }
        
        subgraph_state = default_state
    else:
        subgraph_state = state["subgraph_state"]
    
    # Determine routing
    next_step = route_to_subgraph(state)
    
    return {
        **state,
        "next_step": next_step,  # Set next_step for routing
        "subgraph_state": subgraph_state,
    }

def route_to_subgraph(state: PrimaryState) -> str:
    """Routes user to the correct subgraph based on intent."""
    # Check if the subgraph has a summary (which means it's completed)
    subgraph_state = state.get("subgraph_state", {})
    if subgraph_state and subgraph_state.get("summary"):
        # If we have a summary, check if we need to switch to a different session type
        return "summarize_and_route"  # Go to summarization node
    
    # First determine which session type we're in
    session_type = state.get("session_type", "lesson")
    
    # For invalid session type
    if session_type not in ["lesson", "quiz"]:
        raise ValueError(f"Invalid session type: {session_type}")
    
    # Route based on session type
    if session_type == "lesson":
        return "cassie_entry"
    else:  # session_type == "quiz"
        return "dud_entry"

def summarize_and_route(state: PrimaryState) -> Dict[str, Any]:
    """Analyzes the summary and determines the next session type, then presents the choice to the user."""
    subgraph_state = state.get("subgraph_state", {})
    summary = subgraph_state.get("summary", "")
    
    if not summary:
        # No summary available, keep current session type
        return {**state}
    
    # Use LLM to determine if student needs a lesson or quiz based on the summary
    prompt = f"""
    Based on the following summary of a student's performance, determine if they should:
    1. Continue with another lesson (if they need more practice or teaching)
    2. Take a quiz (if they seem ready to test their knowledge)
    
    Summary: {summary}
    
    Respond with just one word: 'lesson' or 'quiz'.
    """
    
    decision = llm.invoke(prompt).content.strip().lower()
    
    # Default to opposite of current session type if decision is unclear
    current_session_type = state.get("session_type", "lesson")
    if decision not in ["lesson", "quiz"]:
        # If the model doesn't give a clear answer, switch to the opposite type
        new_session_type = "quiz" if current_session_type == "lesson" else "lesson"
    else:
        new_session_type = decision
    
    # Create a message that includes the summary and routing decision, with options for the user
    if "quiz" in decision:
        new_session_type = "quiz"
        recommendation = "I recommend taking a quiz to test your knowledge."
    else:
        new_session_type = "lesson"
        recommendation = "I recommend continuing with more lessons to strengthen your understanding."
    
    # Create message that includes summary and presents options to the user
    message = f"""
    ## Session Summary
    {summary}

    ## Next Steps
    {recommendation}

    **What would you like to do?**
    - Reply with "Continue" to proceed with the {new_session_type}
    - Reply with "Exit" to end this session
    """
    
    # Create new subgraph state with the message
    new_subgraph_state = {
        "topic": state.get("user_topic", ""),
        "messages": [AIMessage(content=message)],
        "summary": summary,
    }
    
    # Return state with both the message for immediate display and the flag for user response handling
    return {
        **state,
        "message": message,  # For direct display in UI
        "subgraph_state": new_subgraph_state,
        "recommended_session_type": new_session_type,
        "awaiting_user_choice": True,  # Flag for the Streamlit app
        "next_step": END  # End the workflow here to let UI take over
    }

def cassie_entry(state: PrimaryState):
    """Entry point for the lesson plan subgraph."""
    # Ensure we have the proper state structure
    if not state.get("subgraph_state"):
        return state
    
    # Invoke lesson graph
    response = lesson_graph.invoke(state["subgraph_state"])
    
    # Check if we have a summary (lesson completed)
    has_summary = response and "summary" in response and response["summary"] is not None
    
    # Set next step based on summary presence
    next_step = "summarize_and_route" if has_summary else None
    
    # Return updated state
    return {**state, "subgraph_state": response, "next_step": next_step}

def dud_entry(state: PrimaryState):
    """Entry point for the quiz subgraph."""
    # Ensure we have the proper state structure
    if not state.get("subgraph_state"):
        return state
    
    # Invoke dud graph
    response = dud_graph.invoke(state["subgraph_state"])
    
    # Check if we have a summary (quiz completed)
    has_summary = response and "summary" in response and response["summary"] is not None
    
    # Set next step based on summary presence
    next_step = "summarize_and_route" if has_summary else None
    
    # Return updated state
    return {**state, "subgraph_state": response, "next_step": next_step}

# Function to determine next step
def determine_next_step(state: PrimaryState):
    """Determines the next step based on the current state."""
    next_step = state.get("next_step")
    if next_step is None:
        return END
    return next_step

# Create the graph
primary_graph = StateGraph(PrimaryState)

# Add nodes
primary_graph.add_node("primary_assistant", primary_assistant)
primary_graph.add_node("cassie_entry", cassie_entry)
primary_graph.add_node("dud_entry", dud_entry)
primary_graph.add_node("summarize_and_route", summarize_and_route)

# Routing Logic
primary_graph.add_edge(START, "primary_assistant")
primary_graph.add_conditional_edges("primary_assistant", determine_next_step)
primary_graph.add_conditional_edges("cassie_entry", determine_next_step)
primary_graph.add_conditional_edges("dud_entry", determine_next_step)
primary_graph.add_conditional_edges("summarize_and_route", determine_next_step)

# Compile
primary_graph = primary_graph.compile()