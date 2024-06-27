"""Write all the APIs here"""

import os
from flask import Blueprint, request, jsonify
from helpers import api_response
from data_retriever import DataRetriever
from werkzeug.utils import secure_filename

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

api_blueprint = Blueprint("api_blueprint", __name__)

data_retriever = DataRetriever(UPLOAD_DIR)


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
def upload_csv():
    if "file" not in request.files:
        return api_response(success=False, message="No file uploaded", status=400)

    file = request.files["file"]
    if file.filename == "":
        return api_response(succes=False, message="No selected file", status=400)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = data_retriever.save_uploaded_file(file, filename)
        return api_response(
            success=True,
            message="File uploaded successfully",
            data={"file_path": file_path},
            status=200,
        )
    else:
        return api_response(success=False, message="File type not allowed", status=400)


@api_blueprint.route("/get-user-data", methods=["POST"])
def get_user_data():
    data = request.get_json()
    file_path = data.get("file_path")
    user_id = data.get("user_id")

    if not file_path or not user_id:
        return api_response(
            success=False, message="File path and user ID are required.", status=400
        )

    try:
        saved_places = data_retriever.get_saved_places(file_path)
        data_retriever.save_to_firestore(user_id, saved_places)
        return api_response(
            success=True,
            message="Data retrieved and saved successfully",
            data={"saved_places": saved_places},
            status=200,
        )
    except Exception as e:
        return api_response(success=False, message=str(e), status=500)
