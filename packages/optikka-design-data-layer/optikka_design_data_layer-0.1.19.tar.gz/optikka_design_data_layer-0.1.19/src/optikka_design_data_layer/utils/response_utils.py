"""
Response utils for the application.
"""

import json
from typing import Dict, Any, Optional, List
from pydantic import ValidationError
from optikka_design_data_layer.errors import S3UploadError, MongoDBUpsertError, AuthValidationError

# CORS headers for all API responses
_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
}

def create_error_response(
    status_code: int,
    message: str,
    error: Optional[Exception] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message to return
        error: Optional exception for logging
        
    Returns:
        Dictionary with statusCode, headers, and body
    """
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS.copy(),
        "body": json.dumps({
            "message": message,
            "error": str(error)
        })
    }

def create_custom_error_response(status_code: int, message: str, error: Optional[Exception] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a customized error response.
    """
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS.copy(),
        "body": json.dumps({
            "message": message,
            "error": str(error),
            "data": data if data is not None else {}
        })
    }


def create_success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Data to include in the response body
        status_code: HTTP status code (default: 200)
        
    Returns:
        Dictionary with statusCode, headers, and body
    """
    return {
        "statusCode": status_code,
        "headers": _CORS_HEADERS.copy(),
        "body": json.dumps(data)
    }


def handle_validation_error(error: ValidationError, context: str = "") -> Dict[str, Any]:
    """
    Handle ValidationError and return appropriate response.
    
    Args:
        error: The ValidationError exception
        context: Optional context for logging
        
    Returns:
        Error response dictionary
    """
    return create_error_response(400, "Invalid event", error)


def handle_s3_upload_error(error: S3UploadError, context: str = "") -> Dict[str, Any]:
    """
    Handle S3UploadError and return appropriate response.
    
    Args:
        error: The S3UploadError exception
        context: Optional context for logging
        
    Returns:
        Error response dictionary
    """
    return create_error_response(500, "Error handling ODS script upload to s3.", error)


def handle_mongodb_upsert_error(error: MongoDBUpsertError, context: str = "") -> Dict[str, Any]:
    """
    Handle MongoDBUpsertError and return appropriate response.
    
    Args:
        error: The MongoDBUpsertError exception
        context: Optional context for logging
        
    Returns:
        Error response dictionary
    """
    return create_error_response(500, "Error handling ODS script object creation in MongoDB.", error)


def handle_generic_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    Handle generic exceptions and return appropriate response.
    
    Args:
        error: The exception
        context: Optional context for logging
        
    Returns:
        Error response dictionary
    """
    return create_error_response(500, "Unknown error handling API event.", error)

def create_auth_error_response(error: AuthValidationError, message: str) -> Dict[str, Any]:
    """
    Create a standardized auth error response.
    """
    return create_error_response(401, message, error)

def create_not_found_response() -> Dict[str, Any]:
    """
    Create a standardized not found response.
    
    Returns:
        Error response dictionary
    """
    return create_error_response(404, "Event type not found", None)
