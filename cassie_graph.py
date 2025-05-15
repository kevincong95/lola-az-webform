import tools

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, START, StateGraph
from typing import List

from utils import OPENAI_API_KEY

# Initialize the language model
cassie_tools = [tools.fetch_lesson_plan, tools.generate_summary]
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    api_key=OPENAI_API_KEY
).bind_tools(cassie_tools)

# Define the state structure
class LessonState(MessagesState):
    """The state of our graph."""
    topic: str
    messages: List[BaseMessage]
    lesson_plan: str | None
    summary: str | None

def chat_node(state: LessonState) -> LessonState:
    """Handle regular chat interactions."""
    # Get the last message
    system = SystemMessage(content="""You are giving a 1-1 online tutoring session to teach a student in 8th or 9th grade. 
        IMPORTANT:
        - Your explanations must be appropriate for a middle school student's age and skill level.
        - This is an interactive session. Only do one part at a time.
        - Do not move to the next part until the student says they are ready.
        - After each teaching point, ask all the corresponding comprehension check questions at once.
        - If the student gets all the questions correct, move to the next teaching point.
        - If the student gets any questions wrong, explain the teaching point in a different way, emphasizing their mistakes.
        - If the student fails to clear the teaching point in 2 attempts, or if they say "quit" or "exit", end the lesson early.
        - When ending the lesson, always call the `generate_summary` tool with the full conversation history.
        """)
    if not state.get("messages", []):
        initial = HumanMessage(content=f"""
        The topic for today is: {state.get('topic', 'What is a computer')}.

        Before you begin the lesson, check whether a lesson plan already exists. If not, fetch one using the `fetch_lesson_plan` tool.
        """)
        response = llm.invoke([system, initial])
    else:
        messages = [system] + state["messages"]
        response = llm.invoke(messages)
    state["messages"].append(response)
    return state

def tool_executor(state: LessonState) -> LessonState:
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
    tool_dict = {tool.name: tool for tool in cassie_tools}
    
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
                
                # Store lesson plan or summary in state
                if tool_name == "fetch_lesson_plan":
                    state["lesson_plan"] = result
                if tool_name == "generate_summary":
                    state["summary"] = result
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

def should_use_tools(state: LessonState):
    """Check if the last message has tool calls."""
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    if isinstance(last_msg, ToolMessage):
        return "chat"
    return END

# Build the graph
def build_graph():
    workflow = StateGraph(LessonState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    workflow.add_node("tools", tool_executor)
    
    # Set up the edges
    workflow.add_edge(START, "chat")
    workflow.add_conditional_edges("chat", should_use_tools)
    workflow.add_edge("tools", "chat")
    
    return workflow.compile(name='Cassie')

# Create the graph
lesson_graph = build_graph()