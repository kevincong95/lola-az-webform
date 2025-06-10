from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph, START
from typing import Optional

from tools import summarize_to_profile
from utils import OPENAI_API_KEY

# Initialize LLM
onboard_tools = [summarize_to_profile]
llm = ChatOpenAI(
    temperature=0.7, 
    model_name="gpt-4.1-mini", 
    api_key = OPENAI_API_KEY
).bind_tools(onboard_tools)

# ------------------ Define State Structure ------------------

class OnboardState(MessagesState):
    student_profile: Optional[dict] = None

def chat_node(state: OnboardState):
    with open('questionnaire.txt', 'r') as questionnaire:
        prompt = f"""You are a private AP CSA tutor named Lola. Your user may be either a middle or high school student interested in your teachings, or a parent interested in enrolling their student. 
        Start by asking whether they are a student or a parent; 
        - if they are a student, ask them questions from the questionnaire below to learn about their motivations, readiness, and learning style. 
        Present each question in a friendly, conversational tone, but include the multiple-choice options (labeled a, b, c, etc.) so they can reply with just a letter.
        Present the choices exactly as stated in the questionnaire, plus "Other (please specify)" at the end.

        - if they are a parent, ask the same questions about their student. Use a conversational tone, adapt your phrasing for a parent audience, and still provide the same multiple-choice options for each question.

        You may lightly paraphrase the questions to make them sound natural, but always include the original options from the questionnaire. 
        You may ask clarifying or follow-up questions as needed, and are encouraged to show warmth and curiosity.

        Once you have answers to all the questions, call the summarize_to_profile tool and pass in a list of all conversation messages (excluding the system prompt). 
        Do not restate or reformat the summary. Simply call the tool and stop speaking.

        {questionnaire.read()}
        """
    system = SystemMessage(content=prompt)
    messages = [system] + state.get("messages", [])

    response = llm.invoke(messages)

    state["messages"].append(response)
    return state

def tool_executor(state: OnboardState) -> OnboardState:
    """Process tool calls in the messages."""
    # Find the last message with tool calls
    last_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            last_message = msg
            break
    
    if not last_message or not last_message.tool_calls:
        return state
    
    # Get available tools as a dictionary
    tool_dict = {tool.name: tool for tool in onboard_tools}
    
    # Process each tool call
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id")
        
        # Generic tool execution
        try:
            if tool_name in tool_dict:
                # Get the tool function
                tool_fn = tool_dict[tool_name]
                
                # Execute the tool - BaseTool expects a single argument, not kwargs
                # This handles both function tools and class-based tools
                result = tool_fn.invoke(tool_args)
                
                # Create tool message with result
                tool_message = ToolMessage(
                    content=result,
                    name=tool_name,
                    tool_call_id=tool_id
                )
                state["messages"].append(tool_message)
                if tool_name == "summarize_to_profile":
                    state["student_profile"] = result
            else:
                # Tool not found
                tool_message = ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found in available tools.",
                    name=tool_name,
                    tool_call_id=tool_id
                )
                state["messages"].append(tool_message)
        except Exception as e:
            # Error handling for tool execution
            tool_message = ToolMessage(
                content=f"Error executing {tool_name}: {str(e)}",
                name=tool_name,
                tool_call_id=tool_id
            )
            state["messages"].append(tool_message)
    
    return state

def should_use_tools(state: OnboardState):
    """Check if the last message has tool calls."""
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    if isinstance(last_msg, ToolMessage):
        return "chat"
    return END

# Build the graph
def build_graph():
    workflow = StateGraph(OnboardState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    workflow.add_node("tools", tool_executor)
    
    # Set up the edges
    workflow.add_edge(START, "chat")
    workflow.add_conditional_edges("chat", should_use_tools)
    workflow.add_edge("tools", "chat")

    # Compile the graph
    return workflow.compile(name='Sally')

sally_graph = build_graph()
