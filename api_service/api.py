"""Write all the APIs here"""

import os
import json
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

# Constants
MILES_TO_METERS = 1609

# Logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Blueprint
api_blueprint = Blueprint("api_blueprint", __name__)


def get_data_retriever():
    return current_app.config["DATA_RETRIEVER"]


def get_csv_uploader():
    return current_app.config["CSV_UPLOADER"]


def get_llm_tools():
    return current_app.config["LLM_TOOLS"]


@api_blueprint.route("/", methods=["POST"])
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
    result = get_llm_tools().test_api()
    return api_response(
        success=True, message="successful", data={"llm_result": result}, status=200
    )


# Fetch document by Collection and Document ID
# Example: http://localhost:5000/api/fetch-document-by-id?document_id=1&collection_name=users
@api_blueprint.route("/fetch-document-by-id", methods=["POST"])
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
@api_blueprint.route("/users/<email>", methods=["POST"])
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

        existing_user = get_data_retriever().fetch_document_by_id("users", email)
        if not existing_user:
            return api_response(success=False, message="User not found", status=404)

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


@api_blueprint.route("/generateUserDescription", methods=["POST"])
def generate_user_description():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return api_response(success=False, message="Email is required", status=400)

        existing_user = get_data_retriever().fetch_document_by_id("users", email)
        if not existing_user:
            return api_response(success=False, message="User not found", status=404)

        gemini_description = get_llm_tools().generate_user_description(email=email)

        updated_data = {**existing_user, "geminiDescription": gemini_description}

        result = get_data_retriever().write_to_collection_with_id(
            "users", email, updated_data
        )
        if result:
            return api_response(
                success=True,
                message="Description generated and saved!",
                data={"geminiDescription": gemini_description},
                status=200,
            )
        else:
            return api_response(
                success=False, message="Failed to generate description", status=500
            )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# Saved Places from Google Takeout
@api_blueprint.route("/saved-places", methods=["POST"])
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
@api_blueprint.route("/nearby-attractions", methods=["POST"])
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
@api_blueprint.route("/nearby-restaurants", methods=["POST"])
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
@api_blueprint.route("/place-details", methods=["POST"])
def get_place_details():
    data = request.get_json()
    email = data.get("email")
    place_id = data.get("placeId")
    document_id = f"{place_id}--{email}"
    latitude = data.get("latitude", "37.7749")
    longitude = data.get("longitude", "-122.4194")
    user_location = f"{latitude},{longitude}"
    try:
        place_data = get_data_retriever().fetch_document_by_id(
            collection_name="place_details", document_id=document_id
        )
        if not place_data:
            place_data = maps.get_place_details(place_id=place_id, origin=user_location)
            place_data = get_llm_tools().process_place_details(
                email=email, place_data=place_data
            )
            get_data_retriever().write_to_collection_with_id(
                collection_name="place_details",
                document_id=document_id,
                data={"email": email, **place_data},
            )
        return api_response(
            success=True,
            message="Place details fetched successfully",
            data=place_data,
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/get-points-of-interest", methods=["POST"])
def get_points_of_interest():
    data = request.get_json()
    user_email = data.get("email")
    latitude = data.get("latitude", "37.7749")
    longitude = data.get("longitude", "-122.4194")
    radius = data.get("radius", 25)
    weather = data.get("weather", "sunny")

    try:
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        logger.info(f"User data: {json.dumps(user_data)}")
        user_location = f"{latitude},{longitude}"
        place_types = get_llm_tools().generate_place_types(email=user_email)
        logger.info(f"User data: {json.dumps(place_types)}")
        # Get places list
        places_result = maps.get_nearby_places(
            location=user_location, radius=radius * MILES_TO_METERS, types=place_types
        )
        logger.info(f"User data: {json.dumps(places_result)}")
        # Call LLM to filter
        filtered_places = get_llm_tools().filter_relevant_places(
            email=user_email, places=places_result, weather=weather
        )
        logger.info(f"User data: {json.dumps(filtered_places)}")
        return api_response(
            success=True,
            message="Points of interest retrieved",
            data=filtered_places,
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/search-points-of-interest", methods=["POST"])
def search_points_of_interest():
    data = request.get_json()
    user_email = data.get("email")
    query = data.get("query")
    latitude = data.get("latitude", "37.7749")
    longitude = data.get("longitude", "-122.4194")
    radius = data.get("radius", 25)
    weather = data.get("weather", "sunny")

    try:
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)
        logger.info(f"User data: {json.dumps(user_data)}")
        query_info = get_llm_tools().parse_query_for_search(query)
        logger.info(f"Query info: {query_info}")
        user_location = f"{latitude},{longitude}"

        if query_info.get("use_text_search"):
            places_result = maps.search_nearby_places(
                query=query_info["text_query"],
                location=user_location,
                radius=radius * MILES_TO_METERS,
            )
            logger.info(f"Search result: {json.dumps(places_result)}")
        else:
            place_types = query_info.get(
                "types", get_llm_tools().generate_place_types(email=user_email)
            )
            logger.info(f"Place types result: {json.dumps(place_types)}")
            places_result = maps.get_nearby_places(
                location=user_location,
                radius=radius * MILES_TO_METERS,
                types=place_types,
            )
            logger.info(f"Nearby result: {json.dumps(places_result)}")

        # Call LLM to filter
        filtered_places = get_llm_tools().filter_relevant_places_based_on_query(
            query=query, email=user_email, places=places_result, weather=weather
        )
        return api_response(
            success=True,
            message="Points of interest retrieved",
            data=filtered_places,
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


# When a user clicks the "Save" button on the app. The app will mark that location in a "saved" bookmark
@api_blueprint.route("/save-places-to-visit", methods=["POST"])
def save_places_to_visit():
    data = request.get_json()
    user_email = data.get("email")
    place_id = data.get("place_id", "")
    place_name = data.get("title", "")
    photo_url = data.get("photo_url", [])
    distance = data.get("distance", [])
    bookmarked = data.get("bookmarked", True)
    visited = data.get("visited", False)

    if not user_email or not (place_id or place_name):
        return api_response(
            success=False,
            message="Email and either place ID or place name are required",
            status=400,
        )

    try:
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        if "bookmarked_places" not in user_data:
            user_data["bookmarked_places"] = {}

        # Use place_id if available, otherwise use place_name as key
        key = place_id if place_id else place_name

        user_data["bookmarked_places"][key] = {
            "place_id": place_id,
            "title": place_name,
            "photo_url": photo_url,
            "distance": distance,
            "bookmarked": bookmarked,
            "visited": visited,
        }

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


@api_blueprint.route("/remove-bookmarked-place", methods=["DELETE"])
def remove_bookmarked_place():
    data = request.get_json()
    user_email = data.get("email")
    place_id = data.get("place_id", "")
    place_name = data.get("name", "")

    if not user_email or not (place_id or place_name):
        return api_response(
            success=False,
            message="Email and either place ID or place name are required",
            status=400,
        )

    try:
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        key = place_id if place_id else place_name

        if (
            "bookmarked_places" not in user_data
            or key not in user_data["bookmarked_places"]
        ):
            return api_response(
                success=False, message="Bookmarked place not found", status=404
            )

        del user_data["bookmarked_places"][key]

        result = get_data_retriever().write_to_collection_with_id(
            "users", user_email, user_data
        )
        if result:
            return api_response(
                success=True,
                message="Place removed from bookmarks successfully",
                status=200,
            )
        else:
            return api_response(
                success=False,
                message="Failed to remove place from bookmarks",
                status=500,
            )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)


@api_blueprint.route("/get-bookmarked-places", methods=["POST"])
def get_bookmarked_places():
    user_email = request.args.get("email")

    if not user_email:
        return api_response(success=False, message="Email is required", status=400)

    try:
        user_data = get_data_retriever().fetch_document_by_id("users", user_email)
        if not user_data:
            return api_response(success=False, message="User not found", status=404)

        bookmarked_places = user_data.get("bookmarked_places", {})
        bookmarked_places_list = [value for key, value in bookmarked_places.items()]
        return api_response(
            success=True,
            message="Bookmarked places retrieved",
            data=bookmarked_places_list,
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)
