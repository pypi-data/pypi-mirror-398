"""
Custom exception classes for the design data layer.
"""


class S3UploadError(Exception):
    """Error raised when an ODS script fails to upload to S3."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class MongoDBUpsertError(Exception):
    """Error raised when an ODS script fails to upsert to MongoDB."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AuthValidationError(Exception):
    """Error raised when auth validation fails."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
