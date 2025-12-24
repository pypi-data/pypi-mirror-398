import os
from collections import namedtuple

EnvironmentVariableConfig = namedtuple("EnvironmentVariableConfig", ["cast", "default_value"])

SpecConfig = namedtuple("SpecConfig", ["vCPUs", "RAM"])


class EnvironmentVariablesImpl:
    REGISTRY = {
        "MONGODB_URI": EnvironmentVariableConfig(cast=str, default_value=None),
        "MONGODB_DATABASE_NAME": EnvironmentVariableConfig(cast=str, default_value="optiform"),
        "MONGODB_CA_DATABASE_NAME": EnvironmentVariableConfig(cast=str, default_value="consumption-app"),
        "MONGODB_USERNAME": EnvironmentVariableConfig(cast=str, default_value=None),
        "MONGODB_PASSWORD": EnvironmentVariableConfig(cast=str, default_value=None),
        "MONGODB_PORT": EnvironmentVariableConfig(cast=str, default_value="27017"),
        "CA_BUNDLE_PATH": EnvironmentVariableConfig(cast=str, default_value=None),
        "API_KEY_SECRET_NAME": EnvironmentVariableConfig(cast=str, default_value=None),
        "MONGODB_CA_BUNDLE_URL": EnvironmentVariableConfig(cast=str, default_value=None),
        "MONGODB_GUIDES_DATABASE": EnvironmentVariableConfig(cast=str, default_value="consumption-app"),
        "TEMPLATE_REGISTRY_COLLECTION_NAME": EnvironmentVariableConfig(
            cast=str, default_value="template_registry"
        ),
        "TEMPLATE_INPUTS_COLLECTION_NAME": EnvironmentVariableConfig(
            cast=str, default_value="template_inputs"
        ),
        "LOG_LEVEL": EnvironmentVariableConfig(cast=str, default_value="INFO"),
        "HTTP_API_ENDPOINT_URL": EnvironmentVariableConfig(cast=str, default_value=None),
        "S3_BUCKET_PREFIX": EnvironmentVariableConfig(cast=str, default_value=None),
        "SQS_QUEUE_URL": EnvironmentVariableConfig(cast=str, default_value=None),
        "POSTGRES_WRITER_QUEUE_URL": EnvironmentVariableConfig(cast=str, default_value=None),
        "RENDER_RUN_COLLECTION_NAME": EnvironmentVariableConfig(cast=str, default_value="render_runs"),
        "TEMPLATE_INPUT_JOB_COLLECTION_NAME": EnvironmentVariableConfig(cast=str, default_value="template_input_job"),
        "BRAND_REGISTRY_COLLECTION_NAME": EnvironmentVariableConfig(cast=str, default_value="brand_registry"),
        "BRANDS_COLLECTION_NAME": EnvironmentVariableConfig(cast=str, default_value="brands"),
        # OpenAI
        "OPENAI_API_KEY_SECRET_ARN": EnvironmentVariableConfig(cast=str, default_value=None),
        "POSTGRES_SSL_MODE": EnvironmentVariableConfig(cast=str, default_value=None),
        "POSTGRES_SECRET_ARN": EnvironmentVariableConfig(cast=str, default_value=None),
        "POSTGRES_PORT": EnvironmentVariableConfig(cast=str, default_value=None),
        "POSTGRES_PROXY_HOST": EnvironmentVariableConfig(cast=str, default_value=None),
        "POSTGRES_DB_NAME": EnvironmentVariableConfig(cast=str, default_value=None),
        "MAX_CONNECTION_AGE": EnvironmentVariableConfig(cast=str, default_value="3600"),
        "AWS_PRESIGNED_URL_EXPIRATION_TIME": EnvironmentVariableConfig(cast=int, default_value=3600),
        "CLOUDFRONT_DOMAIN": EnvironmentVariableConfig(cast=str, default_value=None),
        "CLOUDFRONT_KEY_PAIR_ID": EnvironmentVariableConfig(cast=str, default_value=None),
        "CLOUDFRONT_SECRET_ARN": EnvironmentVariableConfig(cast=str, default_value=None),
    }

    def __getattr__(self, key: str):
        """Retrieve environment variable value with type casting and default fallback.
        Args:
            key: Environment variable name.
        Returns:
            Typed environment variable value.
        Raises:
            KeyError: If environment variable is not defined in registry.
        """
        if key not in self.REGISTRY:
            raise KeyError(f"Environment variable [{key}] not defined in registry.")

        variable_config = self.REGISTRY[key]
        result = os.environ.get(key)

        if (result is None) or (not result):
            return variable_config.default_value

        if variable_config.cast is not None:
            return variable_config.cast(result)

        return result


EnvironmentVariables = EnvironmentVariablesImpl()
