import json
from pathlib import Path
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='.')
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Load JSON data once at startup
DATA_PATH = Path(__file__).parent / 'json1_all_rows.json'
df = pd.DataFrame()

try:
    if DATA_PATH.exists():
        print(f"Loading data from {DATA_PATH}...")
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        df = pd.DataFrame(raw)
        print(f"Loaded {len(df)} records")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Sample divisions: {df['Division'].value_counts().head()}")
    else:
        print(f"ERROR: Data file not found at {DATA_PATH}")
except Exception as e:
    print(f"ERROR loading data: {e}")

def build_series_for_divisions(divisions_list, keyword=None):
    """Build time series data for selected divisions and keywords"""
    if df.empty:
        return {'years': [], 'series': [], 'total': 0, 'error': 'No data loaded'}
    
    # Determine year column
    year_cols = ['Fiscal Year', 'Year', 'publication_year', 'Publication Year']
    year_col = next((c for c in year_cols if c in df.columns), None)
    
    if year_col is None:
        return {'years': [], 'series': [], 'total': 0, 'error': 'No year column found'}
    
    # Parse keywords
    keywords = []
    if keyword:
        if isinstance(keyword, (list, tuple)):
            keywords = [k.strip() for k in keyword if k and str(k).strip()]
        else:
            keywords = [k.strip() for k in str(keyword).split(',') if k.strip()]
    
    # If no divisions provided, use all
    if not divisions_list:
        divisions_list = sorted(df['Division'].dropna().unique().tolist())
    
    years_set = set()
    series = []
    
    def get_counts_by_year(subset_df):
        """Get year counts from a dataframe subset"""
        ys = pd.to_numeric(subset_df[year_col], errors='coerce').dropna().astype(int)
        return ys.value_counts().to_dict()
    
    # Build series for each division
    for div in divisions_list:
        # Match division - handle partial matches
        mask = df['Division'].apply(
            lambda v: isinstance(v, str) and div.lower() in v.lower()
        )
        subset = df[mask]
        
        if len(subset) == 0:
            continue
            
        counts_map = get_counts_by_year(subset)
        years_set.update(counts_map.keys())
        series.append({
            'name': div,
            'counts_map': counts_map,
            'total': len(subset)
        })
    
    # Build series for each keyword
    if keywords:
        for kw in keywords:
            kw_lower = kw.lower()
            
            # Filter by divisions first if specified
            if divisions_list:
                combined_mask = df['Division'].apply(
                    lambda v: isinstance(v, str) and any(
                        div.lower() in v.lower() for div in divisions_list
                    )
                )
                subset_all = df[combined_mask]
            else:
                subset_all = df
            
            # Search in title and abstract
            def row_has_keyword(row):
                title = row.get('Project Title', '')
                abstract = row.get('Task Abstract/Description', '')
                title_str = str(title).lower() if pd.notna(title) else ''
                abstract_str = str(abstract).lower() if pd.notna(abstract) else ''
                return kw_lower in title_str or kw_lower in abstract_str
            
            subset_kw = subset_all[subset_all.apply(row_has_keyword, axis=1)]
            
            if len(subset_kw) > 0:
                counts_map = get_counts_by_year(subset_kw)
                years_set.update(counts_map.keys())
                series.append({
                    'name': f'"{kw}"',
                    'counts_map': counts_map,
                    'total': len(subset_kw)
                })
    
    # Build final structure
    years = sorted(list(years_set))
    years_str = [str(int(y)) for y in years]
    
    for s in series:
        counts_map = s.pop('counts_map', {})
        s['counts'] = [int(counts_map.get(int(y), 0)) for y in years]
    
    total = sum(s.get('total', 0) for s in series)
    
    return {
        'years': years_str,
        'series': series,
        'total': total,
        'year_col': year_col
    }


@app.route('/api/trends', methods=['POST', 'OPTIONS'])
def api_trends():
    """API endpoint for trends data"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    try:
        payload = request.get_json() or {}
        divisions = payload.get('divisions', [])
        keyword = payload.get('keyword', '')
        
        print(f"API request - divisions: {divisions}, keyword: {keyword}")
        
        result = build_series_for_divisions(divisions, keyword=keyword)
        result['requested'] = {'divisions': divisions, 'keyword': keyword}
        
        print(f"Returning {len(result.get('series', []))} series")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in api_trends: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/Trends.html')
def trends():
    return send_from_directory('.', 'Trends.html')


@app.route('/manager.html')
def manager():
    return send_from_directory('.', 'manager.html')


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_file(path):
    try:
        return send_from_directory('.', path)
    except:
        return jsonify({'error': 'File not found'}), 404


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'records': len(df),
        'has_data': not df.empty
    })


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response


if __name__ == '__main__':
    print("=" * 60)
    print("Brickonaut Trends API Starting...")
    print("=" * 60)
    print(f"Data loaded: {len(df)} records")
    print(f"Server: http://localhost:5000")
    print(f"Trends: http://localhost:5000/Trends.html")
    print(f"Health: http://localhost:5000/api/health")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)