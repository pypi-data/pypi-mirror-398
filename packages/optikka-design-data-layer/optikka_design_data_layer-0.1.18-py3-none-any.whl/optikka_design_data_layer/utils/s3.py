"""
S3 utils.
"""

import os
import json
import uuid
import csv
import io
import time
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from optikka_design_data_layer import logger # pylint: disable=relative-beyond-top-level, import-error, no-name-in-module
from optikka_design_data_layer.utils.config import EnvironmentVariables # pylint: disable=relative-beyond-top-level, import-error, no-name-in-module

# S3 and Secrets Manager clients
s3_client = boto3.client("s3")
secrets_client = boto3.client("secretsmanager")

# CloudFront private key caching
_cached_private_key: Optional[str] = None
_last_fetch_time = 0
_CACHE_DURATION = 5 * 60 * 1000  # 5 minutes in milliseconds

def _generate_s3_location(render_run_name: str, file_name: str = None) -> dict[str, str]:
    """Generate a S3 location."""
    logger.debug(f"Generating S3 location for render run name: {render_run_name}")
    uuid_str = str(uuid.uuid4())
    bucket = os.getenv('RENDER_RUN_S3_BUCKET_NAME')
    logger.debug(f"Bucket: {bucket}")
    logger.debug(f"Key: {f'/render-run-csvs/{render_run_name}/{uuid_str}'}")
    return {
        'bucket': bucket,
        'key': f'render-run-csvs/{render_run_name}/{uuid_str}/{file_name}'
    }

def generate_s3_location_for_script(template_registry_id: str) -> dict[str, str]:
    """Generate a S3 location for a script."""
    logger.debug(f"Generating S3 location for script name: {template_registry_id}")
    return {
        'bucket': os.getenv('SCRIPT_S3_BUCKET_NAME'),
        'key': f'ods_scripts/{template_registry_id}.json'
    }
def generate_presigned_upload_url(
        render_run_name: str,
        expiration: int = 3600,
        file_name: str = None
    ) -> tuple[str, dict[str, str]]:
    """Generate a presigned URL for S3 object."""
    try:
        s3_location = _generate_s3_location(render_run_name, file_name)
        logger.debug(f"Generating presigned URL for S3 location: {s3_location}")
        s3_client = boto3.client('s3')
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': s3_location['bucket'], 'Key': s3_location['key']},
            ExpiresIn=expiration
        )
        logger.debug(f"Presigned URL: {url}")
        return url, s3_location
    except ClientError as e:
        logger.debug(f"Failed to generate presigned URL: {str(e)}")
        raise RuntimeError(f"Failed to generate presigned URL: {str(e)}") from e
    except NoCredentialsError as exc:
        logger.debug(f"AWS credentials not found: {str(exc)}")
        raise RuntimeError("AWS credentials not found") from exc
    except Exception as e:
        logger.debug(f"Failed to generate presigned URL: {str(e)}")
        raise RuntimeError(f"Failed to generate presigned URL: {str(e)}") from e


def download_csv_from_s3(bucket: str, key: str) -> bytes:
    """Download CSV file from S3."""
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=bucket, Key=key)
        response_body = response['Body'].read()
        return response_body
    except ClientError as e:
        raise RuntimeError(f"Failed to download object: {str(e)}") from e
    except NoCredentialsError as exc:
        raise RuntimeError("AWS credentials not found") from exc


def parse_csv_to_json(csv_data: bytes) -> list[dict]:
    """Parse CSV data into JSON format."""
    try:
        # Decode bytes to string
        csv_string = csv_data.decode('utf-8')

        # Create a StringIO object to read the CSV
        csv_io = io.StringIO(csv_string)

        # Read CSV and convert to list of dictionaries
        reader = csv.DictReader(csv_io)
        json_data = list(reader)

        return json_data
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode CSV data: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"Failed to parse CSV data: {str(e)}") from e


def download_and_parse_csv_from_s3(bucket: str, key: str) -> list[dict]:
    """Download CSV file from S3 and parse it into JSON format."""
    csv_data = download_csv_from_s3(bucket, key)
    logger.debug(f"CSV data: {csv_data}")
    return parse_csv_to_json(csv_data)


def download_csv_from_location(location_json: str) -> bytes:
    """Download CSV file from S3 location specified in JSON format: {"bucket": "x", "key": "y"}."""
    try:
        location = json.loads(location_json) if isinstance(location_json, str) else location_json

        if not isinstance(location, dict) or 'bucket' not in location or 'key' not in location:
            raise ValueError("Invalid S3 location format. Expected {'bucket': 'x', 'key': 'y'}")

        return download_csv_from_s3(location['bucket'], location['key'])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}") from e

def upload_script_to_s3(script: str, s3_location: dict[str, str]) -> None:
    """Upload a script to S3."""
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(Bucket=s3_location['bucket'], Key=s3_location['key'], Body=script)
    except ClientError as e:
        raise RuntimeError(f"Failed to upload script to S3: {str(e)}") from e
    except NoCredentialsError as exc:
        raise RuntimeError("AWS credentials not found") from exc

def download_script_from_s3(s3_location: dict[str, str]) -> str:
    """Download a script from S3."""
    try:
        s3_client_local = boto3.client('s3')
        if s3_location['bucket'] is None or s3_location['key'] is None:
            raise ValueError("S3 location is invalid")
        response = s3_client_local.get_object(Bucket=s3_location['bucket'], Key=s3_location['key'])
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        raise RuntimeError(f"Failed to download script from S3: {str(e)}") from e
    except NoCredentialsError as exc:
        raise RuntimeError("AWS credentials not found") from exc


# ============================================================================
# Presigned URL Generation with CloudFront Support
# ============================================================================

def rsa_signer(private_key_pem):
    """Create an RSA signer function for CloudFront."""
    private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)

    def sign(message):
        return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

    return sign


def get_cloudfront_private_key() -> str:
    """Get CloudFront private key from Secrets Manager with caching."""
    global _cached_private_key, _last_fetch_time

    now = int(time.time() * 1000)  # Current time in milliseconds

    # Return cached private key if still valid
    if _cached_private_key and (now - _last_fetch_time) < _CACHE_DURATION:
        return _cached_private_key

    try:
        secret_arn = EnvironmentVariables.CLOUDFRONT_SECRET_ARN
        if not secret_arn:
            logger.warning("CLOUDFRONT_SECRET_ARN not configured")
            return ""

        response = secrets_client.get_secret_value(SecretId=secret_arn)

        if not response.get("SecretString"):
            raise RuntimeError("Secret value is empty")

        # Parse the secret string and get the private key
        secret_data = json.loads(response["SecretString"])
        _cached_private_key = secret_data.get("privateKey")
        _last_fetch_time = now

        if not _cached_private_key:
            raise RuntimeError("Private key not found in secret data")

        return _cached_private_key

    except Exception as error:
        logger.error(f"Failed to fetch CloudFront private key from Secrets Manager: {error}")
        return ""


def s3_key_from_location(loc):
    """Extract S3 key from location dict."""
    obj = loc if isinstance(loc, dict) else {}
    key = obj.get("key", "")
    return key[1:] if key.startswith("/") else key


def check_s3_object_exists(s3_location):
    """
    Check if an S3 object exists before generating a presigned URL.

    Args:
        s3_location: Dictionary containing 'bucket' and 'key' for the S3 object

    Returns:
        bool: True if object exists, False otherwise
    """
    s3_location_dict = s3_location if isinstance(s3_location, dict) else {}
    bucket = s3_location_dict.get("bucket")
    key = s3_location_dict.get("key")

    if not bucket or not key:
        logger.warning(f"Invalid S3 location: missing bucket or key. Location: {s3_location_dict}")
        return False

    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        logger.debug(f"S3 object exists: s3://{bucket}/{key}")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "404":
            logger.warning(f"S3 object does not exist: s3://{bucket}/{key}")
        else:
            logger.error(f"Error checking S3 object existence: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking S3 object existence: {e}")
        return False


def clamp(n, min_val, max_val):
    """Clamp a number between min and max values."""
    if not isinstance(n, (int, float)) or not n == n:  # Check for NaN
        return min_val
    if n < min_val:
        return min_val
    if n > max_val:
        return max_val
    return n


def sanitize_resize_params(params):
    """Sanitize and validate resize parameters."""
    if not params:
        return {}

    out = {}

    # Width parameter
    if hasattr(params, "w") and isinstance(params.w, (int, float)) and params.w == params.w and params.w > 0:
        out["w"] = str(int(params.w))

    # Height parameter
    if hasattr(params, "h") and isinstance(params.h, (int, float)) and params.h == params.h and params.h > 0:
        out["h"] = str(int(params.h))

    # Quality parameter
    if hasattr(params, "q") and isinstance(params.q, (int, float)) and params.q == params.q:
        out["q"] = str(clamp(int(params.q), 1, 100))

    # Format parameter
    if hasattr(params, "f") and params.f and params.f in ("webp", "jpeg", "png"):
        out["f"] = params.f

    # Fit parameter
    if hasattr(params, "fit") and params.fit and params.fit in ("cover", "contain", "fill"):
        out["fit"] = params.fit

    # Grayscale parameter
    if hasattr(params, "grayscale") and isinstance(params.grayscale, bool):
        out["grayscale"] = "true" if params.grayscale else "false"

    # Blur parameter
    if hasattr(params, "blur") and isinstance(params.blur, (int, float)) and params.blur == params.blur:
        out["blur"] = str(clamp(int(params.blur), 1, 100))

    return out


def build_resize_query(params=None, version=None):
    """Build a deterministic query string for resize parameters."""
    sanitized = sanitize_resize_params(params)
    order = ["w", "h", "q", "f", "fit", "grayscale", "blur"]
    parts = []

    for key in order:
        if key in sanitized:
            parts.append(f"{key}={sanitized[key]}")

    # Add version parameter if provided
    if version is not None:
        if hasattr(version, "getTime"):
            version_timestamp = version.getTime()
        else:
            try:
                version_timestamp = float(version)
            except (ValueError, TypeError):
                version_timestamp = 0

        if version_timestamp > 0:
            parts.append(f"v={int(version_timestamp)}")

    return "&".join(parts)


def create_presigned_url(s3_location, expiration_time=None, resize_params=None, version=None):
    """
    Create a presigned URL for an S3 object with optional CloudFront signing.

    Args:
        s3_location: Dictionary containing 'bucket' and 'key' for the S3 object
        expiration_time: URL expiration time in seconds (default from env)
        resize_params: Parameters for image resizing (dict with w, h, q, f, fit, etc.)
        version: Object version timestamp

    Returns:
        str or None: Presigned URL if object exists, None otherwise
    """
    expires_in = expiration_time or EnvironmentVariables.AWS_PRESIGNED_URL_EXPIRATION_TIME

    # Check if S3 object exists first
    if not check_s3_object_exists(s3_location):
        logger.warning(f"S3 object does not exist, returning None for location: {s3_location}")
        return None

    has_cdn_signing = bool(
        EnvironmentVariables.CLOUDFRONT_DOMAIN
        and EnvironmentVariables.CLOUDFRONT_KEY_PAIR_ID
        and EnvironmentVariables.CLOUDFRONT_SECRET_ARN
    )

    # Try CloudFront signed URL if configured
    if has_cdn_signing:
        try:
            logger.debug("Using CloudFront signed URL")
            key = s3_key_from_location(s3_location)
            domain = EnvironmentVariables.CLOUDFRONT_DOMAIN or ""
            clean_domain = domain[8:] if domain.startswith("https://") else domain
            base_url = f"https://{clean_domain}/{key}"
            resize_query = build_resize_query(resize_params, version)
            url_to_sign = f"{base_url}?{resize_query}" if resize_query else base_url

            private_key = get_cloudfront_private_key().replace("\\n", "\n")
            expire_date = datetime.now() + timedelta(seconds=expires_in)

            signer = rsa_signer(private_key)
            cloudfront_signer = CloudFrontSigner(EnvironmentVariables.CLOUDFRONT_KEY_PAIR_ID, signer)
            signed_url = cloudfront_signer.generate_presigned_url(url_to_sign, date_less_than=expire_date)
            logger.debug(f"Generated CloudFront signed URL")
            return signed_url
        except Exception as error:
            logger.error(f"CloudFront signing error: {error}")
            logger.info("Falling back to S3 presigned URL")

    # Fallback to S3 presigned URL
    s3_location_dict = s3_location if isinstance(s3_location, dict) else {}
    logger.debug(f"Creating S3 presigned URL for: {s3_location_dict}")
    try:
        command = {
            "Bucket": s3_location_dict.get("bucket"),
            "Key": s3_location_dict.get("key"),
        }
        presigned_url = s3_client.generate_presigned_url("get_object", Params=command, ExpiresIn=expires_in)
        logger.debug(f"Generated S3 presigned URL")
        return presigned_url
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {str(e)}")
        return None
