"""Write all the APIs here"""

import os
from flask import Blueprint, request, jsonify
from helpers import api_response
from data_retriever import DataRetriever
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"csv"}

api_blueprint = Blueprint("api_blueprint", __name__)

data_retriever = DataRetriever()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


@api_blueprint.route("/upload-takeout", methods=["POST"])
def upload_takeout_csv():
    if "files[]" not in request.files:
        return api_response(success=False, message="No file uploaded", status=400)

    files = request.files.getlist["files[]"]
    if not files:
        return api_response(succes=False, message="No selected files", status=400)

    valid_files = [file for file in files if file and allowed_file(file.filename)]
    if not valid_files:
        return api_response(success=False, message="No valid files", status=400)

    # process valid files and save to db
    try:
        saved_places = data_retriever.get_saved_places(valid_files)
        user_id = request.form.get("user_id")
        if not user_id:
            return api_response(success=False,message="User ID required", status=400)
        data_retriever.save_to_firestore(user_id,saved_places)
        return api_response(success=True, message="Files processed and data saved successfully", status=200)
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)

@api_blueprint.route("/get-user-data", methods=["POST"])
def get_user_data():
    data = request.get_json()

