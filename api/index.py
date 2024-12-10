from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from collections import defaultdict
from flask import make_response
from flask_cors import CORS

# Load environment variables
load_dotenv()
app = Flask(__name__, template_folder='Templates')
CORS(app)

@app.route('/')
def index():
    return render_template('Index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
