"""
Flask API for RAG Chatbot

This module provides a basic REST API endpoint for the conversational RAG chatbot.
Code is based on conversational.py
"""

import os
import sys
import shutil
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
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
vector_db = None  # Global reference to vector database


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

    # Store db reference globally for direct access
    global vector_db
    vector_db = db

    # Create a retriever for querying the vector store
    # Increased k to 100 to ensure all documents can be retrieved
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 100},
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

    # Answer question prompt - will be created dynamically based on query type
    def create_qa_system_prompt(is_list_query=False):
        """Create system prompt based on whether this is a list query."""
        base_prompt = (
            "You are an assistant for question-answering tasks about Physical Sciences "
            "research data. Use the following pieces of retrieved context to answer the "
            "question.\n\n"
            "CRITICAL RULES:\n"
            "- NEVER include IDs (like 'ID: 22', 'ID: 2208', 'ID: 1312', or any ID numbers) in your responses.\n"
            "- Only mention names and relevant numbers (like work counts, topic counts, etc.).\n"
        )

        if is_list_query:
            list_format = (
                "- Format your response as a CLEAR LIST, with each item on a new line.\n"
                "- Use a simple format like: '1. Item Name' or '- Item Name' for each item.\n"
                "- Do NOT use markdown formatting like **, #, or ```.\n"
                "- List ALL items from the context. Do not omit or summarize any items.\n"
                "- You can add a brief introductory sentence before the list if helpful.\n"
            )
            return base_prompt + list_format + "\nContext:\n{context}"

        sentence_format = (
                "- Write responses in natural, conversational sentences.\n"
                "- Do NOT use markdown formatting like **, #, or ```.\n"
                "- Express information in complete sentences, not lists or structured formats.\n"
                "- Make the response flow naturally as if you're explaining to someone in conversation.\n"
            )
        return base_prompt + sentence_format + "\nContext:\n{context}"

    # Create a prompt template for answering questions (will be created dynamically)
    # We'll create it in the retrieval function based on query type

    # Format documents function
    def format_docs(docs):
        """Format retrieved documents into a single string, removing IDs."""
        formatted_docs = []
        for doc in docs:
            # Remove ID patterns like "(ID: 1234)" or "ID: 1234" from content
            content = doc.page_content
            # Remove patterns like "(ID: 1234)" or "ID: 1234" or "ID:1234"
            content = re.sub(r'\s*\(?ID:\s*\d+\)?\s*', ' ', content, flags=re.IGNORECASE)
            # Clean up extra spaces
            content = re.sub(r'\s+', ' ', content).strip()
            formatted_docs.append(content)
        return "\n\n".join(formatted_docs)

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

        # Check if this is a "list all" query - if so, retrieve all documents of that type
        query_lower = reformulated_query.lower()
        is_list_all_query = any(phrase in query_lower for phrase in [
            "list all", "all fields", "all subfields", "all topics",
            "all funders", "show all", "what are all", "every field",
            "every subfield", "every topic", "count of", "how many"
        ])

        if is_list_all_query:
            # Determine document type from query
            doc_type = None
            if "field" in query_lower and "subfield" not in query_lower:
                doc_type = "field"
            elif "subfield" in query_lower:
                doc_type = "subfield"
            elif "topic" in query_lower:
                doc_type = "topic"
            elif "funder" in query_lower:
                doc_type = "funder"

            # If we can identify a specific type, retrieve all documents of that type
            if doc_type:
                filter_metadata = {"category": "Physical Sciences", "type": doc_type}
                # Use get() method to retrieve all documents matching the filter
                all_docs = vector_db.get(where=filter_metadata)
                # Convert to Document objects
                retrieved_docs = []
                if all_docs and "documents" in all_docs:
                    for i, doc_content in enumerate(all_docs["documents"]):
                        metadata = {}
                        if "metadatas" in all_docs and i < len(all_docs["metadatas"]):
                            metadata = all_docs["metadatas"][i]
                        retrieved_docs.append(Document(page_content=doc_content, metadata=metadata))
                print(f"Retrieved all {len(retrieved_docs)} {doc_type} documents")
            else:
                # Fallback to similarity search with high k
                retrieved_docs = retriever.invoke(reformulated_query)
                print(f"Retrieved {len(retrieved_docs)} documents (similarity search)")
        else:
            # Regular similarity search (filter already configured in retriever)
            retrieved_docs = retriever.invoke(reformulated_query)
            print(f"Retrieved {len(retrieved_docs)} documents (similarity search)")

        # Store whether this is a list query for use in prompt
        input_data["_is_list_query"] = is_list_all_query
        return format_docs(retrieved_docs)

    # Create the RAG chain
    def process_query(input_data):
        """Process query through retrieval and LLM with appropriate formatting."""
        # Get context (this also sets _is_list_query flag)
        context = get_contextualized_retrieval(input_data)
        is_list_query = input_data.get("_is_list_query", False)

        # Create prompt based on query type
        qa_system_prompt = create_qa_system_prompt(is_list_query=is_list_query)
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # Invoke the chain
        chain = qa_prompt | llm | StrOutputParser()
        result = chain.invoke({
            "context": context,
            "input": input_data["input"],
            "chat_history": input_data.get("chat_history", [])
        })

        return result

    rag_chain = process_query

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
        result = rag_chain({
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
    port = int(os.environ.get('PORT', 5050))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"\nStarting Flask API server on port {port}")
    print(f"Debug mode: {debug}")
    print("API endpoint: POST /api/chat")
    print("\nExample request:")
    print('  curl -X POST http://localhost:5000/api/chat \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"message": "What are the top subfields?"}\'\n')

    app.run(host='0.0.0.0', port=port, debug=debug)
