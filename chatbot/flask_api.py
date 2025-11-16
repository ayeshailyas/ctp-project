"""
Flask API for RAG Chatbot

This module provides a basic REST API endpoint for the conversational RAG chatbot.
Code is based on conversational.py
"""

import os
import sys
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_groq import ChatGroq

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import vector store creation functions
from chatbot.create_vectorstore import create_vectorstore, check_if_rebuild_needed

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Define the persistent directory (must match Milestone 2)
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_research")

# Global variables for RAG components
rag_chain = None
chat_history = []  # Simple global conversation history for basic implementation


def initialize_rag_chain():
    """Initialize the RAG chain, vector store, and LLM."""
    global rag_chain

    # Check if vector store exists or needs to be rebuilt
    if not os.path.exists(persistent_directory):
        print(f"Vector store not found at {persistent_directory}")
        print("Creating vector store...")
        create_vectorstore()
    else:
        # Check if rebuild is needed
        needs_rebuild, reason = check_if_rebuild_needed()
        if needs_rebuild:
            print("=" * 80)
            print("⚠ Vector Store Update Needed")
            print("=" * 80)
            print(f"Reason: {reason}")
            print("\nRebuilding vector store...")
            # Remove existing vector store
            if os.path.exists(persistent_directory):
                shutil.rmtree(persistent_directory)
                print("✓ Removed old vector store")
            # Rebuild
            create_vectorstore()
        else:
            print("✓ Vector store is up to date.")

    # Define the embedding model (must match the one used in Milestone 2)
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Load the existing vector store with the embedding function
    print("Loading vector store...")
    db = Chroma(persist_directory=persistent_directory, embedding_function=embeddings)
    print("✓ Vector store loaded successfully\n")

    # Create a retriever for querying the vector store
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 20},
        filter={"category": "Physical Sciences"}
    )

    # Create a ChatGroq model
    # Check if GROQ_API_KEY is set
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY not found in environment variables. Please set GROQ_API_KEY in your .env file or environment.")

    print("Initializing GROQ LLM...")
    llm = ChatGroq(
        model="llama-3.1-8b-instant",  # Fast and efficient model
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    print("✓ GROQ LLM initialized\n")

    # Contextualize question prompt
    # This system prompt helps the AI understand that it should reformulate the question
    # based on the chat history to make it a standalone question
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, just "
        "reformulate it if needed and otherwise return it as is."
    )

    # Create a prompt template for contextualizing questions
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Answer question prompt
    # This system prompt helps the AI understand that it should provide concise answers
    # based on the retrieved context and indicates what to do if the answer is unknown
    qa_system_prompt = (
        "You are an assistant for question-answering tasks about Physical Sciences "
        "research data. Use the following pieces of retrieved context to answer the "
        "question. You are specifically asked to list all the fields, subfields, topics, founders in the Physical "
        "Sciences data. Do not summarize or omit any of the fields, subfields, topics, founders. If there are "
        "multiple fields, subfields, topics, founders, list them all.\n\n"
        "IMPORTANT FORMATTING INSTRUCTIONS:\n"
        "- Write responses in natural, conversational sentences. Do NOT use markdown "
        "formatting like **, # .\n"
        "- Do NOT include IDs (like 'ID: 22' or 'ID: 2208') in your responses. "
        "Only mention names and relevant numbers.\n"
        "- Express information in complete sentences when summarize, not lists or structured formats.\n"
        "- Make the response flow naturally as if you're explaining to someone in "
        "conversation.\n"
        "Context:\n{context}"
    )

    # Create a prompt template for answering questions
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Format documents function
    def format_docs(docs):
        """Format retrieved documents into a single string."""
        return "\n\n".join(doc.page_content for doc in docs)

    # Create a history-aware retriever function
    def get_contextualized_retrieval(input_data):
        """Retrieve documents, reformulating query based on chat history if needed."""
        query = input_data["input"]
        history = input_data.get("chat_history", [])

        # If there's chat history, reformulate the question to be standalone
        if history:
            # Create a contextualized query using the LLM
            contextualize_chain = contextualize_q_prompt | llm | StrOutputParser()
            reformulated_query = contextualize_chain.invoke({
                "input": query,
                "chat_history": history
            })
        else:
            reformulated_query = query

        filter_metadata = {"category": "Physical Sciences"}
        # Retrieve documents using the (possibly reformulated) query
        retrieved_docs = retriever.invoke(reformulated_query, filter=filter_metadata)
        return format_docs(retrieved_docs)

    # Create the RAG chain with history awareness
    rag_chain = (
        {
            "context": lambda x: get_contextualized_retrieval(x),
            "input": lambda x: x["input"],
            "chat_history": lambda x: x.get("chat_history", []),
        }
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    print("✓ RAG chain initialized successfully")
    return rag_chain


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and return AI responses."""
    global chat_history

    try:
        # Get JSON data from request
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data provided"
            }), 400

        # Get message from request
        message = data.get('message')

        if not message:
            return jsonify({
                "error": "Missing required field: 'message'"
            }), 400

        # Validate message is not empty
        message = message.strip()
        if not message:
            return jsonify({
                "error": "Message cannot be empty"
            }), 400

        # Check if RAG chain is initialized
        if rag_chain is None:
            return jsonify({
                "error": "RAG chain not initialized. Please check server logs."
            }), 503

        # Process the user's query through the retrieval chain with chat history
        result = rag_chain.invoke({
            "input": message,
            "chat_history": chat_history
        })

        # Update the chat history
        chat_history.append(HumanMessage(content=message))
        chat_history.append(AIMessage(content=result))

        # Return response
        return jsonify({
            "response": result
        }), 200

    except Exception as e:
        print(f"Error processing chat message: {e}")
        return jsonify({
            "error": "An error occurred while processing your message",
            "details": str(e) if app.debug else None
        }), 500


if __name__ == '__main__':
    # Initialize RAG chain before starting server
    print("Initializing RAG chain...")
    rag_chain = initialize_rag_chain()

    if rag_chain is None:
        print("Failed to initialize RAG chain. Exiting.")
        sys.exit(1)

    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"\nStarting Flask API server on port {port}")
    print(f"Debug mode: {debug}")
    print("API endpoint: POST /api/chat")
    print("\nExample request:")
    print('  curl -X POST http://localhost:5000/api/chat \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"message": "What are the top subfields?"}\'\n')

    app.run(host='0.0.0.0', port=port, debug=debug)
