import json
from pathlib import Path
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
from kernel import search_publications
import traceback

app = Flask(__name__, static_folder='.')
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})

# Load trends data
DATA_PATH = Path(__file__).parent / 'json1_all_rows.json'
df = pd.DataFrame()

try:
    if DATA_PATH.exists():
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        df = pd.DataFrame(raw)
        print(f"Loaded {len(df)} records for trends")
except Exception as e:
    print(f"ERROR loading trends data: {e}")

# ===== MANAGER ENDPOINTS =====
@app.route('/api/search', methods=['POST', 'OPTIONS'])
def search():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.json
        query = data.get('query', '')
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(search_publications(query))
        finally:
            loop.close()
        
        return jsonify({'answer': result})
    except Exception as e:
        print(f"Error in search: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ===== TRENDS ENDPOINTS =====
@app.route('/api/trends', methods=['POST', 'OPTIONS'])
def api_trends():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        payload = request.get_json() or {}
        divisions = payload.get('divisions', [])
        keyword = payload.get('keyword', '')
        
        result = build_series_for_divisions(divisions, keyword=keyword)
        result['requested'] = {'divisions': divisions, 'keyword': keyword}
        return jsonify(result)
    except Exception as e:
        print(f"Error in trends: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def build_series_for_divisions(divisions_list, keyword=None):
    # [Copy the function from plot.py here - same code]
    if df.empty:
        return {'years': [], 'series': [], 'total': 0}
    
    year_col = next((c for c in ['Fiscal Year', 'Year'] if c in df.columns), None)
    if not year_col:
        return {'years': [], 'series': [], 'total': 0}
    
    keywords = [k.strip() for k in (keyword.split(',') if keyword else [])] if keyword else []
    if not divisions_list:
        divisions_list = sorted(df['Division'].dropna().unique().tolist())
    
    years_set, series = set(), []
    
    def get_counts_by_year(subset_df):
        ys = pd.to_numeric(subset_df[year_col], errors='coerce').dropna().astype(int)
        return ys.value_counts().to_dict()
    
    for div in divisions_list:
        mask = df['Division'].apply(lambda v: isinstance(v, str) and div.lower() in v.lower())
        subset = df[mask]
        if len(subset) == 0:
            continue
        counts_map = get_counts_by_year(subset)
        years_set.update(counts_map.keys())
        series.append({'name': div, 'counts_map': counts_map, 'total': len(subset)})
    
    if keywords:
        for kw in keywords:
            kw_lower = kw.lower()
            subset_all = df if not divisions_list else df[df['Division'].apply(
                lambda v: isinstance(v, str) and any(d.lower() in v.lower() for d in divisions_list))]
            subset_kw = subset_all[subset_all.apply(
                lambda r: kw_lower in str(r.get('Project Title', '')).lower() or 
                         kw_lower in str(r.get('Task Abstract/Description', '')).lower(), axis=1)]
            if len(subset_kw) > 0:
                counts_map = get_counts_by_year(subset_kw)
                years_set.update(counts_map.keys())
                series.append({'name': f'"{kw}"', 'counts_map': counts_map, 'total': len(subset_kw)})
    
    years = sorted(list(years_set))
    years_str = [str(int(y)) for y in years]
    for s in series:
        counts_map = s.pop('counts_map', {})
        s['counts'] = [int(counts_map.get(int(y), 0)) for y in years]
    
    return {'years': years_str, 'series': series, 'total': sum(s.get('total', 0) for s in series), 'year_col': year_col}

# ===== HTML PAGES =====
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/manager.html')
def manager():
    return send_from_directory('.', 'manager.html')

@app.route('/Trends.html')
def trends():
    return send_from_directory('.', 'Trends.html')

@app.route('/scientist.html')
def scientist():
    return send_from_directory('.', 'scientist.html')

@app.route('/architect.html')
def architect():
    return send_from_directory('.', 'architect.html')

@app.route('/<path:path>')
def serve_file(path):
    try:
        return send_from_directory('.', path)
    except:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'manager': True, 'trends': True, 'records': len(df)})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == '__main__':
    print("=" * 60)
    print("BRICKONAUT - Unified Server")
    print("=" * 60)
    print(f"Manager (AI): http://localhost:5000/manager.html")
    print(f"Trends: http://localhost:5000/Trends.html")
    print(f"Home: http://localhost:5000/")
    print(f"Records loaded: {len(df)}")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)