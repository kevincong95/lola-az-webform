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
    
@tool
def summarize_to_profile(messages: List[BaseMessage]):
    """
    Summarize what you've learned about the student from the conversation.
    Return only a valid JSON object with these fields:
        - grade_in_school (integer)
        - learner_type (e.g., when do they plan to take the AP CSA exam?)
        - goal (freeform)
        - main_obstacles (freeform)
        - lesson_frequency (number of sessions per week and preferred session duration)
        - teaching_methods (e.g., hands-on projects, repetition, visual aids, etc.)
        - self_motivated (do they enjoy learning beyond the curriculum?)
        - work_independently (do they thrive or struggle with solo work?)
        - time_management (how they manage deadlines and workload)
        - learning_style (choose from: Logical + concepts, Creative + analogy, Straight + details, Fantasy + metaphor)
        - capability_abstracting_patterns (are they good at generalizing?)
        - logical_reasoning (how strong is their reasoning process?)
        - enjoy_puzzles_riddles (do they enjoy brain teasers?)
        - problem_solving (how do they approach hard problems?)
    Limit all field values to about 20 words in length. If the conversation context doesn't give you enough information to answer, leave the field blank instead of making assumptions. 
    """
    if not messages:
        return json.dumps({
            "error": "No message history provided",
            "suggestion": "Please provide a message history to summarize."
        })
    try:
        summary_prompt = """
        Summarize what you've learned about the student from the conversation.
        Return only a valid JSON object with these fields:
        - grade_in_school (integer)
        - learner_type (e.g., when do they plan to take the AP CSA exam?)
        - goal (freeform)
        - main_obstacles (freeform)
        - lesson_frequency (number of sessions per week and preferred session duration)
        - teaching_methods (e.g., hands-on projects, repetition, visual aids, etc.)
        - self_motivated (do they enjoy learning beyond the curriculum?)
        - work_independently (do they thrive or struggle with solo work?)
        - time_management (how they manage deadlines and workload)
        - learning_style (choose from: Logical + concepts, Creative + analogy, Straight + details, Fantasy + metaphor)
        - capability_abstracting_patterns (are they good at generalizing?)
        - logical_reasoning (how strong is their reasoning process?)
        - enjoy_puzzles_riddles (do they enjoy brain teasers?)
        - problem_solving (how do they approach hard problems?)
        Limit all field values to about 20 words in length. If the conversation context doesn't give you enough information to answer, leave the field blank instead of making assumptions. 
        """
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
        profile = llm.invoke(summary_prompt)
        return json.loads(profile.content)
    except Exception as e:
        return f"Error generating summary: {str(e)}"