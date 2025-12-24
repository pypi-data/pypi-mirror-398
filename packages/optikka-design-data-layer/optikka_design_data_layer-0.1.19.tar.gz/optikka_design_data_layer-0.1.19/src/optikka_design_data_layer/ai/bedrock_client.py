"""AWS Bedrock client"""

import json
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from optikka_design_data_layer import logger


class BedrockClient:
    """Client for AWS Bedrock Runtime operations."""

    CONFIG = Config(
        retries={"max_attempts": 3, "mode": "adaptive"},
        connect_timeout=60,
        read_timeout=300,
    )

    def __init__(self, region_name: str = "us-west-2"):
        self.region_name = region_name
        self.client = boto3.client("bedrock-runtime", region_name=region_name, config=self.CONFIG)
        logger.info(f"Initialized BedrockClient for region: {region_name}")

    def invoke(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Invoke a Bedrock model with the given body."""
        try:
            logger.info(f"Invoking Bedrock model: {model_id}")
            response = self.client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )

            response_body = json.loads(response["body"].read())
            logger.info(f"Successfully invoked model: {model_id}")
            return response_body

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"Bedrock ClientError: {error_code}")
            raise
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {e}")
            raise

    def generate_text_embedding(self, text: str, model_id: str = "amazon.titan-embed-text-v2:0") -> list[float]:
        """
        Generate text embedding using Amazon Titan Embed model.
        
        Args:
            text: Input text to generate embedding for
            model_id: Bedrock model ID (default: amazon.titan-embed-text-v2:0)
            
        Returns:
            List of floats representing the embedding vector (1024 dimensions for v2)
            
        Raises:
            ClientError: If Bedrock API call fails
            ValueError: If response doesn't contain embedding
        """
        try:
            logger.info(f"Generating text embedding for text (length: {len(text)})")
            
            body = {"inputText": text}
            response = self.invoke(model_id=model_id, body=body)
            
            embedding = response.get("embedding")
            if not embedding:
                raise ValueError("No embedding in Bedrock response")
            
            logger.info(f"Generated embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            raise


# Lazy initialization to avoid instantiation on import
_bedrock_instance = None

class _BedrockClientProxy:
    """
    Lazy-loading proxy for BedrockClient singleton.

    The actual BedrockClient instance is only created when first accessed,
    not when the module is imported. This prevents initialization errors in
    Lambda functions that don't use Bedrock.
    """
    def __getattr__(self, name):
        global _bedrock_instance
        if _bedrock_instance is None:
            _bedrock_instance = BedrockClient()
        return getattr(_bedrock_instance, name)

bedrock_client = _BedrockClientProxy()
