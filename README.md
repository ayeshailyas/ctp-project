# Science and Technology Research Topic Trend Analysis

- Team: Arun, Ayesha, Dorisa, Mykola
- Project Scope: Analyze the trends in science and technology research using data from OpenAlex.
- Audience: Researchers, policymakers, and students interested in understanding the trends in science and technology research.

## Key Features
- **Interactive Force-Directed Graph**: Visualizes relationships between the top 10 US research subfields in Physical Sciences
- **Semantic Similarity Connections**: Nodes are connected based on topic similarity using TF-IDF and cosine similarity
- **Dynamic Topic Exploration**: Click any subfield node to explore the top 20 trending topics within that field

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ctp-project
   ```

2. Create a virtual environment and activate it
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file with your OpenAlex API email
   echo "OPENALEX_EMAIL=your-email@example.com" > .env
   ```

5. **Fetch the data**
   ```bash
   # Fetch base datasets
   python save_data_csv.py
   ```

5. **Start the application**
   ```bash
   python flask_api.py
   ```

7. **Open in browser**

Open `subfields.html` in your browser

## Data Sources

The application uses data from [OpenAlex](https://openalex.org/), a comprehensive open database of scholarly works:

- **Fields and Subfields**: Top 10 US subfields in Physical Sciences (Domain ID: 3)
- **Topics**: Top 20 trending topics for each subfield based on US works count
- **Funders**: Top US funders for each subfield
- **Work Counts**: Number of research works from US institutions

## Tech Stack

### Backend
- **Flask**: Web framework for API endpoints
- **Pandas**: Data manipulation and analysis
- **scikit-learn**: TF-IDF vectorization and cosine similarity
- **pyalex**: OpenAlex API client

### Frontend
- **D3.js**: Data visualization and force-directed graph rendering
- **HTML5/CSS3**: Modern responsive design
- **JavaScript ES6+**: Interactive features and API communication

### Data Processing
- **OpenAlex API**: Real-time scholarly data fetching
- **TF-IDF**: Text feature extraction for similarity calculation
- **Cosine Similarity**: Measuring semantic relationships between topics

### Core API Endpoints

- `GET /api/health` - Health check and data status
- `GET /api/subfields/graph` - Get subfield graph data with similar- `GET /api/topics/subfield/<id>` - Get topics for specific subfield with graph structure

## Visualization Features

### Force-Directed Graphs
- **Node Size**: Proportional to US works count in the subfield
- **Interactive Controls**:
  - Zoom in/out with mouse wheel
  - Pan by dragging
  - Click nodes to explore topics
  - Toggle labels visibility
  - Reset view to initial state
- **Semantic Connections**: Topics linked by name similarity

## Data Refresh

The data can be refreshed to get the latest trends:

```bash
# Refresh all data
python save_data_csv.py
python fetch_subfield_topics.py

# Or refresh specific components
python fetch_subfield_topics.py  # Just topics
```

## Similarity Algorithm

The application uses TF-IDF vectorization with cosine similarity to determine relationships:

1. **Text Preprocessing**: Lowercase, remove stopwords, extract n-grams (1-3 grams)
2. **TF-IDF Vectorization**: 
   - `max_df=0.8`: Ignores terms appearing in >80% of documents
   - `sublinear_tf=True`: Uses logarithmic TF scaling
   - `ngram_range=(1,3)`: Captures phrases and concepts
3. **Cosine Similarity**: Measures angular similarity between vectors
4. **Threshold Filtering**: Links created for similarity > 0.12

## Future Enhancements

- [ ] Add more domains beyond Physical Sciences


## Acknowledgments

- [OpenAlex](https://openalex.org/) for providing comprehensive scholarly data
- [D3.js](https://d3js.org/) for powerful data visualization capabilities
- [scikit-learn](https://scikit-learn.org/) for machine learning utilities
- The open science community for making research data accessible
