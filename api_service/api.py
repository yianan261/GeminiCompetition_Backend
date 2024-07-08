"""Write all the APIs here"""

import os, sys
from dotenv import load_dotenv

load_dotenv()
from flask import Blueprint, request
from helpers import api_response
from data_retriever import DataRetriever

data_retriever = DataRetriever()

api_blueprint = Blueprint("api_blueprint", __name__)


@api_blueprint.route("/", methods=["GET"])
def healthcheck():
    return api_response(
        success=True,
        message="App is alive",
        data={"message": "App is alive"},
        status=200,
    )


@api_blueprint.route("/test-hello-world", methods=["POST"])
def test_hello():
    return api_response(
        success=True, message="successful", data={"hello": "world"}, status=200
    )


# Fetch document by Collection and Document ID
# Example: http://localhost:5000/api/fetch-document-by-id?document_id=1&collection_name=users
@api_blueprint.route("/fetch-document-by-id", methods=["GET"])
def fetch_doc_by_id():
    print("fetch_doc_by_id", request.args.to_dict())
    document_id = request.args.get("document_id")
    collection_name = request.args.get("collection_name")
    return api_response(
        success=True,
        message="successful",
        data=data_retriever.fetch_document_by_id(
            document_id=document_id, collection_name=collection_name
        ),
        status=200,
    )


# Fetch document by Collection
# Example: http://localhost:5000/api/fetch-all-documents?collection_name=users
# Body: {key: value}
@api_blueprint.route("/write-document", methods=["POST"])
def write_document():
    data = request.get_json()
    collection_name = request.args.get("collection_name")
    return api_response(
        success=True,
        message="successful",
        data=data_retriever.write_to_collection(collection_name, data),
        status=200,
    )
