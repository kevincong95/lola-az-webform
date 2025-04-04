from typing import Annotated, Literal, Optional, Union
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END

from cassie_graph import lesson_graph, LessonState
from dud_graph import dud_graph, DudState

class PrimaryState(MessagesState):
    """Global state for the tutoring assistant."""
    user_topic: str  # Topic for Cassie Graph (if needed)
    session_type: Literal["lesson", "quiz"]  # Tracks subgraph type
    subgraph_state: Union[LessonState, DudState]  # Active subgraph state
    next_step: Literal["cassie_entry", "dud_entry"]


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
    """Primary assistant fetches user details, greets them, and introduces the next lesson."""
    
    # 1️⃣ Fetch user profile
    if not state['subgraph_state']:
        user_profile = fetch_user_profile(state)
        name = user_profile["name"]
        next_topic = user_profile["next_topic"]

        # 2️⃣ Fetch lesson plan
        lesson_info = fetch_lesson_plan(state)
        lesson_intro = lesson_info["lesson_overview"]
        default_lesson_state = {"topic": next_topic, "lesson_plan": lesson_intro}
        default_dud_state = {"topic": next_topic}

        # 3️⃣ Generate greeting and introduction
        greeting = f"Hello {name}! Ready to learn? Today, we’ll explore **{next_topic}**. {lesson_intro}"

    # 4️⃣ Determine where to route next
    route = route_to_subgraph(state)

    if route == 'cassie_entry':
        new_subgraph_state = default_lesson_state
    else:
        new_subgraph_state = default_dud_state

    return {
        "message": greeting,
        "next_step": route,
        "subgraph_state": new_subgraph_state
    }

def route_to_subgraph(state: PrimaryState):
    """Routes user to the correct subgraph based on intent."""
    # Access state as a dictionary
    subgraph_state = state.get("subgraph_state", None)
    session_type = state.get("session_type", "lesson")  # Default to lesson
    
    # For the invalid session type test
    if session_type not in ["lesson", "quiz"]:
        raise ValueError(f"Invalid session type: {session_type}")
        
    if subgraph_state and "summary" in subgraph_state:
        summary = subgraph_state["summary"]
        # LLM determines if this is a lesson request or a quiz request
        decision = llm.invoke(f"Determine whether the student needs a tutoring lesson (response: lesson) or a quiz (response: quiz) based on their most recent progress summary: {summary}").content.strip().lower()
        if "lesson" in decision:
            return "cassie_entry"
        elif "quiz" in decision:
            return "dud_entry"
    
    # Default routing based on session_type
    if session_type == "lesson":
        return "cassie_entry"
    else:  # session_type == "quiz"
        return "dud_entry"

def cassie_entry(state: PrimaryState):
    if not isinstance(state["subgraph_state"], LessonState):
        return state
    response = lesson_graph.invoke(state["subgraph_state"])
    return {**state, "subgraph_state": response}

def dud_entry(state: PrimaryState):
    if not isinstance(state["subgraph_state"], DudState):
        return state
    response = dud_graph.invoke(state["subgraph_state"])
    return {**state, "subgraph_state": response}

primary_graph = StateGraph(PrimaryState)

# Nodes
primary_graph.add_node("primary_assistant", primary_assistant)
primary_graph.add_node("cassie_entry", cassie_entry)
primary_graph.add_node("dud_entry", dud_entry)

# Routing Logic
primary_graph.add_edge(START, "primary_assistant")
primary_graph.add_conditional_edges("primary_assistant", lambda state: state["next_step"])

# Allow users to return after completing a session
primary_graph.add_edge("cassie_entry", "primary_assistant")
primary_graph.add_edge("dud_entry", "primary_assistant")

# Compile
primary_graph = primary_graph.compile()

# initial_state = PrimaryState(messages=[{"role": "user", "content": "recursion"}])
# output = primary_graph.invoke(initial_state)
# print(output)