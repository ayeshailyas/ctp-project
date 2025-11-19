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
        data_cache = {
            'fields': pd.read_csv(os.path.join(DATA_DIR, 'fields.csv')),
            'subfields': pd.read_csv(os.path.join(DATA_DIR, 'top_subfields_us.csv')),
            'funders': pd.read_csv(os.path.join(DATA_DIR, 'subfield_funders_us.csv')),
            'topics': pd.read_csv(os.path.join(DATA_DIR, 'top_topics_us.csv'))
        }
        
        # Load subfield topics data (top 20 topics for each of top 10 subfields)
        subfield_topics_path = os.path.join(DATA_DIR, 'subfield_topics_us.csv')
        if os.path.exists(subfield_topics_path):
            data_cache['subfield_topics'] = pd.read_csv(subfield_topics_path)
        
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
        'version': '1.0',
        'endpoints': {
            '/api/health': 'Check API health and data status',
            '/api/fields': 'Get all fields in the domain',
            '/api/subfields': 'Get top 10 US subfields',
            '/api/subfields/<id>': 'Get specific subfield by ID',
            '/api/funders': 'Get all subfield funders',
            '/api/funders/<subfield_id>': 'Get funder for specific subfield',
            '/api/topics': 'Get top 10 US topics',
            '/api/topics/<id>': 'Get specific topic by ID',
            '/api/search/subfield?q=<query>': 'Search subfields by name',
            '/api/search/topic?q=<query>': 'Search topics by name',
            '/api/summary': 'Get complete data summary',
            '/api/reload': 'Reload data from CSV files',
            '/api/subfields/graph': 'Get subfields graph data with semantic similarity',
            '/api/topics/popular': 'Get top topics for all top 10 US subfields',
            '/api/topics/subfield/<subfield_id>': 'Get topics graph for a specific subfield'
        }
    })


@app.route('/api/health')
def health():
    data = load_data()
    
    if data is None:
        return jsonify({
            'status': 'error',
            'message': 'Data files not found. Run fetch_and_save_data.py first.'
        }), 500
    
    fetch_date = data['fields']['fetch_date'].iloc[0] if 'fetch_date' in data['fields'].columns else 'Unknown'
    
    return jsonify({
        'status': 'healthy',
        'data_loaded': True,
        'last_updated': fetch_date,
        'records': {
            'fields': len(data['fields']),
            'subfields': len(data['subfields']),
            'funders': len(data['funders']),
            'topics': len(data['topics']),
            'subfield_topics': len(data.get('subfield_topics', pd.DataFrame()))
        }
    })


@app.route('/api/fields')
def get_fields():
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    fields = data['fields'].to_dict('records')
    return jsonify({
        'count': len(fields),
        'data': fields
    })


@app.route('/api/subfields')
def get_subfields():
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    subfields = data['subfields'].to_dict('records')
    return jsonify({
        'count': len(subfields),
        'data': subfields
    })


@app.route('/api/subfields/<subfield_id>')
def get_subfield_by_id(subfield_id):
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        subfield_id = int(subfield_id)
    except ValueError:
        return jsonify({'error': 'Invalid subfield ID'}), 400
    
    subfield = data['subfields'][data['subfields']['id'] == subfield_id]
    
    if subfield.empty:
        return jsonify({'error': 'Subfield not found'}), 404
    
    subfield_data = subfield.iloc[0].to_dict()
    
    funder = data['funders'][data['funders']['subfield_id'] == subfield_id]
    if not funder.empty:
        subfield_data['top_funder'] = funder.iloc[0].to_dict()
    
    return jsonify(subfield_data)


@app.route('/api/funders')
def get_funders():
    """Get all subfield funders."""
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    funders = data['funders'].to_dict('records')
    return jsonify({
        'count': len(funders),
        'data': funders
    })


@app.route('/api/funders/<subfield_id>')
def get_funder_by_subfield(subfield_id):
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        subfield_id = int(subfield_id)
    except ValueError:
        return jsonify({'error': 'Invalid subfield ID'}), 400
    
    funder = data['funders'][data['funders']['subfield_id'] == subfield_id]
    
    if funder.empty:
        return jsonify({'error': 'Funder not found for this subfield'}), 404
    
    return jsonify(funder.iloc[0].to_dict())


@app.route('/api/topics')
def get_topics():
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    topics = data['topics'].to_dict('records')
    return jsonify({
        'count': len(topics),
        'data': topics
    })


@app.route('/api/topics/<topic_id>')
def get_topic_by_id(topic_id):
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    topic = data['topics'][data['topics']['id'] == topic_id]
    
    if topic.empty:
        return jsonify({'error': 'Topic not found'}), 404
    
    return jsonify(topic.iloc[0].to_dict())


@app.route('/api/search/subfield')
def search_subfield():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    results = data['subfields'][
        data['subfields']['name'].str.contains(query, case=False, na=False)
    ]
    
    return jsonify({
        'query': query,
        'count': len(results),
        'data': results.to_dict('records')
    })


@app.route('/api/search/topic')
def search_topic():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    results = data['topics'][
        data['topics']['name'].str.contains(query, case=False, na=False)
    ]
    
    return jsonify({
        'query': query,
        'count': len(results),
        'data': results.to_dict('records')
    })


@app.route('/api/summary')
def get_summary():
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    fetch_date = data['fields']['fetch_date'].iloc[0] if 'fetch_date' in data['fields'].columns else 'Unknown'
    
    return jsonify({
        'last_updated': fetch_date,
        'fields': data['fields'].to_dict('records'),
        'top_subfields': data['subfields'].to_dict('records'),
        'subfield_funders': data['funders'].to_dict('records'),
        'top_topics': data['topics'].to_dict('records')
    })


@app.route('/api/reload', methods=['POST'])
def reload():
    try:
        reload_data()
        return jsonify({
            'status': 'success',
            'message': 'Data reloaded successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/topics/popular')
def get_popular_topics():
    """
    Get top topics for all top 10 US subfields.
    Returns organized data by subfield with top 20 topics per subfield.
    """
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    if 'subfield_topics' not in data:
        return jsonify({
            'error': 'Subfield topics data not found. Run fetch_subfield_topics.py to fetch the data.'
        }), 404
    
    topics_df = data['subfield_topics']
    
    # Group topics by subfield_id
    organized_topics = {}
    subfield_info = {}
    
    for _, topic in topics_df.iterrows():
        subfield_id = str(topic['subfield_id'])
        
        if subfield_id not in organized_topics:
            organized_topics[subfield_id] = []
            # Store subfield info
            subfield_info[subfield_id] = {
                'id': subfield_id,
                'name': topic.get('subfield', 'Unknown'),
                'field': topic.get('field', 'Unknown')
            }
        
        organized_topics[subfield_id].append({
            'id': str(topic['id']),
            'display_name': topic['name'],
            'us_works_count': topic['us_works_count'],
            'field': topic.get('field', 'Unknown'),
            'subfield': topic.get('subfield', 'Unknown')
        })
    
    return jsonify({
        'subfields': subfield_info,
        'topics_by_subfield': organized_topics,
        'total_subfields': len(organized_topics),
        'total_topics': len(topics_df)
    })


@app.route('/api/topics/subfield/<subfield_id>')
def get_topics_by_subfield(subfield_id):
    """
    Get topics for a specific subfield based on US works count.
    Returns graph data with semantic similarity for visualization.
    """
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    if 'subfield_topics' not in data:
        return jsonify({
            'error': 'Subfield topics data not found. Run fetch_subfield_topics.py to fetch the data.'
        }), 404
    
    try:
        subfield_id_int = int(subfield_id)
    except ValueError:
        return jsonify({'error': 'Invalid subfield ID'}), 400
    
    # Filter topics by subfield ID (need to check if subfield matches)
    # Get topics for this specific subfield using subfield_id
    topics_df = data['subfield_topics']
    # CSV values are read as integers by pandas
    matching_topics = topics_df[topics_df['subfield_id'] == subfield_id_int]
    
    if len(matching_topics) == 0:
        return jsonify({
            'error': f'No topics found for subfield ID: {subfield_id}',
            'subfield_id': subfield_id
        }), 404
    
    # Get subfield name from the first matching topic
    subfield_name = matching_topics.iloc[0].get('subfield', 'Unknown')
    
    # Prepare node data
    nodes = []
    topic_names = []
    min_works = matching_topics['us_works_count'].min()
    max_works = matching_topics['us_works_count'].max()
    works_range = max_works - min_works if max_works != min_works else 1
    
    for idx, row in matching_topics.iterrows():
        # Normalize size based on us_works_count (for visualization)
        normalized_size = 10 + ((row['us_works_count'] - min_works) / works_range) * 40
        
        nodes.append({
            'id': str(row['id']),
            'name': row['name'],
            'us_works_count': int(row['us_works_count']),
            'field': row['field'],
            'size': float(normalized_size)
        })
        topic_names.append(row['name'])
    
    # Compute semantic similarity using TF-IDF and cosine similarity
    links = []
    try:
        if len(topic_names) > 1:
            vectorizer = TfidfVectorizer(
                stop_words='english', 
                lowercase=True, 
                ngram_range=(1, 3),  # Include trigrams for better semantic matching
                max_df=0.8,  # Ignore terms that appear in more than 80% of documents
                min_df=1,   # Include terms that appear in at least 1 document
                norm='l2',  # Use L2 normalization
                use_idf=True,
                smooth_idf=True,
                sublinear_tf=True  # Use sublinear TF scaling
            )
            tfidf_matrix = vectorizer.fit_transform(topic_names)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Create links based on similarity threshold
            # Use moderate threshold for balanced connectivity
            similarity_threshold = 0.12
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    similarity = float(similarity_matrix[i][j])
                    if similarity > similarity_threshold:
                        links.append({
                            'source': nodes[i]['id'],
                            'target': nodes[j]['id'],
                            'similarity': similarity,
                            'strength': similarity
                        })
    except Exception as e:
        print(f"Error computing similarity: {e}")
        links = []
    
    return jsonify({
        'subfield_id': subfield_id_int,
        'subfield_name': subfield_name,
        'nodes': nodes,
        'links': links,
        'min_works_count': int(min_works),
        'max_works_count': int(max_works)
    })


@app.route('/api/subfields/graph')
def get_subfields_graph():
    """
    Get subfields graph data with semantic similarity.
    Returns nodes (subfields) and links (similarity edges) for force-directed graph.
    """
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    subfields_df = data['subfields']
    
    if len(subfields_df) == 0:
        return jsonify({'error': 'No subfields data available'}), 404
    
    # Prepare node data
    nodes = []
    subfield_names = []
    min_works = subfields_df['us_works_count'].min()
    max_works = subfields_df['us_works_count'].max()
    works_range = max_works - min_works if max_works != min_works else 1
    
    for idx, row in subfields_df.iterrows():
        # Normalize size based on us_works_count (for visualization)
        # Scale between 10 and 50 (pixels)
        normalized_size = 10 + ((row['us_works_count'] - min_works) / works_range) * 40
        
        nodes.append({
            'id': str(row['id']),
            'name': row['name'],
            'us_works_count': int(row['us_works_count']),
            'size': float(normalized_size)
        })
        subfield_names.append(row['name'])
    
    # Compute semantic similarity using TF-IDF and cosine similarity
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english', 
            lowercase=True, 
            ngram_range=(1, 3),  # Include trigrams for better semantic matching
            max_df=0.8,  # Ignore terms that appear in more than 80% of documents
            min_df=1,   # Include terms that appear in at least 1 document
            norm='l2',  # Use L2 normalization
            use_idf=True,
            smooth_idf=True,
            sublinear_tf=True  # Use sublinear TF scaling
        )
        tfidf_matrix = vectorizer.fit_transform(subfield_names)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Create links based on similarity threshold
        # Only connect subfields with similarity above threshold
        # Use moderate threshold for balanced connectivity
        similarity_threshold = 0.12  # Adjust this to control edge density
        links = []
        
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                similarity = float(similarity_matrix[i][j])
                if similarity > similarity_threshold:
                    links.append({
                        'source': nodes[i]['id'],
                        'target': nodes[j]['id'],
                        'similarity': similarity,
                        'strength': similarity  # Used for link width/thickness
                    })
        
    except Exception as e:
        print(f"Error computing similarity: {e}")
        # Return graph without links if similarity computation fails
        links = []
    
    return jsonify({
        'nodes': nodes,
        'links': links,
        'min_works_count': int(min_works),
        'max_works_count': int(max_works)
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
