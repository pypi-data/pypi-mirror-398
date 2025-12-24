"""
Database clients for PostgreSQL and MongoDB.

To avoid initializing all database clients at import time, import specific clients
from their respective modules:

    from optikka_design_data_layer.db.postgres_client import postgres_client
    from optikka_design_data_layer.db.mongo_client import mongodb_client
    from optikka_design_data_layer.db.mongodb_guide_client import mongodb_guide_client
"""

from optikka_design_data_layer.db.postgres_client import PostgresDBClient
from optikka_design_data_layer.db.mongo_client import MongoDBClient
from optikka_design_data_layer.db.mongodb_guide_client import MongoDBGuideClient
from optikka_design_data_layer.db.postgres_credential_manager import PostgresCredentialManager
from optikka_design_data_layer.db.connection_types import (
    ConnectionStats,
    ConnectionConfig,
    ConnectionHealthStatus,
)

__all__ = [
    "PostgresDBClient",
    "MongoDBClient",
    "MongoDBGuideClient",
    "PostgresCredentialManager",
    "ConnectionStats",
    "ConnectionConfig",
    "ConnectionHealthStatus",
]
