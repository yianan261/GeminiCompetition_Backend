import os
from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import firebase_admin
from firebase_admin import credentials, auth
from api import api_blueprint
from helpers import api_response
from data_retriever import DataRetriever
from google.cloud import firestore
from csv_uploader import CSVUploader
from llm_tools import LLMTools
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, origins=["http://localhost:6000"])

# Blueprint
app.register_blueprint(api_blueprint, url_prefix="/api")

load_dotenv()
google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(f"Using Google credentials from: {google_credentials_path}")

try:
    cred = credentials.Certificate(google_credentials_path)
    firebase_admin.initialize_app(cred, {"projectId": "wander-6ad0c"})
    firestore_client = firestore.Client()
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Error initializing Firestore client: {e}")

print(f"Firestore project ID: {firestore_client.project}")

# Set up DataRetriever
data_retriever = DataRetriever(firestore_client)
app.config["DATA_RETRIEVER"] = data_retriever

csv_uploader = CSVUploader(data_retriever)
app.config["CSV_UPLOADER"] = csv_uploader

llm = LLMTools(data_retriever)
app.config["LLM_TOOLS"] = llm


# Custom error handler for 400 Bad Request error
@app.errorhandler(400)
def handle_bad_request(error):
    return api_response(
        success=False, status=400, message="Please provide valid credentials!"
    )


# Custom error handler for 401 Not Authorized error
@app.errorhandler(401)
def handle_bad_request(error):
    return api_response(success=False, status=401, message="Not authorized!")


# Custom error handler for 404 Not Found error
@app.errorhandler(404)
def not_found_error(error):
    return api_response(success=False, status=404, message="Method not allowed!")


# Custom error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_server_error(error):
    return api_response(success=False, status=500, message="Internal server error!")


# Generic error handler for other HTTPExceptions
@app.errorhandler(HTTPException)
def handle_http_exception(error):
    response = error.get_response()
    print("http_error_handler", response)
    return api_response(success=False, status=error.code, message=error.description)


# Verify Firebase ID Token
def verify_firebase_id_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying Firebase ID token: {e}")
        return None

PORT = os.getenv("PORT", "6000")
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(PORT))