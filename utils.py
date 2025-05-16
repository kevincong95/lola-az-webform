import streamlit as st

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pymongo import MongoClient

# Format: mongodb+srv://<username>:<password>@<cluster>.<id>.mongodb.net/
CONNECTION_STRING = f"mongodb+srv://{st.secrets['MONGO_USERNAME']}:{st.secrets['MONGO_PASSWORD']}@{st.secrets['MONGO_CLUSTER']}/?retryWrites=true&w=majority&appName={st.secrets['MONGO_APP_NAME']}&ssl=true&ssl_cert_reqs=CERT_NONE" 
MONGO_DB_NAME = st.secrets["MONGO_DB_NAME"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

def get_mongodb_connection():
    """
    Establishes connection to MongoDB.
    Update connection string with your MongoDB details.
    """
    if not st.session_state.mongodb_config["uri"]:
        st.error("No MongoDB connection provided.")
        return None
    try:
        import certifi
        client = MongoClient(
            st.session_state.mongodb_config["uri"],
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=30000
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