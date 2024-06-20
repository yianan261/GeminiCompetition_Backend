"""Write all the APIs here"""

import os
from flask import Blueprint
from helpers import api_response

api_blueprint = Blueprint('api_blueprint', __name__)

@api_blueprint.route('/', methods=["GET"])
def healthcheck():
    return api_response(success=True, message="App is alive", data={"message": "App is alive"}, status=200)


@api_blueprint.route('/test-hello-world', methods=["POST"])
def test_hello():
    return api_response(success=True, message="successful", data={"hello": "world"}, status=200)