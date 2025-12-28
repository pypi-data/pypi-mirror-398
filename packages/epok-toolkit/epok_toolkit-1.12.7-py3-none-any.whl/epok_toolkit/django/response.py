from rest_framework.response import Response
from django.http import HttpResponse
from typing import Optional


STATUS_MESSAGES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
}



def response(data: Optional[dict] = None, status_code: int = 200, message: Optional[str] = None) -> Response:
    success = True if 200 <= status_code < 300 else False

    if status_code not in STATUS_MESSAGES:
        raise ValueError(f"Invalid status code: {status_code}. Must be one of {list(STATUS_MESSAGES.keys())}.")
    
    if status_code == 201 and not data:
        raise ValueError("Data cannot be empty for status code 201 (Created).")
    
    if status_code == 204 and data is not None:
        raise ValueError("Data must be None for status code 204 (No Content).")
    
    if not message:
        message = STATUS_MESSAGES[status_code]

    if not data:
        data = {}
    
    payload = {
        "status": success,
        "message": message
    }
    if success and data is not None:
        payload["data"] = data
    elif not success:
        payload["error"] = data
    return Response(payload, status=status_code)



def file_response(file: bytes, filename: str, content_type: str = "application/octet-stream", status_code: int = 200) -> HttpResponse:
    """
    Returns a file response with the given file content, filename, and content type.
    """
    response = HttpResponse(file, status=status_code)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Content-Type"] = content_type
    return response