from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/users", methods=["POST"])
def create_user():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        # Simulate writing to a database
        # get_data_retriever().write_to_collection_with_id("users", user_id, data)
        return jsonify(success=True, message="User created", data=data), 201
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route("/updateUser", methods=["POST"])
def update_user():
    try:
        data = request.get_json()
        user_id = request.args.get("user_id")
        # Simulate writing to a database
        # get_data_retriever().write_to_collection_with_id("users", user_id, data)
        return jsonify(success=True, message="User updated", data=data), 200
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True)
