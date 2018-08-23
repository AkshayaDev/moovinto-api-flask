from flask import jsonify, make_response

# MoovInto Custom Error Codes
moovinto_error_codes = {
    "MOOV_ERR_01": "Bad request",
    "MOOV_ERR_02": "Bad request method",
    "MOOV_ERR_03": "Missing API key",
    "MOOV_ERR_04": "Your API key is invalid",
    "MOOV_ERR_05": "Invalid email format",
    "MOOV_ERR_06": "User already exists",
    "MOOV_ERR_07": "Passwords not matched",
    "MOOV_ERR_08": "Field cannot be empty",
    "MOOV_ERR_09": "Invalid Credential",
    "MOOV_ERR_10": "Not Authorized",
    "MOOV_ERR_11": "Not Found",
}

def success_response(data):
    success_data = {
        "payload": data,
        "status_code": 200,
        "success": "true",
        "error": {}
    }
    return make_response(jsonify(success_data), 200)


def error_response(error_code,error_message):
    error_data = {
        "payload": {},
        "status_code": 00,
        "success": "false",
        "error": {
            "moovinto_error_code": error_code,
            "moovinto_error_message": error_message
        }
    }
    return make_response(jsonify(error_data), 200)