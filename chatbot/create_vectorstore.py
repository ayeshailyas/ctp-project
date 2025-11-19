import os
import sys
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from chatbot.load_data import load_all_csv_documents

# Import data directory and CSV files config from the load_data module
import chatbot.load_data as load_data
data_dir = load_data.data_dir
csv_files = load_data.csv_files

# Load environment variables from .env (for future use with GROQ)
load_dotenv()

# Define the persistent directory
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.join(db_dir, "chroma_db_research")
metadata_file = os.path.join(db_dir, "vectorstore_metadata.json")

print(f"Persistent directory: {persistent_directory}")


def get_csv_modification_times():
    """Get the modification times of all CSV files."""
    csv_times = {}
    for csv_file in csv_files.keys():
        file_path = os.path.join(data_dir, csv_file)
        if os.path.exists(file_path):
            csv_times[csv_file] = os.path.getmtime(file_path)
        else:
            csv_times[csv_file] = None
    return csv_times


def save_vectorstore_metadata():
    """Save metadata about when the vector store was created."""
    metadata = {
        "created_at": datetime.now().isoformat(),
        "csv_modification_times": get_csv_modification_times()
    }
    os.makedirs(db_dir, exist_ok=True)
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    return metadata


def load_vectorstore_metadata():
    """Load metadata about the vector store."""
    if not os.path.exists(metadata_file):
        return None
    try:
        with open(metadata_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def check_if_rebuild_needed():
    """Check if vector store needs to be rebuilt based on CSV file changes."""
    if not os.path.exists(persistent_directory):
        return True, "Vector store does not exist."

    metadata = load_vectorstore_metadata()
    if not metadata:
        return True, "No metadata found. Vector store may be outdated."

    current_csv_times = get_csv_modification_times()
    stored_csv_times = metadata.get("csv_modification_times", {})

    # Check if any CSV file has been modified
    for csv_file, current_time in current_csv_times.items():
        if current_time is None:
            continue  # File doesn't exist, skip
        stored_time = stored_csv_times.get(csv_file)
        if stored_time is None or current_time > stored_time:
            created_at = metadata.get("created_at", "unknown")
            return True, f"CSV file '{csv_file}' has been modified since vector store creation ({created_at})."

    return False, None


def create_vectorstore():
    """Create or rebuild the vector store."""
    # Ensure the db directory exists
    os.makedirs(db_dir, exist_ok=True)

    # Load CSV data and create Document objects
    print("\nLoading CSV data and creating documents...")
    documents = load_all_csv_documents()

    if not documents:
        raise ValueError("No documents were loaded. Please check your CSV files.")

    # For CSV rows, each row is already a small, self-contained chunk
    # So we don't need to split them further
    # Each document is already appropriately sized for embedding
    docs = documents

    # Display information about the documents
    print("\n--- Document Chunks Information ---")
    print(f"Number of document chunks: {len(docs)}")

    # Create embeddings using HuggingFace (free, no API key needed)
    # Using a lightweight, fast embedding model
    print("\n--- Creating embeddings ---")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("--- Finished creating embeddings ---")

    # Create the vector store and persist it
    print("\n--- Creating and persisting vector store ---")
    db = Chroma.from_documents(
        docs, embeddings, persist_directory=persistent_directory
    )
    print("--- Finished creating and persisting vector store ---")

    # Save metadata about when the vector store was created
    metadata = save_vectorstore_metadata()
    print(f"\n✓ Vector store saved to {persistent_directory}")
    print(f"✓ Metadata saved: Created at {metadata['created_at']}")
    return db


# Check if the Chroma vector store already exists
if not os.path.exists(persistent_directory):
    print("Persistent directory does not exist. Initializing vector store...")
    create_vectorstore()

else:
    # Check if rebuild is needed
    needs_rebuild, reason = check_if_rebuild_needed()

    if needs_rebuild:
        print("=" * 80)
        print("⚠ Vector Store Update Needed")
        print("=" * 80)
        print(f"Reason: {reason}")
        print("\nThe CSV data files have been updated since the vector store was created.")
        print("You should rebuild the vector store to include the latest data.")

        response = input("\nDo you want to rebuild the vector store now? (yes/no): ").strip().lower()

        if response in ['yes', 'y']:
            print("\nRebuilding vector store...")
            # Remove existing vector store
            if os.path.exists(persistent_directory):
                shutil.rmtree(persistent_directory)
                print("✓ Removed old vector store")

            # Rebuild using the same function
            create_vectorstore()
        else:
            print("\nVector store rebuild cancelled.")
            print("The vector store will continue to use the old data.")
            metadata = load_vectorstore_metadata()
            if metadata:
                print(f"Current vector store created at: {metadata.get('created_at', 'unknown')}")
    else:
        metadata = load_vectorstore_metadata()
        created_at = metadata.get('created_at', 'unknown') if metadata else 'unknown'
        print("✓ Vector store is up to date.")
        print(f"  Created at: {created_at}")
        print(f"  All CSV files match the stored modification times.")
        print(f"\nTo manually rebuild, delete the directory: {persistent_directory}")

