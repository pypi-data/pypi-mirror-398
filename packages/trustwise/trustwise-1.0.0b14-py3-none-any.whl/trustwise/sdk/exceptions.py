class TrustwiseSDKError(Exception):
    """Base exception for all Trustwise SDK errors."""
    pass

class TrustwiseValidationError(TrustwiseSDKError):
    """Exception for validation errors in Trustwise SDK."""
    pass 

class TrustwiseAPIError(TrustwiseSDKError):
    def __init__(self, message: str, response: object, status_code: int) -> None:
        super().__init__(message)
        self.response = response
        self.status_code = status_code

def make_status_error_from_response(response: object) -> "TrustwiseAPIError":
    """
    Create a TrustwiseAPIError from a requests.Response
    """
    try:
        err_text = response.text.strip()
        body = err_text
        try:
            body = response.json()
            err_msg = f"Error code: {response.status_code} - {body}"
        except ValueError:
            err_msg = err_text or f"Error code: {response.status_code}"
    except AttributeError:
        body = None
        err_msg = f"Error code: {response.status_code}"
    return TrustwiseAPIError(err_msg, body, response.status_code)
