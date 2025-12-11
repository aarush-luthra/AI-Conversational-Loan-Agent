from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/verify-kyc', methods=['POST'])
def verify():
    pan = request.json.get('pan', '')
    # Mock: PAN starting with 'A' is valid
    if pan.startswith('A'): 
        return jsonify({"status": "verified", "name": "John Doe", "address": "123 Tech Park, Bangalore"})
    return jsonify({"status": "failed"}), 400

if __name__ == '__main__': app.run(port=5001)