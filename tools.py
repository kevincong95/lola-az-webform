import json, os
import utils

from langchain_community.document_loaders.mongodb import MongodbLoader
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from typing import List

# Initialize the language model
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    api_key=utils.OPENAI_API_KEY
)


@tool
def fetch_lesson_plan(topic: str):
    """Retrieve the lesson plan for the given topic."""
    if not topic:
        return json.dumps({
            "error": "No topic provided",
            "suggestion": "Please provide a topic for the lesson plan."
        })
    
    try:
        loader = MongodbLoader(
            connection_string=utils.CONNECTION_STRING,
            db_name=utils.MONGO_DB_NAME,
            collection_name="lesson_templates",
            filter_criteria={"topic_name": topic},
            field_names=["template"]
        )
        docs = loader.load()
        if docs:
            return docs[0].page_content
        return json.dumps({
            "error": f"No lesson plan found for topic: {topic}",
            "suggestion": "Please try a different topic or create a new lesson plan."
        })
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "suggestion": "There was an issue connecting to the database. Please try again later."
        })

@tool
def generate_summary(messages: List[BaseMessage]):
    """Generate a summary of the provided conversation."""
    if not messages:
        return json.dumps({
            "error": "No message history provided",
            "suggestion": "Please provide a message history to summarize."
        })
    try:
        summary_prompt = "Summarize the lesson based on the following dialogue. Highlight the student's strengths and weaknesses. \n"
        
        # Process the messages to extract content
        message_texts = []
        for message in messages:
            if isinstance(message, HumanMessage):
                message_texts.append(f"Student: {message.content}")
            elif isinstance(message, AIMessage):
                message_texts.append(f"AI: {message.content}")
            elif isinstance(message, ToolMessage):
                message_texts.append(f"Tool call: {message.name}")
            elif hasattr(message, "content") and hasattr(message, "type"):
                message_texts.append(f"{message.type.capitalize()}: {message.content}")
        
        # Add the extracted messages to the summary prompt
        summary_prompt += "\n".join(message_texts)
        
        # Generate summary using the LLM
        summary = llm.invoke(summary_prompt)
        if hasattr(summary, "content"):
            return summary.content
        return summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"