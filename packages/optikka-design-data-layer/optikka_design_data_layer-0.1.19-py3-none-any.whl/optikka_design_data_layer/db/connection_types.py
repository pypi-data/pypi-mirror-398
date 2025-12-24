"""
Connection-related value objects and types for PostgreSQL connection management.

This module defines immutable value objects following the microservice design patterns
for connection statistics, configuration, and credentials.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ConnectionHealthStatus(str, Enum):
    """
    Health status of the database connection.
    
    Used for monitoring and connection lifecycle decisions.
    """
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PostgresCredentials:
    """
    Immutable value object for PostgreSQL credentials.
    
    Contains username and password retrieved from AWS Secrets Manager.
    Frozen dataclass ensures immutability following value object principles.
    """
    username: str
    password: str


@dataclass(frozen=True)
class ConnectionStats:
    """
    Immutable connection statistics for monitoring and debugging.
    
    Provides comprehensive information about the current connection state,
    performance metrics, and health status for operational monitoring.
    """
    has_connection: bool
    is_connected: bool
    connection_age_seconds: Optional[float]
    max_connection_age_seconds: int
    total_reconnections: int
    last_health_check: Optional[datetime]
    health_status: ConnectionHealthStatus


@dataclass(frozen=True)
class ConnectionConfig:
    """
    Immutable configuration for PostgreSQL connection parameters.
    
    Contains all necessary configuration for establishing and managing
    database connections, typically loaded from environment variables.
    """
    host: str
    database: str
    port: int
    sslmode: str
    max_connection_age_seconds: int
    secrets_arn: str
