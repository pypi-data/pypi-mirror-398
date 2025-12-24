"""
Optikka Design Data Layer
Shared utilities for Optikka microservices.

This package provides:
- Logger (AWS Lambda Powertools)
- Error classes
- Response utilities
- Auth validation
- Database clients (PostgreSQL, MongoDB)
- AI clients (OpenAI, Bedrock)
- Data helpers and validators
- S3 and Secrets Manager utilities
- Environment configuration

Usage:
    from optikka_design_data_layer import logger
    from optikka_design_data_layer.errors import AuthValidationError
    from optikka_design_data_layer.utils import create_success_response
    from optikka_design_data_layer.validation import validate_auth_from_event
    from optikka_design_data_layer.db.postgres_client import postgres_client
    from optikka_design_data_layer.db.mongo_client import mongodb_client
    from optikka_design_data_layer.ai.openai_client import openai_client
    from optikka_design_data_layer.ai.bedrock_client import bedrock_client
"""

__version__ = "0.1.11"

# Re-export core utilities
from optikka_design_data_layer.logger import logger
from optikka_design_data_layer.errors import (
    S3UploadError,
    MongoDBUpsertError,
    AuthValidationError,
)

__all__ = [
    # Logger
    "logger",
    # Errors
    "S3UploadError",
    "MongoDBUpsertError",
    "AuthValidationError",
]
