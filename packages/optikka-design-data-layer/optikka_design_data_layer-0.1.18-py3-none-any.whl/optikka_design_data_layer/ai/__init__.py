"""
AI service clients for OpenAI and Bedrock.

To avoid initializing all AI clients at import time, import specific clients
from their respective modules:

    from optikka_design_data_layer.ai.openai_client import openai_client
    from optikka_design_data_layer.ai.bedrock_client import bedrock_client
"""

from optikka_design_data_layer.ai.openai_client import OpenAIClient
from optikka_design_data_layer.ai.bedrock_client import BedrockClient

__all__ = [
    "OpenAIClient",
    "BedrockClient",
]
