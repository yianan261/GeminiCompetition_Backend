"""Write all the APIs here"""

import os
import sys
from dotenv import load_dotenv
from flask import Blueprint, request
from helpers import api_response
from data_retriever import DataRetriever
from maps import Maps

# Load environment variables
load_dotenv()

# Initialize DataRetriever and Maps instances
data_retriever = DataRetriever()
maps = Maps()

# Create Blueprint
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
            status=200
        )
    else:
        return api_response(
            success=False, 
            message="Failed to fetch nearby attractions", 
            status=response.status_code
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
            status=200
        )
    else:
        return api_response(
            success=False, 
            message="Failed to fetch nearby restaurants", 
            status=response.status_code
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
            status=200
        )
    else:
        return api_response(
            success=False, 
            message="Failed to fetch place details", 
            status=response.status_code
        )