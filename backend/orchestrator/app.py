import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# Need to import ast to safely parse stringified dicts from Gemini
import ast 
from agents.master import run_agent

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    try:
        raw_response = run_agent(data.get('message'), data.get('session_id', 'guest'))
        
        # --- CLEANING LOGIC ---
        # Gemini sometimes returns a string that looks like a Python dict
        cleaned_response = raw_response
        if isinstance(raw_response, str):
            stripped = raw_response.strip()
            # Check if it looks like the {'type': 'text', ...} pattern
            if stripped.startswith("{") and "'type': 'text'" in stripped:
                try:
                    # Safely convert string to dict
                    parsed = ast.literal_eval(stripped)
                    # Extract just the text content
                    cleaned_response = parsed.get("text", raw_response)
                except:
                    # If parsing fails, fall back to the raw string
                    pass
                    
        return jsonify({"response": cleaned_response})
    except Exception as e:
        return jsonify({"response": f"System Error: {str(e)}"}), 500

@app.route('/static/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('static/pdfs', filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)