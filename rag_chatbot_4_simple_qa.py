import os
import sys
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# Load environment variables from .env
load_dotenv()

# Define the persistent directory (must match Milestone 2)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_research")

# Check if vector store exists
if not os.path.exists(persistent_directory):
    print(f"Error: Vector store not found at {persistent_directory}")
    print("Please run rag_chatbot_2_create_vectorstore.py first to create the vector store.")
    sys.exit(1)

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
    search_kwargs={"k": 3},
)

# Create a ChatGroq model
# Check if GROQ_API_KEY is set
if not os.getenv("GROQ_API_KEY"):
    print("Error: GROQ_API_KEY not found in environment variables.")
    print("Please set GROQ_API_KEY in your .env file or environment.")
    sys.exit(1)

print("Initializing GROQ LLM...")
llm = ChatGroq(
    model="llama-3.1-8b-instant",  # Fast and efficient model
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)
print("✓ GROQ LLM initialized\n")

# Answer question prompt
# This system prompt helps the AI understand that it should provide concise answers
# based on the retrieved context and indicates what to do if the answer is unknown
qa_system_prompt = (
    "You are an assistant for question-answering tasks about Physical Sciences research data. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer based on the context provided, just say that you don't know. "
    "Keep your answer concise and based only on the information provided in the context. "
    "Do not make up information that is not in the context.\n\n"
    "Context:\n{context}"
)

# Create a prompt template for answering questions
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        ("human", "{input}"),
    ]
)

# Format documents function
def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)

# Create the RAG chain using RunnablePassthrough (LangChain 1.0 approach)
rag_chain = (
    {
        "context": retriever | format_docs,
        "input": RunnablePassthrough(),
    }
    | qa_prompt
    | llm
    | StrOutputParser()
)

# Simple Q&A function (single-turn, no conversation history)
def simple_qa():
    """Simple Q&A interface - single turn, no conversation history."""
    print("=" * 80)
    print("RAG Chatbot - Simple Q&A")
    print("=" * 80)
    print("Ask questions about Physical Sciences research data.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("You: ").strip()

        if query.lower() == "exit":
            print("\nGoodbye!")
            break

        if not query:
            continue

        try:
            # Process the user's query through the retrieval chain
            result = rag_chain.invoke(query)

            # Display the AI's response
            print(f"\nAI: {result}\n")

        except Exception as e:
            print(f"\nError: {e}\n")
            print("Please try again or type 'exit' to quit.\n")


# Main function
if __name__ == "__main__":
    simple_qa()

