from flask import Flask, jsonify, render_template
import json
import random

app = Flask(__name__)

@app.route('/api/joke', methods=['GET'])
def get_joke():
    with open('src/jokes.json', 'r') as f:
        jokes = json.load(f)
    joke = random.choice(jokes)
    return jsonify(joke)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
