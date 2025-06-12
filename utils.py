import base64
import hashlib
import os
import streamlit as st
import certifi

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

def go_to_page(page_name: str):
    """Navigate to a specified page in the application.
    
    Args:
        page_name (str): The name of the page to navigate to. Valid values are:
            - "landing": The landing page
            - "login": The login page
            - "customer_service": The customer service/onboarding page
            - "csa_chat": The CSA chat interface
            - "main": The main tutoring interface
    """
    st.session_state.current_page = page_name
    st.rerun()

def create_new_user(user_data, password = None):
    """Create a new user in the database with provided information."""
    client = st.session_state.mongo_client
    if client is None:
        return False, "Could not connect to database."
    
    try:
        db = client[MONGO_DB_NAME]
        users_collection = db['students']
        
        # Check if email already exists
        if users_collection.find_one({"email": user_data.get("email", "")}):
            return False, "Email already exists. Please choose another."
        
        # Hash the password
        if password:
            user_data["password_hash"] = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert the new user
        users_collection.insert_one(user_data)
        return True, "User created successfully!"
    
    except Exception as e:
        return False, f"Error creating user: {e}"

def get_avatar_base64(image_path):
    """Convert an image to a base64 string for embedding in HTML/Markdown."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()