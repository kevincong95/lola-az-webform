from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph, START
from typing import Annotated, Optional
import os

# Load environment variables from .env
load_dotenv()

# Retrieve API key from environment
api_key = os.getenv("OPENAI_API_KEY")

# Initialize LLM
llm = ChatOpenAI(temperature=0, model_name="gpt-4")

# ------------------ Define State Structure ------------------

class DudState(MessagesState):
    """State for Dud graph, extending MessagesState for message history management."""
    topic: Annotated[str, "The lesson topic"]
    correct_answers: int
    mistakes: int
    golden_bridge: bool
    current_question: str
    user_answer: Annotated[str, "User's answer to current question", "input"]
    awaiting_answer: bool
    summary: str

# ------------------ Define Graph Nodes ------------------

# 1️⃣ Generate Question
def generate_question(state: DudState) -> DudState:
    """Generates a challenging multiple-choice question."""
    question = llm.invoke("Generate a difficult AP CS A multiple-choice question with 5 answer choices.").content
    
    messages = state.get("messages", []) + [
        {"role": "assistant", "content": f"❓ {question}"}
    ]
    
    return {
        **state,
        "current_question": question,
        "messages": messages,
        "awaiting_answer": True,
        "user_answer": ""
    }

# 2️⃣ Check Answer
def check_answer(state: DudState) -> DudState:
    """Checks if the user's answer is correct."""
    if not state.get("user_answer"):
        return {**state, "awaiting_answer": True}
    
    question = state["current_question"]
    user_answer = state["user_answer"]

    correctness_response = llm.invoke(f"Is '{user_answer}' the correct answer for: {state['current_question']}? Respond with the word correct or incorrect followed by an explanation.").content
    
    is_correct = correctness_response.lower().startswith('correct')
    
    correct_answers = state.get("correct_answers", 0) + int(is_correct)
    mistakes = state.get("mistakes", 0) + 1 - int(is_correct)
    
    messages = state["messages"] + [
        {"role": "user", "content": user_answer},
        {"role": "assistant", "content": correctness_response}
    ]
    
    # Check if we should generate a summary
    if mistakes >= 4 or (correct_answers >= 10 and mistakes <= 3):
        if correct_answers >= 10 and mistakes <= 3:
            # Golden Bridge passed
            summary = llm.invoke("Generate a summary congratulating the student for passing the Golden Bridge challenge and preparing them for the final test.").content
        else:
            # Too many mistakes
            summary = llm.invoke("Summarize the student's mistakes and what needs improvement.").content
        
        messages.append({"role": "assistant", "content": f"📄 **Summary:** {summary}"})
        
        return {
            **state,
            "messages": messages,
            "correct_answers": correct_answers,
            "mistakes": mistakes,
            "user_answer": "",
            "awaiting_answer": False,
            "summary": summary
        }
    
    return {
        **state,
        "messages": messages,
        "correct_answers": correct_answers,
        "mistakes": mistakes,
        "user_answer": "",
        "awaiting_answer": False
    }

# Define flow control functions
def should_continue(state: DudState):
    if state.get("awaiting_answer", False):
        return END
    if state.get("summary", False):
        return END
    
    return "generate_question"

# Define a function to determine the starting point
def get_entry_point(state: DudState):
    if state.get("user_answer", "") and not state.get("awaiting_answer", False):
        return "check_answer"  # Resume from check_answer if we have a user answer
    else:
        return "generate_question"  # Start from the beginning for a new session

# ------------------ Define Graph ------------------

dud_graph = StateGraph(DudState)

# Add nodes
dud_graph.add_node("generate_question", generate_question)
dud_graph.add_node("check_answer", check_answer)

# Define edges
dud_graph.add_conditional_edges(START, get_entry_point)
dud_graph.add_edge("generate_question", "check_answer")
dud_graph.add_conditional_edges("check_answer", should_continue)

# Compile the graph
dud_graph = dud_graph.compile()