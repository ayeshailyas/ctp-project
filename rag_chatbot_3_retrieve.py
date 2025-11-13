import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Define the persistent directory (must match Milestone 2)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_research")

# Check if vector store exists
if not os.path.exists(persistent_directory):
    print(f"Error: Vector store not found at {persistent_directory}")
    print("Please run rag_chatbot_2_create_vectorstore.py first to create the vector store.")
    exit(1)

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
# `search_type` specifies the type of search (e.g., similarity)
# `search_kwargs` contains additional arguments for the search (e.g., number of results to return)
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 3, "score_threshold": 0.1},
)

# Test queries
test_queries = [
    "What are the top subfields?",
    "Tell me about Chemistry",
    "Who funds research?",
    "What topics are in Physical Sciences?",
    "Tell me about Electrical and Electronic Engineering"
]

print("=" * 80)
print("Testing Document Retrieval")
print("=" * 80)

# Test each query
for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 80)

    # Retrieve relevant documents based on the query
    relevant_docs = retriever.invoke(query)

    if not relevant_docs:
        print("No relevant documents found (score threshold too high).")
        continue

    # Display the relevant results with metadata
    print(f"\n--- Relevant Documents ({len(relevant_docs)} found) ---")
    for i, doc in enumerate(relevant_docs, 1):
        print(f"\nDocument {i}:")
        print(f"Content: {doc.page_content}")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Type: {doc.metadata.get('type', 'Unknown')}")
        # Show additional metadata if available
        if 'name' in doc.metadata:
            print(f"Name: {doc.metadata['name']}")
        if 'id' in doc.metadata:
            print(f"ID: {doc.metadata['id']}")

    print("\n" + "=" * 80)

print("\n✓ Retrieval testing complete!")
print("\nYou can modify the test_queries list to test different questions.")

