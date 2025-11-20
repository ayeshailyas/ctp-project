from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__)
CORS(app)  

DATA_DIR = "data"

data_cache = None


def load_data():
    global data_cache
    
    if data_cache is not None:
        return data_cache
    
    try:
        # Initialize with base files
        data_cache = {
            'fields': pd.read_csv(os.path.join(DATA_DIR, 'fields.csv')),
            'subfields': pd.read_csv(os.path.join(DATA_DIR, 'top_subfields_us.csv')),
            'funders': pd.read_csv(os.path.join(DATA_DIR, 'subfield_funders_us.csv')),
            'topics': pd.read_csv(os.path.join(DATA_DIR, 'top_topics_us.csv'))
        }
        
        # Load subfield topics data
        subfield_topics_path = os.path.join(DATA_DIR, 'subfield_topics_us.csv')
        if os.path.exists(subfield_topics_path):
            data_cache['subfield_topics'] = pd.read_csv(subfield_topics_path)

        # --- NEW: Load Yearly Trends Data ---
        yearly_sf_path = os.path.join(DATA_DIR, 'yearly_subfields.csv')
        if os.path.exists(yearly_sf_path):
            data_cache['yearly_subfields'] = pd.read_csv(yearly_sf_path)
            
        yearly_tp_path = os.path.join(DATA_DIR, 'yearly_subfield_topics.csv')
        if os.path.exists(yearly_tp_path):
            data_cache['yearly_topics'] = pd.read_csv(yearly_tp_path)
        
        print("✓ Data loaded successfully")
        return data_cache
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def reload_data():
    global data_cache
    data_cache = None
    return load_data()


@app.route('/')
def home():
    return jsonify({
        'name': 'OpenAlex Physical Sciences API',
        'version': '1.2',
        'endpoints': {
            '/api/health': 'Check API health',
            '/api/trends/years': 'Get list of available years',
            '/api/trends/graph?year=2023': 'Get subfields graph for a specific year',
            '/api/trends/topics?year=2023&subfield_id=X': 'Get topics graph for a subfield in a specific year'
        }
    })


@app.route('/api/health')
def health():
    data = load_data()
    if data is None:
        return jsonify({'status': 'error', 'message': 'Data files not found'}), 500
    return jsonify({'status': 'healthy', 'data_loaded': True})


# --- EXISTING ENDPOINTS ---
@app.route('/api/fields')
def get_fields():
    data = load_data()
    return jsonify({'count': len(data['fields']), 'data': data['fields'].to_dict('records')})

@app.route('/api/subfields/graph')
def get_subfields_graph():
    """Standard All-Time Graph"""
    data = load_data()
    if data is None or 'subfields' not in data: return jsonify({'error': 'Data not loaded'}), 500
    subfields_df = data['subfields'].head(10)
    return generate_graph_from_df(subfields_df)

@app.route('/api/topics/subfield/<subfield_id>')
def get_topics_by_subfield(subfield_id):
    """All-Time Topics for a Subfield"""
    data = load_data()
    if data is None or 'subfield_topics' not in data: return jsonify({'error': 'Data not loaded'}), 500
    try:
        sf_id = int(subfield_id)
        topics_df = data['subfield_topics']
        matching = topics_df[topics_df['subfield_id'] == sf_id]
        if len(matching) == 0: return jsonify({'error': 'No topics found'}), 404
        return generate_graph_from_df(matching)
    except ValueError:
        return jsonify({'error': 'Invalid ID'}), 400


# --- TRENDS ENDPOINTS ---

@app.route('/api/trends/years')
def get_available_years():
    """Returns list of years available in the dataset."""
    data = load_data()
    if data is None or 'yearly_subfields' not in data:
        return jsonify({'error': 'Yearly data not found. Run save_data_csv.py first.'}), 404
    years = sorted(data['yearly_subfields']['year'].unique().tolist())
    return jsonify({'years': years})


@app.route('/api/trends/graph')
def get_yearly_graph():
    """Returns subfields graph for a specific year."""
    year_param = request.args.get('year')
    if not year_param: return jsonify({'error': 'Missing "year" parameter'}), 400
    
    data = load_data()
    if data is None or 'yearly_subfields' not in data: return jsonify({'error': 'Yearly data not found'}), 404
    
    try:
        year = int(year_param)
        df = data['yearly_subfields']
        yearly_df = df[df['year'] == year]
        
        if yearly_df.empty: return jsonify({'error': f'No data found for year {year}'}), 404
            
        graph_data = generate_graph_from_df(yearly_df)
        graph_data['year'] = year
        return jsonify(graph_data)
        
    except ValueError:
        return jsonify({'error': 'Year must be a number'}), 400


@app.route('/api/trends/topics')
def get_yearly_topics_graph():
    """
    Returns topics graph for a specific subfield AND year.
    Usage: /api/trends/topics?year=2023&subfield_id=3315
    """
    year_param = request.args.get('year')
    subfield_id_param = request.args.get('subfield_id')

    if not year_param or not subfield_id_param:
        return jsonify({'error': 'Missing "year" or "subfield_id" parameter'}), 400

    data = load_data()
    if data is None or 'yearly_topics' not in data:
        return jsonify({'error': 'Yearly topics data not found'}), 404

    try:
        year = int(year_param)
        # Convert subfield_id to string first to handle potential type mismatches in CSV
        subfield_id = int(subfield_id_param)
        
        df = data['yearly_topics']
        
        # Filter by both Year and Subfield ID
        filtered_df = df[
            (df['year'] == year) & 
            (df['subfield_id'] == subfield_id)
        ]

        if filtered_df.empty:
            return jsonify({'error': f'No topics found for subfield {subfield_id} in {year}'}), 404

        graph_data = generate_graph_from_df(filtered_df)
        graph_data['year'] = year
        graph_data['subfield_id'] = subfield_id
        return jsonify(graph_data)

    except ValueError:
        return jsonify({'error': 'Parameters must be numbers'}), 400


# --- HELPER FUNCTION ---
def generate_graph_from_df(df):
    nodes = []
    names = []
    
    if df.empty: return {'nodes': [], 'links': []}

    # 1. Build Nodes
    for _, row in df.iterrows():
        nodes.append({
            'id': str(row['id']),
            'name': row['name'],
            'us_works_count': int(row['us_works_count']),
            'size': 10 + (int(row['us_works_count']) / df['us_works_count'].max() * 40)
        })
        names.append(row['name'])
    
    # 2. Build Links (Semantic Similarity)
    links = []
    try:
        if len(names) > 1:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(names)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            threshold = 0.10
            
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    sim = float(similarity_matrix[i][j])
                    if sim > threshold:
                        links.append({
                            'source': nodes[i]['id'],
                            'target': nodes[j]['id'],
                            'similarity': sim,
                            'strength': sim
                        })
    except Exception as e:
        print(f"Similarity error: {e}")
        links = []
        
    return {
        'nodes': nodes,
        'links': links,
        'min_works_count': int(df['us_works_count'].min()),
        'max_works_count': int(df['us_works_count'].max())
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
