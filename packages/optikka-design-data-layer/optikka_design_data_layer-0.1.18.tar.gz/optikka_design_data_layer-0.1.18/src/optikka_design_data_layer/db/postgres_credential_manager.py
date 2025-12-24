"""
PostgreSQL credential management using AWS Secrets Manager.

This module handles credential retrieval following the single responsibility principle,
separated from connection management for better testability and maintainability.
"""

import json
import boto3
from optikka_design_data_layer import logger
from optikka_design_data_layer.db.connection_types import PostgresCredentials


class PostgresCredentialManager:
    """
    Handle PostgreSQL credential retrieval from AWS Secrets Manager.

    Separated from connection management for single responsibility principle.
    Provides clean abstraction for credential retrieval with proper error handling.
    """

    def __init__(self, secrets_client=None):
        """
        Initialize credential manager with optional secrets client injection.

        Args:
            secrets_client: Optional boto3 secrets manager client for testing
        """
        self._secrets_client = secrets_client or boto3.client("secretsmanager")

    def get_credentials(self, secrets_arn: str) -> PostgresCredentials:
        """
        Retrieve PostgreSQL credentials from AWS Secrets Manager.

        Args:
            secrets_arn: ARN of the secret containing credentials

        Returns:
            PostgresCredentials with username and password

        Raises:
            CredentialRetrievalError: If credentials cannot be retrieved
        """
        try:
            logger.info("Retrieving PostgreSQL credentials from Secrets Manager")
            response = self._secrets_client.get_secret_value(SecretId=secrets_arn)
            secret_data = json.loads(response["SecretString"])

            # Validate required fields are present
            if "username" not in secret_data or "password" not in secret_data:
                raise CredentialRetrievalError("Secret must contain 'username' and 'password' fields")

            credentials = PostgresCredentials(username=secret_data["username"], password=secret_data["password"])

            logger.info("PostgreSQL credentials retrieved successfully")
            return credentials

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret JSON: {e}")
            raise CredentialRetrievalError(f"Invalid JSON in secret: {str(e)}")

        except KeyError as e:
            logger.error(f"Missing required field in secret: {e}")
            raise CredentialRetrievalError(f"Missing required field: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to retrieve PostgreSQL credentials: {e}")
            raise CredentialRetrievalError(f"Cannot retrieve credentials: {str(e)}")


class CredentialRetrievalError(Exception):
    """
    Raised when credentials cannot be retrieved from AWS Secrets Manager.

    Specific exception type for credential-related failures, allowing
    calling code to handle credential issues separately from other errors.
    """

    pass
