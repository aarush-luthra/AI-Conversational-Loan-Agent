import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agents.master import run_agent

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    try:
        response = run_agent(data.get('message'), data.get('session_id', 'guest'))
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

@app.route('/static/pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('static/pdfs', filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)