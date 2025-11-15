# RAG Chatbot Milestones

## Overview

Build a RAG (Retrieval-Augmented Generation) chatbot that answers questions about Physical Sciences research data from CSV files. The chatbot will use GROQ API for LLM and follow the code structure patterns from `2a_rag_basics_metadata.py`, `2b_rag_basics_metadata.py`, and `7_rag_conversational.py`.

## Data Source

- CSV files in `data/` directory:
  - `fields.csv` - Fields in Physical Sciences domain
  - `top_subfields_us.csv` - Top 10 US subfields
  - `subfield_funders_us.csv` - Funders for each subfield
  - `top_topics_us.csv` - Top 10 US topics

## Technology Stack

- **LLM**: GROQ API
- **Embeddings**: OpenAI embeddings (text-embedding-3-small) or compatible
- **Vector Store**: Chroma (persistent)
- **Framework**: LangChain
- **Interface**: CLI (command-line)

---

## Example Questions Users Can Ask

The chatbot should be able to answer questions about the Physical Sciences research data. Here are example questions organized by category:

### Questions About Fields

- "What fields are in Physical Sciences?"
- "How many fields are there in Physical Sciences?"
- "Tell me about the Chemistry field"
- "List all fields in Physical Sciences"
- "How many topics does Chemistry have?"

### Questions About Subfields

- "What are the top subfields in Physical Sciences?"
- "What is the top subfield?"
- "Tell me about Electrical and Electronic Engineering"
- "What are the top 3 subfields?"
- "Which subfield has the most US works?"
- "How many US works does Biomedical Engineering have?"
- "What subfields are in Physical Sciences?"

### Questions About Topics

- "What are the top topics in Physical Sciences?"
- "Tell me about the top 5 topics"
- "What topics are in Chemistry?"
- "Which topic has the most US works?"
- "List all topics"
- "What field does [topic name] belong to?"

### Questions About Funders

- "Who funds research in Electrical and Electronic Engineering?"
- "What funder supports Biomedical Engineering?"
- "Tell me about funders for Materials Chemistry"
- "Which funder has the most works in [subfield]?"
- "What is the top funder for [subfield name]?"
- "List all funders"

### General Questions

- "What data do you have about Physical Sciences?"
- "Tell me about Physical Sciences research"
- "What information is available?"
- "Summarize the Physical Sciences research data"
- "What can you tell me about research in Physical Sciences?"

### Follow-up Questions (for conversational mode)

- "Tell me more about that"
- "What about the first one?"
- "Who funds research in that area?"
- "How many works does it have?"
- "What field does it belong to?"

### Note on Question Types

- The chatbot should handle natural language variations
- Questions can be asked in different ways (e.g., "What is..." vs "Tell me about...")
- The chatbot should provide clear, concise answers based on the CSV data
- If information is not available in the data, the chatbot should say so

---

## Milestone 1: Load CSV Data and Create Document Objects

**Goal**: Read CSV files and convert rows into LangChain Document objects (in memory) ready for embedding.

**What you'll build**:

- A script that reads all CSV files from `data/` directory using pandas
- Converts each row into a LangChain `Document` object with:
  - `page_content`: Human-readable text representation of the row data
  - `metadata`: Dictionary with source file, data type, and relevant fields (ID, name, etc.)
- Documents are created in memory (no intermediate text files needed)
- Documents are ready to be passed directly to the embedding/vector store creation

**Note**: Unlike the reference files that load from `.txt` files, we work directly with CSV data. We create Document objects in memory without saving intermediate text files.

**Verification**:

- Run the script and see printed output showing:
  - Number of documents created from each CSV
  - Sample document content (page_content)
  - Document metadata (source file, data type, IDs, etc.)

**Files to create**:

- `rag_chatbot_1_load_data.py`

**Expected output example**:

```
Loading CSV data...
✓ Loaded 12 fields from fields.csv
✓ Loaded 10 subfields from top_subfields_us.csv
✓ Loaded 10 funders from subfield_funders_us.csv
✓ Loaded 10 topics from top_topics_us.csv
Total documents: 42

Sample document:
Page Content: "Field: Chemistry (ID: 16) has 101 topics."
Metadata: {'source': 'fields.csv', 'type': 'field', 'id': '16', 'name': 'Chemistry'}
```

---

## Milestone 2: Create Vector Store with Embeddings

**Goal**: Generate embeddings from Document objects and create a persistent Chroma vector store.

**What you'll build**:

- Script that:
  1. Loads CSV data and creates Document objects (using code from Milestone 1, or import the function)
  2. Splits documents into chunks (if needed - for CSV rows, each row is typically one chunk)
  3. Creates embeddings using OpenAI embeddings
  4. Persists vector store to disk using `Chroma.from_documents()` (similar structure to `2a_rag_basics_metadata.py`)

**Note**: We embed directly from Document objects created from CSV data. No intermediate text files are created or saved.

**Verification**:

- Run the script and see:
  - Vector store created in `db/chroma_db_research/`
  - Number of document chunks created
  - Confirmation message when complete
- Re-run script and see it detects existing vector store (checks if directory exists)

**Files to create**:

- `rag_chatbot_2_create_vectorstore.py`

**Expected output example**:

```
Creating vector store...
Loading CSV data and creating documents...
✓ Loaded 42 documents from CSV files

--- Document Chunks Information ---
Number of document chunks: 42

--- Creating embeddings ---
--- Finished creating embeddings ---

--- Creating and persisting vector store ---
✓ Vector store saved to db/chroma_db_research/
```

---

## Milestone 3: Basic Retrieval (No LLM)

**Goal**: Test document retrieval from vector store.

**What you'll build**:

- Script that loads existing vector store
- Implements similarity search
- Retrieves relevant documents for test queries
- Displays results with metadata (similar to `2b_rag_basics_metadata.py`)

**Verification**:

- Run script with test queries like:
  - "What are the top subfields?"
  - "Tell me about Chemistry"
  - "Who funds research?"
- See retrieved documents with their content and source metadata

**Files to create**:

- `rag_chatbot_3_retrieve.py`

**Expected output example**:

```
Query: What are the top subfields?

--- Relevant Documents ---
Document 1:
Subfield: Electrical and Electronic Engineering (ID: 2208) has 1,626,963 US works.
Source: top_subfields_us.csv

Document 2:
Subfield: Biomedical Engineering (ID: 2204) has 1,315,880 US works.
Source: top_subfields_us.csv
```

---

## Milestone 4: Simple Q&A with GROQ LLM

**Goal**: Add GROQ LLM to generate answers from retrieved context.

**What you'll build**:

- Script that combines retrieval + GROQ LLM
- Simple prompt template for question answering
- Single-turn Q&A (no conversation history yet)
- CLI interface for asking questions

**Verification**:

- Run script and ask questions:
  - "What is the top subfield in Physical Sciences?"
  - "How many topics does Chemistry have?"
- See natural language answers generated by GROQ

**Files to create**:

- `rag_chatbot_4_simple_qa.py`

**Expected output example**:

```
You: What is the top subfield in Physical Sciences?
AI: The top subfield in Physical Sciences based on US works count is Electrical and Electronic Engineering with 1,626,963 works.
```

---

## Milestone 5: Conversational RAG with History

**Goal**: Add conversation history for context-aware responses.

**What you'll build**:

- History-aware retriever (reformulates questions based on chat history)
- Conversational chain with chat history
- CLI chat loop (similar to `7_rag_conversational.py`)
- Type 'exit' to quit

**Verification**:

- Run script and have a conversation:
  - "What are the top 3 subfields?"
  - "Tell me more about the first one"
  - "Who funds research in that area?"
- Verify the chatbot understands context from previous messages

**Files to create**:

- `rag_chatbot_5_conversational.py`

**Expected output example**:

```
Start chatting! Type 'exit' to end.

You: What are the top 3 subfields?
AI: The top 3 subfields in Physical Sciences are: 1) Electrical and Electronic Engineering (1,626,963 works), 2) Biomedical Engineering (1,315,880 works), and 3) Materials Chemistry (1,100,200 works).

You: Tell me more about the first one
AI: Electrical and Electronic Engineering is the top subfield with 1,626,963 US works. It focuses on electrical systems and electronic devices.

You: Who funds research in that area?
AI: [Information about funders for Electrical and Electronic Engineering]
```

---

## Milestone 6: Handle Data Updates

**Goal**: Detect when CSV files change and rebuild vector store.

**What you'll build**:

- Check if CSV files have been modified since last vector store creation
- Option to rebuild vector store when data changes
- Clear messaging about data freshness

**Verification**:

- Update a CSV file
- Run script and see prompt to rebuild vector store
- Rebuild and verify new data is included

**Files to modify**:

- `rag_chatbot_2_create_vectorstore.py` (add timestamp checking)
- Or create: `rag_chatbot_6_data_updates.py`

---

## Implementation Notes

### Code Structure Pattern

Follow the structure from reference files:

- Use LangChain components (Chroma, embeddings, chains)
- Persistent vector store in `db/` directory
- Clear print statements for verification
- Error handling for missing files

**Important**: While the reference files (`2a_rag_basics_metadata.py`, etc.) load from `.txt` files, our implementation works directly with CSV data:

- Read CSV files with `pandas`
- Convert rows to LangChain `Document` objects in memory
- Embed directly without creating intermediate text files
- This approach is more efficient and better suited for structured CSV data

### GROQ API Setup

- Install: `pip install langchain-groq`
- Set environment variable: `GROQ_API_KEY`
- Use: `ChatGroq` instead of `ChatOpenAI`

### Dependencies to Add

```txt
langchain
langchain-community
langchain-openai  # For embeddings
langchain-groq    # For GROQ LLM
chromadb
python-dotenv
pandas
```

### Environment Variables

Create `.env` file:

```
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # For embeddings
```

---

## Next Steps After Milestones

Once all milestones are complete:

- Integrate chatbot with Flask API
- Add web interface
- Connect to globe visualization
- Add more sophisticated query handling
