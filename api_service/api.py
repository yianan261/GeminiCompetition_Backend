"""Write all the APIs here"""

import os, sys
from dotenv import load_dotenv

load_dotenv()
from flask import Blueprint, request, current_app
from helpers import api_response

api_blueprint = Blueprint("api_blueprint", __name__)


def get_data_retriever():
    return current_app.config["DATA_RETRIEVER"]


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
    document_id = request.args.get("document_id")
    collection_name = request.args.get("collection_name")
    try:
        data = get_data_retriever().fetch_document_by_id(
            document_id=document_id, collection_name=collection_name
        )
        return api_response(success=True, message="successful", data=data, status=200)
    except Exception as e:
        print(f"Error fetching document by ID: {e}")
        return api_response(success=False, message=str(e), status=500)


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
        data=get_data_retriever().write_to_collection(collection_name, data),
        status=200,
    )


# Users 
@api_blueprint.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        data = get_data_retriever().fetch_document_by_id("users", user_id)
        return api_response(
            success=True, message="User retrieved", data=data, status=200
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/users", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        get_data_retriever().write_to_collection_with_id("users", user_id, data)
        return api_response(success=True, message="User created", data=data, status=201)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# Saved Places
@api_blueprint.route("/saved-places", methods=["POST"])
def save_place():
    try:
        data = request.get_json()
        get_data_retriever().write_to_collection("saved_places", data)
        return api_response(success=True, message="Place saved", data=data, status=201)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/saved-places", methods=["GET"])
def get_saved_places():
    try:
        user_id = request.args.get("user_id")
        data = get_data_retriever().fetch_document_by_criteria(
            "saved_places", "user_id", user_id
        )
        return api_response(
            success=True, message="Saved places retrieved", data=data, status=200
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/saved-places/<place_id>", methods=["DELETE"])
def delete_saved_place(place_id):
    try:
        get_data_retriever().delete_document_by_id("saved_places", place_id)
        return api_response(success=True, message="Place deleted", status=200)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# Trips
@api_blueprint.route("/trips", methods=["POST"])
def create_trip():
    try:
        data = request.get_json()
        trip_id = data.get("trip_id")
        get_data_retriever().write_to_collection_with_id("trips", trip_id, data)
        return api_response(success=True, message="Trip created", data=data, status=201)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/trips/<trip_id>", methods=["GET"])
def get_trip(trip_id):
    try:
        data = get_data_retriever().fetch_document_by_id("trips", trip_id)
        return api_response(
            success=True, message="Trip retrieved", data=data, status=200
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/trips/<trip_id>", methods=["PUT"])
def update_trip(trip_id):
    try:
        data = request.get_json()
        get_data_retriever().write_to_collection_with_id("trips", trip_id, data)
        return api_response(success=True, message="Trip updated", data=data, status=200)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/trips/<trip_id>", methods=["DELETE"])
def delete_trip(trip_id):
    try:
        get_data_retriever().delete_document_by_id("trips", trip_id)
        return api_response(success=True, message="Trip deleted", status=200)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# Places
@api_blueprint.route("/places", methods=["POST"])
def create_place():
    try:
        data = request.get_json()
        place_id = data.get("place_id")
        get_data_retriever().write_to_collection_with_id("places", place_id, data)
        return api_response(
            success=True, message="Place created", data=data, status=201
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/places/<place_id>", methods=["GET"])
def get_place(place_id):
    try:
        data = get_data_retriever().fetch_document_by_id("places", place_id)
        return api_response(
            success=True, message="Place retrieved", data=data, status=200
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/places/<place_id>", methods=["PUT"])
def update_place(place_id):
    try:
        data = request.get_json()
        get_data_retriever().write_to_collection_with_id("places", place_id, data)
        return api_response(
            success=True, message="Place updated", data=data, status=200
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/places/<place_id>", methods=["DELETE"])
def delete_place(place_id):
    try:
        get_data_retriever().delete_document_by_id("places", place_id)
        return api_response(success=True, message="Place deleted", status=200)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)
