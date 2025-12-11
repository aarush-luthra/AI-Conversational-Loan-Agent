from flask import Flask, jsonify
import random
app = Flask(__name__)

@app.route('/get-score', methods=['POST'])
def score():
    # Returns a random score between 650 and 850
    return jsonify({"credit_score": random.randint(650, 850)}), 200

if __name__ == '__main__': app.run(port=5002)