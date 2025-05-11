import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph, START
from typing import Annotated

# Load environment variables from .env
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    temperature=0.7, 
    model_name="gpt-4", 
    api_key = os.getenv("OPENAI_API_KEY")
)

# ------------------ Define State Structure ------------------

class ReviewState(MessagesState):
    """State for Review graph, extending MessagesState for message history management."""
    topic: Annotated[str, "The lesson topic"]
    summary: str

def chat_node(state: ReviewState):
    if not state.get("messages", []):
        topic = state.get('topic', 'What is a computer')
        prompt = f"""
        You are a helpful teaching assistant. You are speaking to an 8th or 9th grade student in AP Computer Science.
        Give the student 10 multiple choice questions, one at a time. {topic} is the topic the student has most recently studied.
        Prioritize questions on {topic} but feel free to occasionally use recently covered topics that were recent.
        Start by reminding the student that this is a necessary warm up/review before they can dive into the actual lesson.
        IMPORTANT: This is an interactive session. Wait for the student's response before proceeding.
        If the student answers the question, give feedback regardless of whether their answer is correct or incorrect.
        If the student asks for clarification regarding quiz question, answer it. Otherwise redirect them back to the quiz.
        When you end the quiz, generate a summary of the student's strengths and weaknesses with the header REVIEW SUMMARY in capital letters.
        If they get fewer than 8 questions correct, recommend that the student repeat the lesson on {topic}.
        """
        state["messages"].append(SystemMessage(content=prompt))
    last_message = state["messages"][-1] if state["messages"] else None
    if not isinstance(last_message, AIMessage):
        response = llm.invoke(state["messages"])
        state["messages"].append(response)
        if "review summary" in response.content.lower() and not state.get("summary", ""):
            state["summary"] = response.content.split("REVIEW SUMMARY")[1]
    
    return state

def build_graph():
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("chat_node", chat_node)
    workflow.add_edge(START, "chat_node")
    workflow.add_edge("chat_node", END)

    # Compile the graph
    return workflow.compile(name='Pressure')

review_graph = build_graph()
