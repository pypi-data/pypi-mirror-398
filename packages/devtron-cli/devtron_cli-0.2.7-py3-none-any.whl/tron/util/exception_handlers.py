import json
import requests
from functools import wraps

EXCEPTION_HANDLERS = {
    requests.exceptions.ConnectionError: "Network connection error: Unable to connect. Please check the URL and your network.",
    requests.exceptions.Timeout: "Request timed out: The server did not respond in time.",
    json.JSONDecodeError: "JSON decode error: Failed to parse the server response. The API might be down or returning invalid data.",
    KeyError: "Key error: The API response is missing an expected key.",
    TypeError: "Type error: The data structure from the API was not as expected.",
}

def handle_api_exceptions(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_message = f"HTTP error occurred: {status_code} {e.response.reason}."
            print(error_message)
            return {"success": False, "error": error_message}

        except Exception as e:
            error_message = EXCEPTION_HANDLERS.get(type(e))

            if error_message:
                formatted_error = f"{error_message} Details: {e}"
            else:
                formatted_error = f"An unexpected error occurred: {e.__class__.__name__}: {e}"
            print(formatted_error)
            return {"success": False, "error": formatted_error}

    return wrapper