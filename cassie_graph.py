import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
import json
from langgraph.graph import END, StateGraph, START

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize the language model
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define the state structure for the lesson
class LessonState(dict):
    """The state of our tutorial lesson."""
    topic: str
    lesson_plan: List[Dict[str, Any]]
    current_step: int
    current_question: str
    attempts: int
    summary: str
    messages: List[Dict[str, str]]
    user_answer: str
    awaiting_answer: bool
    template: Optional[Dict[str, Any]] = None
    template_path: Optional[str] = None

# Node functions
def create_lesson_plan(state: LessonState) -> LessonState:
    """Create a structured lesson plan for the given topic."""
    topic = state["topic"]
    
    # Check if we already have a template
    if state.get("template"):
        template_str = json.dumps(state["template"], indent=2)
        prompt = f"""
        Using this JSON template as a structure:
        {template_str}
        
        Execute the provided lesson plan in a 1-1 online tutoring setting to teach an 8th or 9th grader this topic: What is a computer.
        Only do one part at a time. Do not move to the next part until the student says they are ready. 
        Include the video link (https://www.youtube.com/watch?v=Cu3R5it4cQs) in the introduction part.
        When going through each individual teaching point, make sure to ask all the corresponding comprehension check questions at once. 
        If the student gets all the questions correct, move to the next teaching point. Otherwise, explain the teaching point in a different way, emphasizing the student's mistakes. 
        If the student isn't able to clear the teaching point in 2 attempts, just end the lesson.
        """
    else:
        # Create a default lesson plan structure
        prompt = f"""
        Create a detailed lesson plan in a 1-1 online tutoring setting to teach an 8th or 9th grader this topic: 
        {topic}
        
        The lesson plan should be structured as a list of steps, where each step has:
        1. A title
        2. Content to explain to the student
        3. A question to check understanding
        4. The expected answer or key points
        
        Return the result as a JSON array.
        """
    
    # Generate the lesson plan
    system_prompt = "You are an expert educational content creator specialized in creating interactive lesson plans."
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ])
    
    try:
        # Try to parse the response as JSON
        lesson_plan = json.loads(response.content)
        state["lesson_plan"] = lesson_plan
    except:
        # If parsing fails, use a simpler approach
        state["messages"].append({"role": "assistant", "content": "I'm having trouble creating a structured lesson plan. Let me try a simpler approach."})
        
        # Create a simpler lesson plan with a fallback approach
        prompt = f"Create a simple 3-step lesson plan about {topic} for a middle school student. Each step should include what to teach and a question to ask."
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])
        
        # Create a manually structured lesson plan
        state["lesson_plan"] = [
            {
                "title": f"Introduction to {topic}",
                "content": f"Let's learn about {topic}. This is a fascinating subject that we'll explore together.",
                "question": f"Are you ready to learn about {topic}?",
                "answer": "Yes"
            },
            {
                "title": f"Basic concepts of {topic}",
                "content": f"The fundamental concepts of {topic} include...",
                "question": f"Can you name one important concept related to {topic}?",
                "answer": "Any reasonable concept"
            },
            {
                "title": f"Practicing with {topic}",
                "content": f"Now let's practice what we've learned about {topic}.",
                "question": f"How would you apply what you've learned about {topic}?",
                "answer": "Any reasonable application"
            }
        ]
    
    # Add introduction message
    state["messages"].append({
        "role": "assistant", 
        "content": f"I've prepared a lesson about {topic}. We'll go through it step by step. Let's get started!"
    })
    
    # Set the current step to 0 (beginning)
    state["current_step"] = 0
    state["awaiting_answer"] = True
    
    # Get the first step's content
    if state["lesson_plan"] and len(state["lesson_plan"]) > 0:
        first_step = state["lesson_plan"][0]
        # Present the content to the student
        content_message = f"### {first_step['title']}\n\n{first_step['content']}"
        state["messages"].append({"role": "assistant", "content": content_message})
        
        # Ask a question to check understanding
        question_message = f"**Question**: {first_step['question']}"
        state["messages"].append({"role": "assistant", "content": question_message})
        
        # Set the current question for evaluation
        state["current_question"] = first_step["question"]
    
    return state

def load_template(state: LessonState) -> LessonState:
    """Load a template if a path is provided."""
    if state.get("template_path"):
        try:
            with open(state["template_path"], 'r') as file:
                state["template"] = json.load(file)
                # Add a confirmation message
                state["messages"].append({
                    "role": "assistant", 
                    "content": f"I've loaded your template file. I'll use it to structure the lesson on {state['topic']}."
                })
        except Exception as e:
            # If we can't load the template, inform the user and continue without it
            state["template"] = None
            state["messages"].append({
                "role": "assistant", 
                "content": f"I couldn't load the template file due to an error: {str(e)}. I'll create a lesson plan without it."
            })
    
    return state

# Build the graph
def build_lesson_graph():
    workflow = StateGraph(LessonState)
    
    # Add nodes
    workflow.add_node("create_lesson_plan", create_lesson_plan)
    workflow.add_node("load_template", load_template)
    
    # Set up the edges
    workflow.add_edge("load_template", "create_lesson_plan")
    
    # Set the entry point based on whether we need to load a template
    workflow.add_conditional_edges(
        START,
        lambda state: "load_template" if state.get("template_path") else "create_lesson_plan",
        {
            "load_template": "load_template",
            "create_lesson_plan": "create_lesson_plan"
        }
    )
    
    # After creating the lesson plan, end the graph
    workflow.add_edge("create_lesson_plan", END)
    
    return workflow.compile()

# Create the lesson graph
lesson_graph = build_lesson_graph()