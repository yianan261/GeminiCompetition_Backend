"""Write all the APIs here"""

import os
from flask import Blueprint, request
from helpers import api_response

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


## firebase APIs
from firebase import fetch_documents, write_to_collection


# Fetch all documents
@api_blueprint.route("/fetch-all-documents", methods=["GET"])
def fetch_docs():
    return api_response(
        success=True, message="successful", data=fetch_documents(), status=200
    )


# Fetch document by Collection and Document ID
# Example: http://localhost:5000/api/fetch-document-by-id?document_id=1&collection_name=users
@api_blueprint.route("/fetch-document-by-id", methods=["GET"])
def fetch_doc_by_id():
    document_id = request.args.get("document_id")
    collection_name = request.args.get("collection_name")
    return api_response(
        success=True,
        message="successful",
        data=fetch_documents(document_id=document_id, collection_name=collection_name),
        status=200,
    )
