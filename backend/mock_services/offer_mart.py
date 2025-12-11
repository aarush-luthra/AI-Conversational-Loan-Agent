from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/get-limit', methods=['POST'])
def limit():
    # Everyone has a pre-approved limit of 2 Lakhs for this demo
    return jsonify({"pre_approved_limit": 200000}), 200

if __name__ == '__main__': app.run(port=5003)