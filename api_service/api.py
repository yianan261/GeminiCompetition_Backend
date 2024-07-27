"""Write all the APIs here"""

import os
import sys
from dotenv import load_dotenv
from flask import Blueprint, abort, redirect, request, current_app, session
from helpers import api_response
from maps import Maps
from schema.users import user_schema
from jsonschema import validate, ValidationError
from data_retriever import DataRetriever

# Load environment variables
load_dotenv()

# Initialize Maps instances
maps = Maps()

# Create Blueprint
api_blueprint = Blueprint("api_blueprint", __name__)


def get_data_retriever():
    return current_app.config["DATA_RETRIEVER"]


def get_csv_uploader():
    return current_app.config["CSV_UPLOADER"]


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


# TODO: may remove?
def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # authorization required
        else:
            return function()

    return wrapper


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
    data = request.get_json()
    try:
        validate(instance=data, schema=user_schema)
    except ValidationError as e:
        return api_response(
            success=False, message="Invalid create user data", error=str(e), status=400
        )

    google_id = data.get("google_id")

    try:
        # Check if user with google_id already exists
        existing_user = get_data_retriever().fetch_document_by_criteria(
            "users", "google_id", google_id
        )
        if existing_user:
            return api_response(
                success=False,
                message="User with this Google ID already exists",
                status=409,
            )

        # Add the new user using google_id as document ID
        new_user_id = get_data_retriever().write_to_collection_with_id(
            "users", google_id, data
        )
        if new_user_id:
            return api_response(
                success=True,
                message="User created",
                data={"user_id": new_user_id},
                status=201,
            )
        else:
            return api_response(
                success=False, message="Failed to create user", status=500
            )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/updateUser", methods=["POST"])
def update_user():
    try:
        data = request.get_json()
        user_id = request.args.get("user_id")
        get_data_retriever().write_to_collection_with_id("users", user_id, data)
        return api_response(success=True, message="User updated", data=data, status=200)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# Saved Places from Google Takeout
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


# TODO: remove this section (not doing trip app anymore)
# Trips
# @api_blueprint.route("/trips", methods=["POST"])
# def create_trip():
#     try:
#         data = request.get_json()
#         trip_id = data.get("trip_id")
#         get_data_retriever().write_to_collection_with_id("trips", trip_id, data)
#         return api_response(success=True, message="Trip created", data=data, status=201)
#     except Exception as e:
#         return api_response(success=False, message=str(e), status=500)


# @api_blueprint.route("/trips/<trip_id>", methods=["GET"])
# def get_trip(trip_id):
#     try:
#         data = get_data_retriever().fetch_document_by_id("trips", trip_id)
#         return api_response(
#             success=True, message="Trip retrieved", data=data, status=200
#         )
#     except Exception as e:
#         return api_response(success=False, message=str(e), status=500)


# @api_blueprint.route("/trips/<trip_id>", methods=["PUT"])
# def update_trip(trip_id):
#     try:
#         data = request.get_json()
#         get_data_retriever().write_to_collection_with_id("trips", trip_id, data)
#         return api_response(success=True, message="Trip updated", data=data, status=200)
#     except Exception as e:
#         return api_response(success=False, message=str(e), status=500)


# @api_blueprint.route("/trips/<trip_id>", methods=["DELETE"])
# def delete_trip(trip_id):
#     try:
#         get_data_retriever().delete_document_by_id("trips", trip_id)
#         return api_response(success=True, message="Trip deleted", status=200)
#     except Exception as e:
#         return api_response(success=False, message=str(e), status=500)


# TODO: change the user_id to get it from sessions
@api_blueprint.route("/upload-csv", methods=["POST"])
def upload_csv():
    if "files[]" not in request.files:
        return api_response(success=False, message="No file part", status=400)

    files = request.files.getlist("files[]")
    if not files:
        return api_response(success=False, message="No selected files", status=400)

    # TODO: replace this with user_id from sessions
    # user_id = session.get("user_id")
    user_id = request.form.get("user_id")
    if not user_id:
        return api_response(success=False, message="User ID required", status=400)

    # Use CSVUploader to save uploaded files
    try:
        csv_uploader = get_csv_uploader()
        success, message = csv_uploader.save_uploaded_files(files, user_id)
        if success:
            return api_response(
                success=True, message="Files uploaded successfully", status=200
            )
        else:
            return api_response(
                success=False,
                message=f"Failed to upload files with message {message}",
                status=500,
            )
    except Exception as e:
        print(f"Error uploading files: {e}")
        return api_response(success=False, message=str(e), status=500)


# API to get nearby attractions
@api_blueprint.route("/nearby-attractions", methods=["GET"])
def get_nearby_attractions():
    data = request.get_json()
    user_location = data.get("location")  # e.g., "37.7749,-122.4194"
    radius = data.get("radius", 5000)  # default radius in meters

    response = maps.get_nearby_attractions(user_location, radius)

    if response.status_code == 200:
        return api_response(
            success=True,
            message="Nearby attractions fetched successfully",
            data=response.json(),
            status=200,
        )
    else:
        return api_response(
            success=False,
            message="Failed to fetch nearby attractions",
            status=response.status_code,
        )


# API to get nearby restaurants
@api_blueprint.route("/nearby-restaurants", methods=["GET"])
def get_nearby_restaurants():
    user_location = request.args.get("location")  # e.g., "37.7749,-122.4194"
    radius = request.args.get("radius", 5000)  # default radius in meters

    response = maps.get_nearby_restaurants(user_location, radius)

    if response.status_code == 200:
        return api_response(
            success=True,
            message="Nearby restaurants fetched successfully",
            data=response.json(),
            status=200,
        )
    else:
        return api_response(
            success=False,
            message="Failed to fetch nearby restaurants",
            status=response.status_code,
        )


# API to get place details
@api_blueprint.route("/place-details", methods=["GET"])
def get_place_details():
    place_id = request.args.get("place_id")

    response = maps.get_place_details(place_id)

    if response.status_code == 200:
        return api_response(
            success=True,
            message="Place details fetched successfully",
            data=response.json(),
            status=200,
        )
    else:
        return api_response(
            success=False,
            message="Failed to fetch place details",
            status=response.status_code,
        )
