# How to Run the Chatbot

This guide explains how to run the RAG chatbot with Flask API and web interface.

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Required Python packages** (install via `pip install -r requirements.txt`)
3. **API Keys**:
   - GROQ API key (for LLM)

## Step 1: Install Dependencies

Navigate to the project root directory and install required packages:

```bash
cd /home/dorisa/Documents/CUNY/CPT/ctp-project
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

Create a `.env` file in the project root directory (if it doesn't exist) with your API keys:

```bash
# .env file
GROQ_API_KEY=your_groq_api_key_here
```

**Note:** Replace `your_groq_api_key_here` with your actual API keys.

## Step 3: Verify Vector Store

The chatbot requires a vector store to be created. If it doesn't exist, it will be created automatically when you start the Flask API.

To manually create/rebuild the vector store:

```bash
cd chatbot
python3 create_vectorstore.py
```

## Step 4: Start the Flask API Server

Open a terminal and start the Flask API server:

```bash
cd chatbot
python flask_api.py
```

**Keep this terminal window open** - the server needs to keep running.

## Step 5: Open the Web Interface

1. Open `index.html` in your web browser:

   - You can double-click the file, or
   - Right-click and select "Open with" → your browser, or
   - Use a local web server (recommended for development):
     ```bash
     # Using Python's built-in server
     python -m http.server 8000
     # Then open: http://localhost:8000/index.html
     ```

2. You should see the globe visualization page

3. Look for the **chat button (💬)** in the bottom-right corner

4. Click the chat button to open the chatbot modal

## Step 6: Use the Chatbot

1. **Click a suggested question** button, or
2. **Type your question** in the input field and press Enter or click Send

Example questions:

- "What are the top subfields in Physical Sciences?"
- "What fields are in Physical Sciences?"
- "What are the top topics in Physical Sciences?"

## Troubleshooting

### Flask API won't start

**Error: "GROQ_API_KEY not found"**

- Make sure you have a `.env` file in the project root
- Verify the API key is correct in the `.env` file
- Restart the Flask server after adding/updating the `.env` file

**Error: "Vector store not found"**

- The vector store will be created automatically on first run
- If it fails, manually run: `python create_vectorstore.py`

### Chatbot shows "Offline" status

- Make sure the Flask API server is running
- Check that the API URL in `chatbot/chatbot.js` matches your Flask server port
- Default: `http://localhost:5000/api/chat`

## File Structure

```
ctp-project/
├── chatbot/
│   ├── flask_api.py          # Flask API server
│   ├── chatbot.js            # Frontend JavaScript
│   ├── chatbot.css           # Frontend styles
│   ├── rag_chatbot_*.py      # RAG implementation files
│   └── db/                   # Vector store database
├── index.html                # Main page with globe + chatbot
├── globe.js                  # Globe visualization
└── requirements.txt          # Python dependencies
```

## Quick Start Summary

1. Install dependencies: `pip install -r requirements.txt`
2. Add API keys to `.env` file
3. Start Flask API: `cd chatbot && python flask_api.py`
4. Open `index.html` in browser
5. Click chat button (💬) and start chatting!

## Notes

- The Flask API must be running for the chatbot to work
- The chatbot uses conversation history (stored in memory, resets when server restarts)
- Vector store is created automatically if it doesn't exist
- The chatbot connects to `http://localhost:5000/api/chat` by default

