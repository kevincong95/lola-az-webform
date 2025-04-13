import os
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json
from langgraph.graph import END, StateGraph

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize the language model
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define the state structure
class State(dict):
    """The state of our graph."""
    topic: str
    messages: List[BaseMessage]
    template: Dict[str, Any] | None
    template_path: str | None
    lesson_plan: str | None

# Function to read JSON template
def read_json_template(file_path: str) -> Dict[str, Any] | str:
    """Read the JSON template file and return its contents"""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        return f"Error reading template file: {str(e)}"

# Node functions
def extract_file_path(state: State) -> State:
    """Extract file path from the latest user message."""
    # Get the last user message
    last_user_message = None
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            last_user_message = message.content
            break
    
    if last_user_message and ".json" in last_user_message:
        state["template_path"] = last_user_message
    
    return state

def load_template(state: State) -> State:
    """Load the template from the file path."""
    if state.get("template_path"):
        template = read_json_template(state["template_path"])
        if isinstance(template, dict):
            state["template"] = template
        else:
            # It's an error message
            state["template"] = None
            # Add an error message to the conversation
            state["messages"].append(AIMessage(content=f"I couldn't load that template. {template}"))
    
    return state

def route_based_on_template(state: State) -> str:
    """Determine the next node based on whether we have a template."""
    if state.get("lesson_plan"):
        print('DEBUG: Routing to END')
        return END
    else:
        print('DEBUG: Routing to execute_lesson_plan')
        return "execute_lesson_plan"

def execute_lesson_plan(state: State) -> State:
    """Execute a lesson plan specified in the template."""
    if state.get("template"):
        template_str = json.dumps(state["template"], indent=2)
        
        prompt = f"""
        Using this JSON template as a structure:
        {template_str}
        
        Execute the provided lesson plan in a 1-1 online tutoring setting to teach an 8th or 9th grader this topic: {state.get('topic', 'What is a computer')}.
        Only do one part at a time. Do not move to the next part until the student says they are ready. 
        Include the video link (https://www.youtube.com/watch?v=Cu3R5it4cQs) in the introduction part.
        When going through each individual teaching point, make sure to ask all the corresponding comprehension check questions at once. 
        If the student gets all the questions correct, move to the next teaching point. Otherwise, explain the teaching point in a different way, emphasizing the student's mistakes. 
        If the student isn't able to clear the teaching point in 2 attempts, just end the lesson.
        """
        
        result = llm.invoke([SystemMessage(content="You are a helpful teaching assistant."), 
                      HumanMessage(content=prompt)])
        
        state["lesson_plan"] = result.content
        state["messages"].append(AIMessage(content=result.content))
    
    return state

def chat_node(state: State) -> State:
    """Handle regular chat interactions."""
    # Get the last message
    last_message = state["messages"][-1] if state["messages"] else None
    
    if isinstance(last_message, HumanMessage):
        # If we've created a lesson plan, tell the user
        system_content = "You are a helpful teaching assistant."
        if state.get("lesson_plan"):
            system_content += " You have already created a lesson plan for the user."
        
        response = llm.invoke(state["messages"] + [SystemMessage(content=system_content)])
        state["messages"].append(AIMessage(content=response.content))
    
    return state

# Build the graph
def build_graph():
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("human_input", chat_node)
    workflow.add_node("extract_file_path", extract_file_path)
    workflow.add_node("load_template", load_template)
    workflow.add_node("execute_lesson_plan", execute_lesson_plan)
    
    # Set up the edges
    workflow.add_edge("human_input", "extract_file_path")
    workflow.add_edge("extract_file_path", "load_template")
    
    workflow.add_conditional_edges(
        "load_template",
        route_based_on_template
    )
    workflow.add_edge("execute_lesson_plan", END)
    
    # Set the entry point
    workflow.set_entry_point("human_input")
    
    return workflow.compile()

# Create the graph
lesson_graph = build_graph()