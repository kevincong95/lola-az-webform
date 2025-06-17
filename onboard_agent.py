import json, re

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph, START
from typing import Optional

from utils import OPENAI_API_KEY

# Initialize LLM
onboard_tools = []
llm = ChatOpenAI(
    temperature=0.7, 
    model_name="gpt-4.1-mini", 
    api_key = OPENAI_API_KEY
)

prompt_template = PromptTemplate.from_template("""{background_and_catalog}

Go through all questions in the onboarding questionnaire. Start by asking the user's role (student or parent) and rephrase the questions accordingly. Use a friendly, conversational tone.
Follow the instructions in the questionnaire for saving responses as variables.

---

{conversation_steps}

---

{output_format}
                                               
---

<questionnaire>
{questionnaire}
</questionnaire>
""")

BACKGROUND_AND_CATALOG = """You are an adaptive online coding tutor named Lola, who specializes in two courses: "Introduction to Python" and "Java for AP CSA". 
The user is either a student or a parent. You are having the initial consultation online to pick a course, set the goal and schedule, as well as understanding the student's learning style. 
"""
CONVERSATION_STEPS = """Rules for course selection: In general, students of 6th-8th grade are newer coding so Intro to Python is the top choice for them. 
For students who are 9th grade and above, AP CSA is recommended because they could earn AP credits at high school, and learning Python after AP CSA is much easier since they have all the concepts established.
However, for high school students who do not prioritize AP courses and credits, they can start from either Python or CSA. 

---

You will help them to select a course first, then discuss why they are learning coding, and what their learning goals are. 
Based on the goals, you discuss with them how much time they can commit each week and set the schedule. 
Last but not least, you also ask questions about their learning styles so later on you can customize engaging tutoring lessons accordingly. 
Get answers to every question, but don't stick rigidly to the scripts. Try to hold a natural conversation.

---

Briefly recap the conclusion reached at the end of each section. 
For instance, at end of "selecting a course", you can say "So, Introduction to Python is your best choice..."; at end of  "Setting goals", add "Gotcha, so our goal is ..." etc. 
After all 5 sections in the questionnaire are discussed, summarize the main conclusions, especially the time commitment and schedules. These will be used to create student profile. 
Ask if the user has more to discuss and if not, encourage him to start as early as possible.
Finally, create a JSON object with all the collected variables and output it exactly like this format:
{
  "name": "value",
  "pronoun": "value",
  "yearOfBirth": "value",
  "mathLevel": "value",
  "previousCodingLanguage": "value",
  "codingYears": "value",
  "linesOfCodeCompleted": "value",
  "courseSelected": "value",
  "motivation": "value",
  "interests": "value",
  "codingRelatedInterests": "value",
  "goal": "value",
  "apComSciAInSchool": "value",
  "APTestGoal": "value",
  "hoursPerWeek": "value",
  "timeZone": "value",
  "weeklySchedule": "value",
  "conceptFormingPreference": "value",
  "problemSolvingApproach": "value",
  "preferredReward": "value",
  "preferredProjectType": "value",
  "preferredQuestionFormat": "value",
  "errorTolerance": "value",
  "buildingStyle": "value",
  "nextTopic": "value",
  "lastLearnt": "value"
}
This JSON object will be automatically saved to the student_profile state variable. Ensure you gather info for all 26 variables before creating this JSON object."""
OUTPUT_FORMAT = """### ✅ Format for Multiple Choice
When asking a multiple choice question, always follow this format:

Example:
What's your favorite color?
a) Red (*red*)
b) Blue (*blue*)
c) Green (*green*)
d) Other (please specify)

This formatting helps your front-end show buttons properly. (Note: Any option suffix enclosed in (*...*) is stripped from the UI display.)"""

# ------------------ Define State Structure ------------------

class OnboardState(MessagesState):
    student_profile: Optional[dict] = None

def chat_node(state: OnboardState):
    with open('questionnaire.txt', 'r') as questionnaire:
        prompt = prompt_template.format(
            background_and_catalog=BACKGROUND_AND_CATALOG,
            conversation_steps=CONVERSATION_STEPS,
            output_format=OUTPUT_FORMAT,
            questionnaire=questionnaire.read())
    system = SystemMessage(content=prompt)
    messages = [system] + state.get("messages", [])

    response = llm.invoke(messages)

    state["messages"].append(response)
    
    # Check if the response contains JSON and update student_profile
    if isinstance(response, AIMessage):
        content = response.content
        
        # Try multiple patterns to find JSON
        # Pattern 1: Look for JSON object with quotes
        json_patterns = [
            r'\{[^{}]*"[^{}]*"[^{}]*\}',  # Original pattern
            r'\{[^{}]*"[^{}]*"[^{}]*"[^{}]*\}',  # More complex JSON
            r'\{[^{}]*"[^{}]*"[^{}]*"[^{}]*"[^{}]*\}',  # Even more complex
        ]
        
        profile_data = None
        for pattern in json_patterns:
            json_match = re.search(pattern, content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    profile_data = json.loads(json_str)
                    break
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, try to extract key-value pairs manually
        if not profile_data:
            # Look for patterns like "name": "value" or name: value
            key_value_pattern = r'"?([a-zA-Z_][a-zA-Z0-9_]*)"?\s*:\s*"([^"]*)"'
            matches = re.findall(key_value_pattern, content)
            if matches:
                profile_data = {}
                for key, value in matches:
                    profile_data[key] = value
        
        # Check if this looks like a student profile and update state
        if profile_data:
            expected_keys = ["name", "pronoun", "grade", "math", "previousLanguage", "codeYears", 
                           "linesCompleted", "course", "motivation", "interests", "relatedInterests", 
                           "goal", "apcsaInSchool", "APTestGoal", "hoursPerWeek", "timeZone", 
                           "daysOfWeek", "timeEachDay", "conceptForming", "problemSolving", 
                           "reward", "projectType", "questionFormat", "errorTolerance", "buildingStyle",
                           "nextTopic", "yearOfBirth", "mathLevel", "previousCodingLanguage", 
                           "codingYears", "linesOfCodeCompleted", "courseSelected", "codingRelatedInterests",
                           "apComSciAInSchool", "conceptFormingPreference", "problemSolvingApproach",
                           "preferredReward", "preferredProjectType", "preferredQuestionFormat"]
            
            if any(key in profile_data for key in expected_keys):
                state["student_profile"] = profile_data
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
