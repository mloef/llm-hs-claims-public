from flask import Flask, request, jsonify, send_from_directory
from striprtf.striprtf import rtf_to_text
import openai
import json
import pickle
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from flask_cors import CORS


API_KEY = 'sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
openai.api_key = API_KEY

app = Flask(__name__)
CORS(app)

@app.route('/api/hello', methods=['POST'])
def hello():
    """
    This function handles the POST request to the /api/hello endpoint.
    It takes the insurance provider letter and insurance terms as input files,
    processes them, and returns a JSON response with the results.
    """
    decision = request.files['insurance_provider_letter']
    contract = request.files['insurance_terms']

    collection, sentences = _initialize_db(contract.read())

    rtf_data = decision.read().decode('utf-8')

    sample_procedure = rtf_to_text(rtf_data)

    results = _query(sample_procedure, collection, sentences)
    print("FINAL RESULTS")
    print(results)

    response = results

    return jsonify(response), 200

@app.route('/submit/claim', methods=['POST', 'GET'])
def claim():
    """
    This function handles the POST and GET requests to the /submit/claim endpoint.
    It takes a claim as input and submits it using the _handle_claim_submission function.
    """
    claim = 'placeholder'
    return _handle_claim_submission(claim)

def _handle_claim_submission(claim):
    """
    This function handles the claim submission process.
    It logs in to the insurance website, navigates to the claim submission page,
    fills out the form, and submits the claim.
    """
    # ... (rest of the code)

def _query(data, collection, sentences):
    """
    This function queries the GPT-4 model with the given data, collection, and sentences.
    It processes the response and returns the results.
    """
    # ... (rest of the code)

def _initialize_db(file=None):
    """
    This function initializes the database with the given file.
    If no file is provided, it uses a default file.
    It returns the collection and sentences.
    """
    # ... (rest of the code)

def _query_db(query, collection, sentences):
    """
    This function queries the database with the given query, collection, and sentences.
    It returns the results.
    """
    # ... (rest of the code)

if __name__ == '__main__':
    collection, sentences = _initialize_db()

    with open('claim.rtf', 'r') as f:
        rtf_data = f.read()

    sample_procedure = rtf_to_text(rtf_data)

    print(_query(sample_procedure, collection, sentences))
