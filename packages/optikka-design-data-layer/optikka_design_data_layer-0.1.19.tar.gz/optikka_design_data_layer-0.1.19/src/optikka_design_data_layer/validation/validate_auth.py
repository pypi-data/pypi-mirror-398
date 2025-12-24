"""
Validate auth from event.
"""
import json
import base64
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from optikka_design_data_layer.logger import logger
from optikka_design_data_layer.errors import AuthValidationError

class SecretManagerClient: # pylint: disable=too-few-public-methods
    """Client for interacting with AWS Secret Manager"""

    def __init__(self):
        """
        Initialize the Secret Manager client
        
        Args:
            region_name: AWS region name. If None, uses default region.
        """
        try:
            self.client = boto3.client('secretsmanager')
        except NoCredentialsError as e:
            logger.error("AWS credentials not found")
            raise AuthValidationError("AWS credentials not configured") from e
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error(f"Failed to initialize Secret Manager client: {str(e)}")
            raise AuthValidationError(
                f"Failed to initialize Secret Manager client: {str(e)}"
            ) from e

    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret from AWS Secret Manager
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            The secret value as a string
            
        Raises:
            AuthValidationError: If secret retrieval fails
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)

            if 'SecretString' in response:
                return response['SecretString']
            return base64.b64decode(response['SecretBinary']).decode('utf-8')

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DecryptionFailureException':
                logger.error(f"Secret {secret_name} could not be decrypted")
                raise AuthValidationError(f"Secret {secret_name} could not be decrypted") from e
            if error_code == 'InternalServiceErrorException':
                logger.error(f"Internal service error for secret {secret_name}")
                raise AuthValidationError(f"Internal service error for secret {secret_name}") from e
            if error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_name}")
                raise AuthValidationError(f"Invalid parameter for secret {secret_name}") from e
            if error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_name}")
                raise AuthValidationError(f"Invalid request for secret {secret_name}") from e
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret {secret_name} not found")
                raise AuthValidationError(f"Secret {secret_name} not found") from e
            logger.error(f"Unexpected error retrieving secret {secret_name}: {str(e)}")
            raise AuthValidationError(
                f"Unexpected error retrieving secret {secret_name}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
            raise AuthValidationError(f"Failed to retrieve secret {secret_name}: {str(e)}") from e

class AuthValidator:
    """Validator for authentication headers using AWS Secret Manager"""

    def __init__(self, secret_name: str, header_key: str = "Authorization"):
        """
        Initialize the auth validator
        
        Args:
            secret_name: Name of the secret in AWS Secret Manager containing the expected auth value
            header_key: Name of the header to validate (default: "Authorization")
            region_name: AWS region name. If None, uses default region.
        """
        self.secret_name = secret_name
        self.header_key = header_key
        self.secret_manager = SecretManagerClient()
        self._expected_auth_value = None

    def _get_expected_auth_value(self) -> str:
        """
        Get the expected auth value from Secret Manager (cached)
        
        Returns:
            The expected auth value
            
        Raises:
            AuthValidationError: If secret retrieval fails
        """
        if self._expected_auth_value is None:
            try:
                secret_value = self.secret_manager.get_secret(self.secret_name)
                # Parse JSON if the secret is stored as JSON
                try:
                    secret_data = json.loads(secret_value)
                    if isinstance(secret_data, dict) and 'optiform_api_key' in secret_data:
                        self._expected_auth_value = secret_data['optiform_api_key']
                    else:
                        self._expected_auth_value = secret_value
                except json.JSONDecodeError:
                    # If not JSON, use the raw value
                    self._expected_auth_value = secret_value

                logger.info(f"Successfully retrieved auth value from secret {self.secret_name}")
            except Exception as e:
                logger.error(f"Failed to get expected auth value: {str(e)}")
                raise AuthValidationError(f"Failed to get expected auth value: {str(e)}") from e

        return self._expected_auth_value

    def validate_auth_header(self, event: Dict[str, Any]) -> bool:
        """
        Validate that the auth header exists and matches the expected value
        
        Args:
            event: Lambda event payload
            
        Returns:
            True if auth header is valid, False otherwise
            
        Raises:
            AuthValidationError: If validation fails due to configuration issues
        """
        try:
            # Extract headers from the event
            headers = self._extract_headers(event)
            if not headers:
                logger.warning("No headers found in event")
                return False

            # Check if the required header exists
            if self.header_key.lower() not in [key.lower() for key in headers.keys()]:
                logger.warning(f"Required header '{self.header_key}' not found in event")
                return False

            headers_lower = {key.lower(): value for key, value in headers.items()}
            # Get the actual auth value from the event
            actual_auth_value = headers_lower[self.header_key.lower()]
            actual_auth_value = actual_auth_value.replace("Bearer ", "")
            # Get the expected auth value from Secret Manager
            expected_auth_value = self._get_expected_auth_value()    
            # Compare the values
            if actual_auth_value == expected_auth_value:
                logger.info("Auth header validation successful")
                return True
            else:
                logger.warning("Auth header value does not match expected value")
                return False

        except AuthValidationError as e:
            # Re-raise AuthValidationError as-is
            raise AuthValidationError(f"Auth validation error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error during auth validation: {str(e)}")
            raise AuthValidationError(f"Unexpected error during auth validation: {str(e)}") from e

    def _extract_headers(self, event: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract headers from Lambda event
        
        Args:
            event: Lambda event payload
            
        Returns:
            Dictionary of headers
        """
        headers = {}

        # Handle API Gateway events
        if 'headers' in event:
            headers = event['headers']
        elif 'requestContext' in event and 'http' in event.get('requestContext', {}):
            # API Gateway v2 format
            headers = event.get('headers', {})
        elif 'Records' in event:
            # SQS/SNS events might have headers in a different format
            # This is a simplified version - adjust based on your specific event structure
            headers = {}

        # Convert header keys to lowercase for case-insensitive comparison
        return {k.lower(): v for k, v in headers.items()}

    def get_auth_header_value(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Get the auth header value from the event
        
        Args:
            event: Lambda event payload
            
        Returns:
            The auth header value if present, None otherwise
        """
        headers = self._extract_headers(event)
        return headers.get(self.header_key.lower())

def validate_auth_from_event(
        event: Dict[str, Any],
        secret_name: str,
        header_key: str = "Authorization",
    ) -> bool:
    """
    Convenience function to validate auth header from Lambda event
    
    Args:
        event: Lambda event payload
        secret_name: Name of the secret in AWS Secret Manager
        header_key: Name of the header to validate (default: "Authorization")        
    Returns:
        True if auth header is valid, False otherwise
        
    Raises:
        AuthValidationError: If validation fails due to configuration issues
    """
    validator = AuthValidator(secret_name, header_key)
    return validator.validate_auth_header(event)
