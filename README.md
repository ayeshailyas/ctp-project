# Science and Technology Research Topic Trend Analysis

- Team: Arun, Ayesha, Dorisa, Mykola
- Project Scope: Analyze the trends in science and technology research using data from OpenAlex.
- Audience: Researchers, policymakers, and students interested in understanding the trends in science and technology research.

## Key Features
- **Interactive Force-Directed Graph**: Visualizes relationships between the top 10 US research subfields in Physical Sciences
- **Semantic Similarity Connections**: Nodes are connected based on topic similarity using TF-IDF and cosine similarity
- **Dynamic Topic Exploration**: Click any subfield node to explore the top 20 trending topics within that field

## Quick Start
- **Go to frontend/my-globe-app**
- Run **npm install** (This installs Next.js, React, Tailwind, Recharts, Lucide, and the Google AI SDK.)

- **Go to backend/**
- Run **pip install pandas pyalex python-dotenv**

- **Create a file called .env.local in frontend/my-globe-app**
- Paste your api key that you get from https://aistudio.google.com/
- Use this format **GEMINI_API_KEY=your_google_gemini_api_key_here**

- **Go to frontend/my-globe-app**
- Run **npm run dev** (This will start the website)
