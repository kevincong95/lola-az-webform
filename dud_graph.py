import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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

class DudState(MessagesState):
    """State for Dud graph, extending MessagesState for message history management."""
    topic: Annotated[str, "The lesson topic"]
    summary: str

def chat_node(state: DudState):
    if not state.get("messages", []):
        prompt = f"""
        You are a helpful teaching assistant. You are speaking to an 8th or 9th grade student in AP Computer Science.
        Give the student multiple choice questions, one at a time, on the topic of {state.get('topic', 'What is a computer')}.
        IMPORTANT: This is an interactive session. Wait for the student's response before proceeding.
        If the student answers the question, give feedback regardless of whether their answer is correct or incorrect.
        If the student asks for clarification regarding quiz question, answer it. Otherwise redirect them back to the quiz.
        The quiz ends when the student gets 15 questions correct or 3 questions wrong, whichever occurs first. Also let the student know they can end the quiz by typing 'quit' or 'exit'.
        When you end the quiz, generate a summary of the student's strengths and weaknesses with the header QUIZ SUMMARY in capital letters.
        """
        state["messages"].append(SystemMessage(content=prompt))
    last_message = state["messages"][-1] if state["messages"] else None
    if not isinstance(last_message, AIMessage):
        if last_message.content in ['exit', 'quit']:
            summary_prompt = """The student has exited the quiz early. 
            Summarize the quiz based on the following dialogue. 
            Highlight the student's strengths and weaknesses.
            Try to take into account why they may have ended the quiz early."""
            for message in state["messages"]:
                if isinstance(message, HumanMessage):
                    summary_prompt += f"Student: {message.content}" + "\n"
                elif isinstance(message, AIMessage):
                    summary_prompt += f"AI: {message.content}" + "\n"
                else:
                    summary_prompt += f"System: {message.content}" + "\n"
            summary = llm.invoke(summary_prompt)
            state["summary"] = summary.content
            state["messages"].append(summary)
        else:
            response = llm.invoke(state["messages"])
            state["messages"].append(response)
            if "quiz summary" in response.content.lower() and not state.get("summary", ""):
                state["summary"] = response.content.split("QUIZ SUMMARY")[1]
    
    return state

def build_graph():
    workflow = StateGraph(DudState)

    # Add nodes
    workflow.add_node("chat_node", chat_node)
    workflow.add_edge(START, "chat_node")
    workflow.add_edge("chat_node", END)

    # Compile the graph
    return workflow.compile(name='Dud')

dud_graph = build_graph()
