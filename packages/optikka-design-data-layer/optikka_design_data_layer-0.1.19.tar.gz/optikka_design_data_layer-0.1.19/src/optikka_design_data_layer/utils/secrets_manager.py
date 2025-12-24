"""
AWS Secrets Manager helpers.
"""

import json
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from optikka_design_data_layer import logger


class SecretsManager:
    """
    Thin wrapper around boto3 Secrets Manager client.
    """

    def __init__(self, secrets_client: Optional[object] = None) -> None:
        self._client = secrets_client or boto3.client("secretsmanager")

    def get_secret_string(self, secret_arn: str) -> str:
        """Retrieve a secret's SecretString from AWS Secrets Manager."""
        try:
            response = self._client.get_secret_value(SecretId=secret_arn)
            secret_string = response.get("SecretString")
            if not secret_string:
                raise RuntimeError("SecretString not found in Secrets Manager response")
            return secret_string
        except ClientError as e:
            logger.error(f"Failed to retrieve secret '{secret_arn}': {e}")
            raise RuntimeError(
                f"Failed to retrieve secret '{secret_arn}': {str(e)}"
            ) from e

    def get_openai_api_key(self, secret_arn: str) -> str:
        """Fetch and parse an OpenAI API key from a given secret."""
        secret_string = self.get_secret_string(secret_arn)
        return self._extract_api_key_from_secret_string(secret_string)

    def _extract_api_key_from_secret_string(self, secret_string: str) -> str:
        """
        Extract OpenAI API key from SecretString.
        """
        try:
            data = json.loads(secret_string)
            if isinstance(data, dict):
                value = data.get("api_key")
                if isinstance(value, str) and value.strip():
                    return value.strip()
                raise ValueError("Secret JSON must contain non-empty 'api_key'")
        except json.JSONDecodeError:
            pass

        raw = secret_string.strip()
        if not raw:
            raise ValueError("Secret string is empty")
        return raw
