from flask import jsonify

def api_response(success=False, data=None, status=200, message=None, error=None):
    """
    Helper function to format API responses.
    :param data: Data to include in the response (default is None)
    :param status: HTTP status code (default is 200)
    :param message: Optional message to include in the response (default is None)
    :param error: Optional array of error objects: [{"field":<field_name>, "message":<message>}]
    :return: JSON response
    """
    response = {
        'success': success,
        'status': status,
        'data': data,
        'message': message,
        'error': error
    }
    return jsonify(response), status