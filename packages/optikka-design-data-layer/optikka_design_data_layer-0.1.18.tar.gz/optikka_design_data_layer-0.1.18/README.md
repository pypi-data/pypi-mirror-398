# optikka-design-data-layer

Shared design data layer utilities for Optikka microservices running on AWS Lambda.

This package provides AWS service clients, database connections, validators, and utilities for Lambda functions in the design-data-microservices ecosystem.

## Installation

```bash
pip install optikka-design-data-layer
```

## Usage

### Database Clients

```python
from optikka_design_data_layer.clients import mongodb_client, postgres_client

# MongoDB operations
template = mongodb_client.get_template_registry_by_id("template-123")

# PostgreSQL operations
result = postgres_client.execute_query("SELECT * FROM images WHERE id = %s", ("image-123",))
```

### AWS Services

```python
from optikka_design_data_layer.aws import (
    upload_script_to_s3,
    SecretsManager,
    BedrockClient,
    OpenAIClient,
)

# S3 operations
s3_location = upload_script_to_s3("my-script-content", "script.js")

# Secrets Manager
secrets = SecretsManager()
api_key = secrets.get_secret("my-secret-arn")

# AI clients
bedrock = BedrockClient()
openai = OpenAIClient()
```

### Validation

```python
from optikka_design_data_layer.validation import (
    validate_auth_from_event,
    TemplateInputValidator,
)
from ods_models import TemplateInput, TemplateRegistry

# Auth validation
if validate_auth_from_event(event, secret_name):
    # Process authenticated request
    pass

# Template input validation
validator = TemplateInputValidator()
is_valid, errors = validator.validate(template_input, template_registry)
```

### Utilities

```python
from optikka_design_data_layer.utils import (
    create_success_response,
    create_error_response,
    get_all_guide_data_by_image,
)

# Lambda response utilities
return create_success_response(data={"message": "Success"})
return create_error_response(500, "Internal server error")

# Asset data utilities
guides = get_all_guide_data_by_image(images)
```

### Configuration and Logging

```python
from optikka_design_data_layer import logger, EnvironmentVariables

# Logging (AWS Lambda Powertools)
logger.info("Processing request")
logger.error("Error occurred", exc_info=True)

# Environment variables
db_name = EnvironmentVariables.MONGODB_DATABASE_NAME
bucket = EnvironmentVariables.S3_BUCKET_PREFIX
```

## Package Structure

```
optikka_design_data_layer/
├── clients/           # Database clients
│   ├── mongo_client.py
│   ├── postgres_client.py
│   ├── postgres_credential_manager.py
│   └── mongodb_guide_client.py
├── aws/               # AWS service clients
│   ├── s3_utils.py
│   ├── secrets_manager.py
│   ├── bedrock_client.py
│   └── openai_client.py
├── validation/        # Validators
│   ├── validate_auth.py
│   └── validate_template_input_object.py
├── utils/             # Utilities
│   ├── response_utils.py
│   └── get_asset_data_by_image.py
├── logger.py          # AWS Lambda Powertools logger
├── config.py          # Environment variables
├── errors.py          # Custom exceptions
└── connection_types.py # Connection types
```

## Dependencies

- **ods-models-py**: Pydantic data models
- **boto3**: AWS SDK for Python
- **pymongo**: MongoDB driver
- **psycopg2-binary**: PostgreSQL adapter
- **aws-lambda-powertools**: AWS Lambda utilities
- **pydantic**: Data validation
- **openai**: OpenAI client
- And more...

## Migration from Lambda Layer

### Old (Lambda layer imports)

```python
from logger import logger  # pylint: disable=import-error
from models import TemplateRegistry  # pylint: disable=import-error
from mongo_client import mongodb_client  # pylint: disable=import-error
```

### New (pip package imports)

```python
from optikka_design_data_layer import logger
from ods_models import TemplateRegistry
from optikka_design_data_layer.clients import mongodb_client
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

## Related Packages

- `ods-types-py` - Core types and enums
- `ods-models-py` - Pydantic data models

## License

PROPRIETARY - Optikka
