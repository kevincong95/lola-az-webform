import os
from dotenv import load_dotenv
import utils

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from typing import Annotated, Sequence, TypedDict

load_dotenv()

# Define the state type
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    context: Annotated[list[str], "The context retrieved from the knowledge base"]

# Initialize the language model
llm = ChatOpenAI(
    temperature=0.7, 
    model_name="gpt-4.1-mini", 
    api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Initialize vector store at module level
def initialize_vector_store():
    """Initialize or get existing MongoDB vector store."""
    client = utils.get_mongodb_connection()
    if not client:
        raise Exception("Could not connect to MongoDB")
        
    db = client[utils.MONGO_DB_NAME]
    collection = db[os.getenv("MONGODB_COLLECTION_NAME", "csa_documents")]
    
    # Create vector store
    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name=os.getenv("MONGODB_VECTOR_INDEX_NAME", "default")
    )
    return vector_store

try:
    vectorstore = initialize_vector_store()
except Exception as e:
    print(f"Warning: Could not initialize vector store: {e}")
    vectorstore = None

def retrieve(state: AgentState) -> AgentState:
    """Retrieve relevant context from the knowledge base."""
    if not vectorstore:
        raise Exception("Vector store not initialized")
        
    # Get the last human message
    last_message = state["messages"][-1].content
    
    # Retrieve relevant documents
    docs = vectorstore.similarity_search(last_message, k=3)
    context = [doc.page_content for doc in docs]
    
    return {"messages": state["messages"], "context": context}

def generate_response(state: AgentState) -> AgentState:
    """Generate a response using the retrieved context."""
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Lola, an expert AP Computer Science A tutor. 
        Use the following context to answer the student's question about AP CSA curriculum.
        If the context doesn't contain relevant information, say so and provide a general answer.
        Always be encouraging and supportive in your responses.
        
        Context:
        {context}"""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # Format the prompt
    formatted_prompt = prompt.format_messages(
        context="\n\n".join(state["context"]),
        messages=state["messages"]
    )
    
    # Generate response
    response = llm.invoke(formatted_prompt)
    
    # Add the response to messages
    state["messages"].append(response)
    
    return state

def invoke_agent(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Invoke the agent with a list of messages."""
    result = app.invoke({
        "messages": messages,
        "context": []
    })
    return result["messages"]

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate_response)

# Add edges
workflow.add_edge(START, "retrieve")  # Add entry point
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# Compile the graph
app = workflow.compile() 