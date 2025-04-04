import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph, START
from openinference.instrumentation.openai import OpenAIInstrumentor
from phoenix.otel import register
from typing import Annotated, List

# Load environment variables and initialize LLM
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0, model_name="gpt-4")
PHOENIX_API_KEY = os.getenv("PHOENIX_API_KEY")
os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={PHOENIX_API_KEY}"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"

# configure the Phoenix tracer
tracer_provider = register(
  project_name="fastlearn",
  endpoint="https://app.phoenix.arize.com/v1/traces"
)
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

class LessonState(MessagesState):
    topic: Annotated[str, "The lesson topic", "input"]
    lesson_plan: List[str]
    current_step: int
    current_question: str
    attempts: int
    summary: str
    user_answer: Annotated[str, "User's answer to current question", "input"]
    awaiting_answer: bool  # State flag for UI flow control

def generate_lesson_plan(state: LessonState) -> LessonState:
    response = llm.invoke(
        f"Create a lesson plan for {state['topic']} with 3 key teaching points. Return each teaching point in one sentence and no other formatting text."
    ).content
    lesson_plan = [line for line in response.split("\n") if line]
    return {**state, "lesson_plan": lesson_plan, "current_step": 0}

def ask_question(state: LessonState) -> LessonState:
    step = state["current_step"]
    
    question = llm.invoke(f"Generate a multiple-choice question for: {state['lesson_plan'][step]}").content
    messages = state.get("messages", []) + [
        {"role": "assistant", "content": f"🤔 **Question:** {question}"}
    ]
    return {**state, "current_question": question, "messages": messages, "awaiting_answer": True, "user_answer": ""}

def check_answer(state: LessonState) -> LessonState:
    if not state.get("user_answer"):
        return {**state, "awaiting_answer": True}
    
    current_step = state["current_step"]
    user_answer = state["user_answer"]
    
    feedback = llm.invoke(f"Is '{user_answer}' the correct answer for: {state['current_question']}? Respond with the word correct or incorrect followed by an explanation.").content
    
    is_correct = feedback.lower().startswith('correct')
    new_step = current_step
    
    if is_correct:
        new_step = current_step + 1
        attempts = 0
    else:
        attempts = state.get("attempts", 0) + 1

    messages = state["messages"] + [
        {"role": "user", "content": user_answer},
        {"role": "assistant", "content": feedback}
    ]

    # Check if we've completed all steps or exhausted attempts
    if new_step >= len(state["lesson_plan"]) or attempts > 1:
        summary = llm.invoke(f"""Summarize the student's learning. 
        Mention strengths, mistakes, and improvement areas. 
        Here is the message history: {messages}""").content
        
        return {**state, 
                "messages": messages, 
                "current_step": new_step,
                "attempts": attempts, 
                "summary": summary,
                "user_answer": "", 
                "awaiting_answer": False}
    
    # Return updated state with new step value
    return {**state, 
            "messages": messages, 
            "current_step": new_step,
            "attempts": attempts, 
            "user_answer": "",  # Clear the answer for the next question
            "awaiting_answer": False}

def should_continue(state: LessonState):
    if state.get("awaiting_answer", False):
        return END
    if state.get("summary", False):
        return END
    
    # Check if we have more steps to go
    if state["current_step"] < len(state["lesson_plan"]):
        return "ask_question"
    else:
        return END

# Define a function to determine the starting point
def get_entry_point(state: LessonState):
    if state.get("user_answer", "") and not state.get("awaiting_answer", False):
        return "check_answer"  # Resume from check_answer if we have a user answer
    elif len(state.get("lesson_plan", [])) > 0:
        return "ask_question"  # Jump to asking questions if we already have a lesson plan
    else:
        return "generate_lesson_plan"  # Start from the beginning for a new session

# Define the graph
lesson_graph = StateGraph(LessonState)

# Add nodes
lesson_graph.add_node("generate_lesson_plan", generate_lesson_plan)
lesson_graph.add_node("ask_question", ask_question)
lesson_graph.add_node("check_answer", check_answer)

# Define edges
lesson_graph.add_conditional_edges(START, get_entry_point)
lesson_graph.add_edge("generate_lesson_plan", "ask_question")
lesson_graph.add_edge("ask_question", "check_answer")
lesson_graph.add_conditional_edges("check_answer", should_continue)

# Compile the graph
lesson_graph = lesson_graph.compile()