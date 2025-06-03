import os
import streamlit as st

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pymongo import MongoClient
from urllib.parse import quote_plus

load_dotenv()

def get_secret(key):
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets[key]
    except Exception as e:
        st.error(f"Failed to load secrets: {e}")
        return None

USERNAME = quote_plus(get_secret('MONGO_USERNAME'))
PASSWORD = quote_plus(get_secret('MONGO_PASSWORD'))
CLUSTER = get_secret('MONGO_CLUSTER')
MONGO_DB_NAME = get_secret('MONGO_DB_NAME')

CONNECTION_STRING = f"mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSTER}/{MONGO_DB_NAME}?retryWrites=true&w=majority"
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")

@st.cache_resource
def get_mongodb_connection():
    """
    Establishes connection to MongoDB.
    Update connection string with your MongoDB details.
    """
    try:
        import certifi
        client = MongoClient(
            CONNECTION_STRING,
            tls=True,
            tlsCAFile=certifi.where(),
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=30000,
            appname=get_secret('MONGO_APP_NAME'),
            retryWrites=True,
            w='majority'
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

# Convert Streamlit chat format to Langgraph format
def convert_to_langgraph_messages(streamlit_messages):
    langgraph_messages = []
    for msg in streamlit_messages:
        if msg["role"] == "user":
            langgraph_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langgraph_messages.append(AIMessage(content=msg["content"]))
        elif msg["role"] == "system":
            langgraph_messages.append(SystemMessage(content=msg["content"]))
    return langgraph_messages

# Convert Langgraph format to Streamlit chat format
def convert_to_streamlit_messages(langgraph_messages):
    streamlit_messages = []
    for msg in langgraph_messages:
        if isinstance(msg, HumanMessage):
            streamlit_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            streamlit_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            streamlit_messages.append({"role": "system", "content": msg.content})
    return streamlit_messages