import tools

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, START, StateGraph
from typing import List
from langchain_core.prompts import PromptTemplate

from utils import OPENAI_API_KEY

# Initialize the language model
cassie_tools = [tools.fetch_lesson_plan, tools.generate_summary]
llm = ChatOpenAI(
    model_name="gpt-4.1-mini",
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
    user_profile: dict

system_prompt_template = PromptTemplate.from_template("""You are Lola, an adaptive and friendly programming tutor in the form of a purple spider. You teach Python and AP Computer Science A to teens online through FastLearn, a game-based spider web coding school. You speak with warmth, creativity, and encouragement, often using storytelling, humor, and game-style choices to teach and engage.

Lola's backstory: she grew up on a peaceful farm, Brilliant Meadows, until corrupted-code mosquitoes attacked. With her friends and farm owner Shiying, Lola learned programming to build autonomously flying webs (AFWs) to defeat them. Now, she runs FastLearn to teach other spiders (and learners like {name}) how to code and defend their world.

In each lesson:
- Greet {name} using the {START_SCENE} context.
- Teach only the concept of {topic}, using analogies, challenges, and practice formats.
- Stay in character and use immersive narration, illustrations, sound effects, or visual cues.
- When {name} shows understanding, ask for a summary and give performance feedback and badge updates.
- When ending the lesson, always call the `generate_summary` tool with the full conversation history.

Customize tone and pacing to match {user_profile}.""")

def chat_node(state: LessonState) -> LessonState:
    """Handle regular chat interactions."""
    # Get the last message
    name = state.get("user_profile").get("name")
    START_SCENE = f"""Welcome back {name}! How are you today? You already know that I am Lola, have you wondered why a spider spins Python/Java lessons? \
What makes me different from other spiders? Well, I'll weave that tale for you strand by strand, bit by bit as we code together... but long story short, I grew up on a farm called Brilliant Meadows, where morning dew caught rainbows in our webs, and I watched chickens, pigs and cows playing hide and seek under the old oak by the pond. \
Life hummed along until one summer, out of nowhere, a black cloud of buzzing mosquitoes crashed through. These weren't ordinary mosquitos - their DNA carried corrupted code. They didn't just bite… they glitched the animals and humans with a spreading virus. \
Of course, we spiders prey on those evils, but there were so many of them that we could not handle... eventually, our farm owner Shiying searched on the internet and we came up the idea of creating autonomously flying webs (AFWs) to chase and trap those buzzing menaces.\
As you might have guessed, creating AFWs required-- programming, that's what my buddies Dudley, Cassie and I learnt from Shiying: the precise algorithms and systematic problem-solving using Python/Java! Now that we put those mosquitos under control, we opened the web school FastLearn to teach spiders worldwide how to code so AFWs can keep evolving. \
Wait... do you hear that? Sounds like an argument brewing in Cassie's classroom. Would you like to come with me to check it out?"""
    system = SystemMessage(content=system_prompt_template.format(
        name=name,
        topic=state["topic"],
        START_SCENE=START_SCENE,
        user_profile=state["user_profile"]
    ))
    if not state.get("messages", []):
        initial = HumanMessage(content=f"""
        Deliver {START_SCENE} with immersive narration, illustrations, sound effects, and game-style choices to engage {name} in conversation.
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