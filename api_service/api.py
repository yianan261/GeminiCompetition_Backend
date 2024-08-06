"""Write all the APIs here"""

import os
from dotenv import load_dotenv
from flask import (
    Blueprint,
    request,
    current_app,
)
from helpers import api_response
from maps import Maps
from schema.users import user_schema
from jsonschema import validate, ValidationError
from datetime import datetime, timezone
import io
from csv_uploader import CSVUploader
from llm_tools import LLMTools

# Load environment variables
load_dotenv()

# Initialize Maps instances
maps = Maps()

# Initialize LLM Tools
llm = LLMTools()

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

@api_blueprint.route("/test-gemini", methods=["POST"])
def test_gemini():
    result = llm.test_api()
    return api_response(
        success=True, message="successful", data={"llm_result": result}, status=200
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
# Pass in email to get user data
@api_blueprint.route("/users/<email>", methods=["GET"])
def get_user(email):
    try:
        data = get_data_retriever().fetch_document_by_id("users", email)
        if data:
            return api_response(
                success=True, message="User retrieved", data=data, status=200
            )
        else:
            return api_response(success=False, message="User not found", status=404)
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

    email = data.get("email")

    try:
        existing_user = get_data_retriever().fetch_document_by_criteria(
            "users", "email", email
        )
        if existing_user:
            return api_response(
                success=False,
                message="User with this email already exists",
                status=409,
            )

        # Add createdAt timestamp
        data["createdAt"] = datetime.now(timezone.utc).isoformat()

        result = get_data_retriever().write_to_collection_with_id("users", email, data)
        if result:
            return api_response(
                success=True,
                message="User created",
                data={"email": email},
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
        email = data.get("email")
        if not email:
            return api_response(success=False, message="Email is required", status=400)

        # Fetch the existing user document
        existing_user = get_data_retriever().fetch_document_by_id("users", email)
        if not existing_user:
            return api_response(success=False, message="User not found", status=404)

        # Merge the existing data with the new data
        updated_data = {**existing_user, **data}

        result = get_data_retriever().write_to_collection_with_id(
            "users", email, updated_data
        )
        if result:
            return api_response(
                success=True, message="User updated", data=updated_data, status=200
            )
        else:
            return api_response(
                success=False, message="Failed to update user", status=500
            )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# Saved Places from Google Takeout
@api_blueprint.route("/saved-places", methods=["GET"])
def get_saved_places():
    try:
        user_email = request.args.get("email")
        data = get_data_retriever().fetch_document_by_criteria(
            "saved_places", "user_email", user_email
        )
        return api_response(
            success=True, message="Saved places retrieved", data=data, status=200
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# users can either upload Google Takeout zip file or Google Takeout folder
@api_blueprint.route("/process-takeout-files", methods=["POST"])
def process_takout_files():
    user_email = request.form.get("email")
    if not user_email:
        return api_response(success=False, message="User email is required", status=400)

    uploaded_files = request.files.getlist("files[]")
    if not uploaded_files:
        return api_response(success=False, message="No files provided", status=400)

    csv_uploader = get_csv_uploader()

    for file in uploaded_files:
        if file.filename.endswith(".zip"):
            file_stream = io.BytesIO(file.read())
            success, message = csv_uploader.process_zip_file(file_stream, user_email)
        else:
            folder_path = f"/tmp/{file.filename}"
            file.save(folder_path)
            success, message = csv_uploader.process_folder(folder_path, user_email)
            os.remove(folder_path)

        if not success:
            return api_response(
                success=False, message=f"Failed to process files: {message}", status=500
            )

    return api_response(success=True, message=f"{message}", status=200)


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


# TODO: need to change user_interests to places that are visitable on the map and apply LLM filter for recommendations
@api_blueprint.route("/getPointOfInterest", methods=["GET"])
def get_point_of_interest():
    data = request.get_json()
    user_email = data.get("email")

    try:
        # Fetch user data using email ID from the database
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        user_location = user_data.get(
            "location", "37.7749,-122.4194"
        )  # Default to San Francisco
        # TODO: need to change this, because interests list may contain non-location items
        user_interests = user_data.get("interests", ["parks", "museums"])

        # Search for points of interest using Google Maps API
        points_of_interest = []
        for interest in user_interests:
            response = maps.search_places_nearby(
                user_location, interest, radius=50 * 1609
            )  # 50 miles in meters
            if response.status_code == 200:
                points_of_interest.extend(response.json().get("results", []))

        # Further filter results using LLM (mocked for this example)
        filtered_points_of_interest = (
            points_of_interest  # Apply actual LLM filtering here
        )

        return api_response(
            success=True,
            message="Points of interest retrieved",
            data=filtered_points_of_interest,
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# TODO: might need to change the query to LLM generated function call?
@api_blueprint.route("/searchPointOfInterest", methods=["POST"])
def search_point_of_interest():
    data = request.get_json()
    user_email = data.get("email")
    query = data.get("query")

    try:
        # Fetch user data from the database
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        user_location = user_data.get(
            "location", "37.7749,-122.4194"
        )  # Default to San Francisco

        # Search for points of interest using the user's query and Google Maps API
        response = maps.search_places_nearby(
            user_location, query, radius=50 * 1609
        )  # 50 miles in meters
        if response.status_code == 200:
            points_of_interest = response.json().get("results", [])

            # Further filter results using LLM (mocked for this example)
            filtered_points_of_interest = (
                points_of_interest  # Apply actual LLM filtering here
            )

            return api_response(
                success=True,
                message="Points of interest retrieved",
                data=filtered_points_of_interest,
                status=200,
            )
        else:
            return api_response(
                success=False,
                message="Failed to search points of interest",
                status=response.status_code,
            )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# When a user clicks the "Save" button on the app. The app will mark that location in a "saved" bookmark
@api_blueprint.route("/save-places-to-visit", methods=["POST"])
def save_places_to_visit():
    data = request.get_json()
    user_email = data.get("email")
    location = data.get("location")

    if not user_email or not location:
        return api_response(
            success=False, message="Email and location are required", status=400
        )

    try:
        # Fetch user data using email ID from the database
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        # Create bookmarked_places field if it does not exist
        if "bookmarked_places" not in user_data:
            user_data["bookmarked_places"] = {}

        # Add the location to the bookmarked_places field
        user_data["bookmarked_places"][location["name"]] = location

        # Update the user's data in the database
        result = get_data_retriever().write_to_collection_with_id(
            "users", user_email, user_data
        )
        if result:
            return api_response(
                success=True, message="Place bookmarked successfully", status=200
            )
        else:
            return api_response(
                success=False, message="Failed to bookmark place", status=500
            )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/get-places-to-visit", methods=["GET"])
def get_places_to_visit():
    user_email = request.args.get("email")

    if not user_email:
        return api_response(success=False, message="Email is required", status=400)

    try:
        # Fetch user data from the database
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        # Retrieve bookmarked places
        bookmarked_places = user_data.get("bookmarked_places", {})
        bookmarked_places_list = [
            {"location": key, **value} for key, value in bookmarked_places.items()
        ]
        return api_response(
            success=True,
            message="Bookmarked places retrieved",
            data=bookmarked_places_list,
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)
