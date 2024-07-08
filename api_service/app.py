import os
import firebase_admin
from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from api import api_blueprint, initialize_data_retriever
from helpers import api_response
from firebase_admin import credentials, firestore
from data_retriever import DataRetriever

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
service_account_key_path = os.getenv("GEMINI_KEY")
# base_path = os.path.abspath(os.path.dirname(__file__))
# parent_path = os.path.abspath(os.path.join(base_path, os.pardir))

## Blueprint
app.register_blueprint(api_blueprint, url_prefix="/api")

# yian firebase test key
# service_account_key_path = os.path.join(parent_path, "gem_key.json")

cred = credentials.Certificate(service_account_key_path)
firebase_admin.initialize_app(cred)

# connect to firestore emulator for local test
if os.getenv("FIRESTORE_EMULATOR_HOST"):
    firestore_client = firestore.client(options={"projectId": "geminiapp-88748"})
else:
    firestore_client = firestore.client()

app.config["FIRESTORE"] = firestore_client

# DataRetriever singleton
with app.app_context():
    data_retriever = DataRetriever(firestore_client)
    app.config["DATA_RETRIEVER"] = data_retriever
    initialize_data_retriever(app)


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


### TODO: FIREBASE LOGIC GOES HERE @kasi

print()
PORT = os.getenv("PORT", "5000")

if __name__ == "__main__":
    app.run(debug=True, port=int(PORT))
