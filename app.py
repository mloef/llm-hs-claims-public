
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
    #email = request.form['email']
    decision = request.files['insurance_provider_letter']
    contract = request.files['insurance_terms']
    # print(email, decision, contract)

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
    #claim = request.form['claim']
    claim = 'placeholder'
    return _handle_claim_submission(claim)


def _handle_claim_submission(claim):
    cookies = pickle.load(open("cookies.pkl", "rb"))
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.anthem.com")
    for cookie in cookies:
        cookie['domain'] = ".anthem.com"
        driver.add_cookie(cookie)

    # Navigate to login screen.
    login_wait = WebDriverWait(driver, 30)
    first_login = login_wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Log In")))
    first_login.click()
    login_wait = WebDriverWait(driver, 30)
    login_element = login_wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Log In")))
    login_element.click()

    # Grab login credentials.
    with open("credentials.json", "r") as file:
        data = json.load(file)
    email = data["username"]
    password = data["password"]

    # Enter login credentials
    email_wait = WebDriverWait(driver, 30)
    email_field = email_wait.until(EC.presence_of_element_located((By.ID, "txtUsername")))
    email_field.send_keys(email)
    time.sleep(3)
    password_field = driver.find_element(By.ID, "txtPassword")
    password_field.send_keys(password)
    driver.find_element(By.ID, "btnLogin").click()

    # Navigate to claim submission.
    driver.get(
        "https://membersecure.anthem.com/member/message-center/new-message?category=56")

    # Setup claims form
    message_wait = WebDriverWait(driver, 30)
    message_type = message_wait.until(EC.presence_of_element_located((By.ID, "ddlNewMsgCat_button")))
    message_type.click()
    # Element 104 is "Greviances / Appeals"
    desired_item = driver.find_element(By.CSS_SELECTOR, "[data-value='104']")
    desired_item.click()

    message_subtype = driver.find_element(By.ID, "ddlNewMsgCatSub_button")
    message_subtype.click()

    desired_subitem = driver.find_element(
        By.CSS_SELECTOR, "[data-value='487']")
    desired_subitem.click()

    title = driver.find_element(By.ID, "txtNewMsgTitleText")
    title.send_keys("Test Message")

    greviance_radio_field = driver.find_element(
        By.ID, "lbl_rbtnAppealType-appealGreivance-1")
    greviance_radio_field.click()

    wait(100)

    return 'OK', 200


def _query(data, collection, sentences):
    prompt0 = 'Provide a list of medical procedures from the following text in json format. Repeat all details as provided, and describe the procedure in plain english.'
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt0},
            {"role": "user", "content": data},
        ],
        temperature=0,
    )

    for choice in response["choices"]:
        procedures = json.loads(str(choice["message"]["content"]))

    prompt1 = ''.join([#'You are an expert in health insurance claims and a strident patient advocate.',
                       'You are provided a description of a medical procedure with costs, in json format.',
                       'You are also provided relevant pieces of the insurance contract, including the copayment and coinsurance.',
                       'Determine whether or not the plan paid the correct amounts for this procedure and succintly summarize why or why not.',
                       ])

    results = []

    for procedure in procedures:
        search_results = _query_db(
            procedure['description'], collection, sentences)
        print('SEARCH RESULTS')
        print(search_results)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt1},
                {"role": "system", "content": '\n'.join(search_results)},
                {"role": "user", "content": str(procedure)},
            ],
            temperature=0,
        )

        print("PROCEDURE JSON")
        pprint(procedure)

        result = response['choices'][0]["message"]["content"]
        print("RESULT")
        print(result)
        results.append(result)

    return '\n'.join(results)


def _initialize_db(file=None):
    from tika import parser

    # Parse the PDF file and extract the text content
    if not file:
        parsed_pdf = parser.from_file('4CDFIND01012020.pdf')
    else:
        parsed_pdf = parser.from_buffer(file)
    text = parsed_pdf['content']
    with open('tike-output.txt', 'w') as f:
        f.write(text)

    from pysbd import Segmenter

    # create a sentence segmenter for English
    segmenter = Segmenter(language="en", clean=True)
    # text = "This is a sample text. It contains a few sentences. And it demonstrates the use of PySBD."
    sentences = segmenter.segment(text)  # get a list of sentences

    import chromadb
    from chromadb.utils import embedding_functions
    from chromadb.config import Settings

    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
                                      persist_directory="chroma",))

    try:
        print("loading db")
        collection = client.get_collection("llm-hs-claims",  embedding_function=embedding_functions.OpenAIEmbeddingFunction(
            api_key=API_KEY,
            model_name="text-embedding-ada-002"
        ))
    except Exception as e:
        print('load failed. reinitializing')
        collection = client.create_collection("llm-hs-claims", embedding_function=embedding_functions.OpenAIEmbeddingFunction(
            api_key=API_KEY,
            model_name="text-embedding-ada-002"
        ))

        chunk_size = 1000

        for i in range(0, len(sentences), chunk_size):
            chunk = sentences[i:i+chunk_size]
            collection.add(
                documents=chunk,
                ids=[str(i) for i in range(i, i+len(chunk))],
                metadatas=[{"userID": "0", 'index': str(
                    i)} for i in range(i, i+len(chunk))]
            )

    return collection, sentences


def _query_db(query, collection, sentences):
    # print(query)
    TOP_K = 2

    CONTEXT_WINDOW = 50

    query_result = collection.query(
        query_texts=[query],
        n_results=TOP_K,
        where={"userID": "0"},
    )

    # pprint.pprint(query_result)

    result = []
    for id in query_result['ids'][0]:
        index = int(id)
        result.append(' '.join(sentences[i] for i in range(
            index-CONTEXT_WINDOW//2, index+CONTEXT_WINDOW//2)))

    return result


# hardcode demo if main
if __name__ == '__main__':
    collection, sentences = _initialize_db()

    with open('claim.rtf', 'r') as f:
        rtf_data = f.read()

    sample_procedure = rtf_to_text(rtf_data)

    print(_query(sample_procedure, collection, sentences))
