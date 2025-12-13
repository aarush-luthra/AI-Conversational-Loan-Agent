import sqlite3
from flask import Flask, request, jsonify
app = Flask(__name__)
DB_PATH = 'mock_bank.db'

@app.route('/get-limit', methods=['POST'])
def get_limit():
    pan = request.json.get('pan') # Now requires PAN!
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT pre_approved_limit FROM customers WHERE pan=?", (pan,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({"pre_approved_limit": row['pre_approved_limit']}), 200
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__': app.run(port=5003)