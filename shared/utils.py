from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def success_response(data: Any, message: str = "Success", status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({
            "success": True,
            "message": message,
            "data": data
        })
    )

def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None):
    body = {
        "success": False,
        "error": {
            "code": error_code or "UNKNOWN",
            "message": message
        }
    }
    return JSONResponse(status_code=status_code, content=body)