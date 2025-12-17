import sqlite3
import os
from flask import Flask, request, jsonify
app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_bank.db')

@app.route('/get-score', methods=['POST'])
def get_score():
    pan = request.json.get('pan') # Now requires PAN!
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT credit_score FROM customers WHERE pan=?", (pan,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({"credit_score": row['credit_score']}), 200
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__': app.run(port=5002)