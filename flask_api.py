from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os

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
            '/api/reload': 'Reload data from CSV files'
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
            'topics': len(data['topics'])
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
