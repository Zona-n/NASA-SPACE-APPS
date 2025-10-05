from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
from kernel import search_publications
import os
import traceback

app = Flask(__name__, static_folder='.')

# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/api/search', methods=['POST', 'OPTIONS'])
def search():
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        print(f"Received query: {query}")
        
        # Create new event loop for async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(search_publications(query))
        finally:
            loop.close()
        
        print(f"Generated response length: {len(result)} characters")
        
        return jsonify({'answer': result})
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error in search endpoint: {error_msg}")
        traceback.print_exc()
        return jsonify({
            'error': f'Server error: {error_msg}'
        }), 500

# Serve HTML files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/manager.html')
def manager():
    return send_from_directory('.', 'manager.html')

@app.route('/scientist.html')
def scientist():
    return send_from_directory('.', 'scientist.html')

@app.route('/architect.html')
def architect():
    return send_from_directory('.', 'architect.html')

# Serve static assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/<path:path>')
def serve_file(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'File not found'}), 404

# Health check endpoint
@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok', 
        'message': 'API is running',
        'port': 5000
    })

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == '__main__':
    print("=" * 60)
    print("Flask API Starting...")
    print("=" * 60)
    print(f"Server: http://localhost:5000")
    print(f"Manager Page: http://localhost:5000/manager.html")
    print(f"Health Check: http://localhost:5000/api/health")
    print("=" * 60)
    print("\nMake sure to access the page through http://localhost:5000")
    print("NOT by opening the HTML file directly!\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')