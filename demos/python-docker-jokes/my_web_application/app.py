from flask import Flask, jsonify, render_template
import json
import random

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/joke')
def tell_joke():
    with open('jokes.json') as f:
        jokes = json.load(f)
    joke = random.choice(jokes)
    return jsonify({'joke': joke})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
