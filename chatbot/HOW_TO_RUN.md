# How to Run the Chatbot

## Required API Keys

Create a `.env` file in the project root directory with:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

**Note:** Replace `your_groq_api_key_here` with your actual GROQ API key.

## How to Run

### Step 1: Install Dependencies

```bash
cd /home/dorisa/Documents/CUNY/CPT/ctp-project
pip install -r requirements.txt
```

### Step 2: Start the Flask API Server

```bash
cd chatbot
python flask_api.py
```

**Keep this terminal window open** - the server needs to keep running.

### Step 3: Open the Web Interface

Open `index.html` in your web browser. The chatbot button (💬) is located in the bottom-right corner.
