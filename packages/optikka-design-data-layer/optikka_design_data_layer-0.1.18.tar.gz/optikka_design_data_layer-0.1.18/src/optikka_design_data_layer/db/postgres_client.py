"""
PostgreSQL connection manager with singleton pattern optimized for AWS Lambda.

This module provides centralized connection management with health checks,
automatic reconnection, and comprehensive monitoring for Lambda reuse scenarios.
"""

import psycopg2

# Import from lambda layer
from optikka_design_data_layer import logger# pylint: disable=relative-beyond-top-level, import-error, no-name-in-module
from datetime import datetime
from typing import Optional, List
from psycopg2.extras import RealDictCursor

from optikka_design_data_layer.db.connection_types import ConnectionStats, ConnectionConfig, ConnectionHealthStatus
from optikka_design_data_layer.db.postgres_credential_manager import PostgresCredentialManager, CredentialRetrievalError
from optikka_design_data_layer.utils.config import EnvironmentVariables

# from design_data_layer.python.models import WorkflowExecutionResult  # pylint: disable=import-error
# from design_data_layer.python.models import Image  # pylint: disable=import-error

from ods_models import WorkflowExecutionResult, Image, WorkflowBatch, KoreExecution  # pylint: disable=import-error

# from ods_models import Image  # pylint: disable=import-error


class PostgresDBClient:
    """
    Singleton connection manager optimized for AWS Lambda reuse.

    Provides a single, reusable database connection per Lambda container
    with automatic health checks, aging policies, and graceful reconnection.

    Features:
    - Singleton pattern for Lambda container reuse
    - Automatic connection health monitoring
    - Age-based connection recreation
    - Comprehensive connection statistics
    - Graceful error handling and recovery
    """

    _instance: Optional["PostgresDBClient"] = None
    _initialized: bool = False

    def __new__(cls, config: Optional[ConnectionConfig] = None) -> "PostgresDBClient":
        """
        Singleton pattern implementation for Lambda reuse.

        Args:
            config: Optional connection configuration (uses environment if not provided)

        Returns:
            Singleton instance of PostgresDBClient
        """
        if cls._instance is None:
            cls._instance = super(PostgresDBClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[ConnectionConfig] = None):
        """
        Initialize singleton instance only once.

        Args:
            config: Optional connection configuration (uses environment if not provided)
        """
        if self._initialized:
            return

        self._connection: Optional[psycopg2.extensions.connection] = None
        self._connection_created_at: Optional[datetime] = None
        self._total_reconnections: int = 0
        self._last_health_check: Optional[datetime] = None
        self._health_status: ConnectionHealthStatus = ConnectionHealthStatus.UNKNOWN

        # Configuration with defaults from environment
        self._config = self._load_config_from_environment()

        # Initialize credential manager
        self._credential_manager = PostgresCredentialManager()
        self._initialized = True

        logger.info("PostgresConnectionManager singleton initialized")

    def get_connection(self) -> psycopg2.extensions.connection:
        """
        Get or create a database connection.

        Returns:
            Active PostgreSQL connection

        Raises:
            ConnectionError: If connection cannot be established
        """
        logger.debug(f"Should recreate connection: {self._should_recreate_connection()}")
        if self._should_recreate_connection():
            self._create_new_connection()
        logger.debug(f"Connection: {self._connection}")
        return self._connection

    def close_connection(self) -> None:
        """
        Close the database connection gracefully.

        Rolls back any pending transactions and closes the connection.
        Resets connection state for clean shutdown.
        """
        if self._connection and not self._connection.closed:
            try:
                self._connection.rollback()  # Rollback any pending transactions
                self._connection.close()
                logger.info("Database connection closed gracefully")
            except Exception as e:
                logger.warning(f"Error during connection close: {str(e)}")

        self._connection = None
        self._connection_created_at = None
        self._health_status = ConnectionHealthStatus.UNKNOWN

    def reset_connection(self) -> None:
        """
        Reset connection for new Lambda invocation.

        Rolls back any pending transactions but keeps connection alive for reuse.
        If reset fails, connection will be closed and recreated on next use.
        """
        if self._connection and not self._connection.closed:
            try:
                self._connection.rollback()
                logger.info("Database connection reset for new invocation")
            except Exception as e:
                logger.warning(f"Error during connection reset: {str(e)}")
                # If reset fails, close and recreate on next use
                self.close_connection()

    def get_connection_stats(self) -> ConnectionStats:
        """
        Get comprehensive connection statistics for monitoring.

        Returns:
            ConnectionStats with current connection state and metrics
        """
        connection_age_seconds = None
        if self._connection_created_at:
            age = datetime.now() - self._connection_created_at
            connection_age_seconds = age.total_seconds()

        return ConnectionStats(
            has_connection=self._connection is not None,
            is_connected=not self._connection.closed if self._connection else False,
            connection_age_seconds=connection_age_seconds,
            max_connection_age_seconds=self._config.max_connection_age_seconds,
            total_reconnections=self._total_reconnections,
            last_health_check=self._last_health_check,
            health_status=self._health_status,
        )

    def _load_config_from_environment(self) -> ConnectionConfig:
        """
        Load connection configuration from environment variables.

        Returns:
            ConnectionConfig loaded from environment

        Raises:
            ValueError: If required environment variables are missing
        """
        # Validate required PostgreSQL environment variables
        required_vars = ["POSTGRES_PROXY_HOST", "POSTGRES_DB_NAME", "POSTGRES_SECRET_ARN"]
        missing_vars = []

        for var in required_vars:
            if getattr(EnvironmentVariables, var) is None:
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"Missing required PostgreSQL environment variables: {', '.join(missing_vars)}")

        return ConnectionConfig(
            host=EnvironmentVariables.POSTGRES_PROXY_HOST,
            database=EnvironmentVariables.POSTGRES_DB_NAME,
            port=EnvironmentVariables.POSTGRES_PORT,
            sslmode=EnvironmentVariables.POSTGRES_SSL_MODE,
            max_connection_age_seconds=EnvironmentVariables.MAX_CONNECTION_AGE,
            secrets_arn=EnvironmentVariables.POSTGRES_SECRET_ARN,
        )

    def _should_recreate_connection(self) -> bool:
        """
        Check if connection should be recreated based on various criteria.

        Returns:
            True if connection should be recreated, False otherwise
        """
        if self._connection is None:
            logger.debug("Connection recreation needed: No connection exists")
            return True

        if self._connection.closed:
            logger.debug("Connection recreation needed: Connection is closed")
            return True

        # Check connection age
        if self._connection_created_at:
            age = datetime.now() - self._connection_created_at
            if age.total_seconds() > float(self._config.max_connection_age_seconds):
                logger.info(
                    f"Connection recreation needed: Age {age.total_seconds():.1f}s exceeds maximum {self._config.max_connection_age_seconds}s"
                )
                return True

        # Perform health check
        if not self._is_connection_healthy():
            logger.info("Connection recreation needed: Health check failed")
            return True

        return False

    def _is_connection_healthy(self) -> bool:
        """
        Test connection health with a simple query.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            self._last_health_check = datetime.now()
            self._health_status = ConnectionHealthStatus.HEALTHY
            return True

        except Exception as e:
            logger.warning(f"Connection health check failed: {str(e)}")
            self._health_status = ConnectionHealthStatus.UNHEALTHY
            return False

    def _create_new_connection(self) -> None:
        """
        Create a new database connection.

        Closes any existing connection, retrieves fresh credentials,
        and establishes a new connection with proper error handling.

        Raises:
            ConnectionError: If connection cannot be established
        """
        logger.info("Creating new database connection")

        # Close existing connection if it exists
        if self._connection and not self._connection.closed:
            try:
                self._connection.close()
                logger.debug("Closed existing connection")
            except Exception as e:
                logger.warning(f"Error closing old connection: {str(e)}")

        try:
            # Get fresh credentials
            credentials = self._credential_manager.get_credentials(self._config.secrets_arn)

            # Create new connection
            self._connection = psycopg2.connect(
                host=self._config.host,
                database=self._config.database,
                user=credentials.username,
                password=credentials.password,
                port=self._config.port,
                sslmode=self._config.sslmode,
            )

            # Update connection metadata
            self._connection_created_at = datetime.now()
            self._total_reconnections += 1
            self._health_status = ConnectionHealthStatus.HEALTHY

            logger.info(f"Database connection established successfully (reconnection #{self._total_reconnections})")

        except CredentialRetrievalError as e:
            logger.error(f"Failed to retrieve credentials: {str(e)}")
            self._health_status = ConnectionHealthStatus.UNHEALTHY
            raise ConnectionError(f"Cannot retrieve database credentials: {str(e)}")

        except psycopg2.Error as e:
            logger.error(f"PostgreSQL connection error: {str(e)}")
            self._health_status = ConnectionHealthStatus.UNHEALTHY
            raise ConnectionError(f"Cannot establish PostgreSQL connection: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error creating database connection: {str(e)}")
            self._health_status = ConnectionHealthStatus.UNHEALTHY
            raise ConnectionError(f"Cannot establish database connection: {str(e)}")

    def get_all_images(self, pagination_options: dict) -> tuple[List[Image], int]:
        """
        Retrieve all image data from the PostgreSQL database with pagination and sorting.

        Args:
            pagination_options: Dictionary containing:
                - limit: Number of records to return
                - skip: Number of records to skip
                - sort_by: Column name to sort by
                - sort_order: Sort direction (ASC or DESC)

        Returns:
            Tuple of (List of Image objects, Total count of all images)
        """
        try:
            # Extract sorting parameters with defaults
            sort_by = pagination_options.get("sort_by", "createdAt")
            sort_order = pagination_options.get("sort_order", "DESC")

            # Validate sort_by column to prevent SQL injection
            valid_columns = {"name", "createdAt", "size", "updatedAt", "id"}
            if sort_by not in valid_columns:
                logger.warning(f"Invalid sort_by column '{sort_by}', defaulting to 'createdAt'")
                sort_by = "createdAt"

            # Validate sort_order to prevent SQL injection
            if sort_order not in {"ASC", "DESC"}:
                logger.warning(f"Invalid sort_order '{sort_order}', defaulting to 'DESC'")
                sort_order = "DESC"

            with self.get_connection() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get total count of all images
                    cursor.execute('SELECT COUNT(*) FROM "Image"')
                    total_count = cursor.fetchone()["count"]

                    # Build dynamic ORDER BY clause with validated parameters
                    # Using f-string is safe here because we've validated the inputs against whitelists
                    order_by_clause = f'"{sort_by}" {sort_order}, "id" ASC'
                    query = f'SELECT * FROM "Image" ORDER BY {order_by_clause} LIMIT %s OFFSET %s'

                    logger.info(
                        f"Executing query: {query} with limit={pagination_options['limit']}, offset={pagination_options['skip']}"
                    )

                    cursor.execute(
                        query,
                        (pagination_options["limit"], pagination_options["skip"]),
                    )
                    rows = cursor.fetchall()
                    return ([Image(**row) for row in rows], total_count)
        except psycopg2.Error as e:
            logger.error(f"Database error while retrieving all images: {str(e)}")
            return ([], 0)
        except Exception as e:
            logger.error(f"Unexpected error retrieving all images: {str(e)}")
            return ([], 0)

    def get_image_data(
        self, image_id: str
    ) -> Optional[Image]:  # this should be a get All images data, add pagination, and filter where image = Filter
        """
        Retrieve image data from the PostgreSQL database and return it as an Image object.
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute('SELECT * FROM "Image" WHERE "id" = %s', (image_id,))
                    row = cursor.fetchone()
                    return Image(**row) if row else None
        except psycopg2.Error as e:
            logger.error(f"Database error while retrieving image data for ID {image_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving image data for ID {image_id}: {str(e)}")
            return None

    def get_workflow_execution_results_by_original_image_id(
        self, original_image_id: str
    ) -> list[WorkflowExecutionResult]:
        """
        Get workflow execution results by original image id.
        """
        try:
            connection = self.get_connection()

            # send: originalImageId
            # search: WorkflowExecutionResult table
            # get: id

            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    'SELECT * FROM "WorkflowExecutionResult" WHERE "originalImageId" = %s', (original_image_id,)
                )
                rows = cursor.fetchall()
                return [WorkflowExecutionResult(**row) for row in rows]

        except psycopg2.Error as e:
            logger.error(f"Error retrieving workflow execution results by original image id: {str(e)}")
            raise ConnectionError(f"Failed to retrieve workflow execution results by original image id: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving workflow execution results by original image id: {str(e)}")
            raise Exception(f"Cannot retrieve workflow execution results by original image id: {str(e)}")

    def get_workflow_batch_by_batch_id(self, batch_id: str) -> WorkflowBatch:
        """
        Get workflow batch by batch id.
        """
        try:
            connection = self.get_connection()
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM "WorkflowBatch" WHERE "id" = %s', (batch_id,))
                row = cursor.fetchone()
                return WorkflowBatch(**row) if row else None
        except psycopg2.Error as e:
            logger.error(f"Error retrieving workflow batch by batch id: {str(e)}")
            raise ConnectionError(f"Failed to retrieve workflow batch by batch id: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving workflow batch by batch id: {str(e)}")
            raise Exception(f"Cannot retrieve workflow batch by batch id: {str(e)}")

    def get_kore_execution_by_kore_execution_id(self, kore_execution_id: str) -> KoreExecution:
        """
        Get kore execution by kore execution id.
        """
        try:
            connection = self.get_connection()
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('SELECT * FROM "KoreExecution" WHERE "id" = %s', (kore_execution_id,))
                row = cursor.fetchone()
                return KoreExecution(**row) if row else None
        except psycopg2.Error as e:
            logger.error(f"Error retrieving kore execution by kore execution id: {str(e)}")
            raise ConnectionError(f"Failed to retrieve kore execution by kore execution id: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving kore execution by kore execution id: {str(e)}")
            raise Exception(f"Cannot retrieve kore execution by kore execution id: {str(e)}")

    def get_all_studio_ids_list(self, pagination_options: dict) -> tuple[list[dict], int]:
        """
        Retrieve all studios (id and name) from the PostgreSQL database with pagination.
        
        Args:
            pagination_options: Dictionary containing:
                - limit: Number of records to return
                - skip: Number of records to skip
        
        Returns:
            Tuple of (List of dicts with 'id' and 'name' keys, Total count of all studios)
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get total count of all studios
                    cursor.execute('SELECT COUNT(*) FROM "Studio"')
                    total_count = cursor.fetchone()["count"]
                    
                    # Get paginated studios with id and name
                    query = 'SELECT id, name FROM "Studio" ORDER BY "id" ASC LIMIT %s OFFSET %s'
                    logger.info(
                        f"Executing query: {query} with limit={pagination_options['limit']}, offset={pagination_options['skip']}"
                    )
                    
                    cursor.execute(
                        query,
                        (pagination_options["limit"], pagination_options["skip"]),
                    )
                    rows = cursor.fetchall()
                    # Return only id and name for each record
                    return [{"id": row["id"], "name": row.get("name", row["id"])} for row in rows], total_count
        except psycopg2.Error as e:
            logger.error(f"Database error while retrieving all studio ids list: {str(e)}")
            return ([], 0)
        except Exception as e:
            logger.error(f"Unexpected error retrieving all studio ids list: {str(e)}")
            return ([], 0)

    def get_all_account_ids_list(self, pagination_options: dict) -> tuple[list[dict], int]:
        """
        Retrieve all distinct account IDs from the Image table with pagination.
        If Account table exists, joins to get account name, otherwise uses accountId as name.
        
        Args:
            pagination_options: Dictionary containing:
                - limit: Number of records to return
                - skip: Number of records to skip
        
        Returns:
            Tuple of (List of dicts with 'id' and 'name' keys, Total count of distinct account IDs)
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Try to get accounts from Account table if it exists, otherwise use Image table
                    # First check if Account table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'Account'
                        )
                    """)
                    account_table_exists = cursor.fetchone()["exists"]
                    
                    if account_table_exists:
                        # Get total count of accounts
                        cursor.execute('SELECT COUNT(*) FROM "Account"')
                        total_count = cursor.fetchone()["count"]
                        
                        # Get paginated accounts with id and name
                        query = 'SELECT id, name FROM "Account" ORDER BY "id" ASC LIMIT %s OFFSET %s'
                        logger.info(
                            f"Executing query: {query} with limit={pagination_options['limit']}, offset={pagination_options['skip']}"
                        )
                        
                        cursor.execute(
                            query,
                            (pagination_options["limit"], pagination_options["skip"]),
                        )
                        rows = cursor.fetchall()
                        # Return only id and name for each record
                        return [{"id": row["id"], "name": row.get("name", row["id"])} for row in rows], total_count
                    else:
                        # Get total count of distinct account IDs from Image table
                        cursor.execute('SELECT COUNT(DISTINCT "accountId") FROM "Image"')
                        total_count = cursor.fetchone()["count"]
                        
                        # Get paginated distinct account IDs (use accountId as both id and name)
                        query = 'SELECT DISTINCT "accountId" as id FROM "Image" ORDER BY "accountId" ASC LIMIT %s OFFSET %s'
                        logger.info(
                            f"Executing query: {query} with limit={pagination_options['limit']}, offset={pagination_options['skip']}"
                        )
                        
                        cursor.execute(
                            query,
                            (pagination_options["limit"], pagination_options["skip"]),
                        )
                        rows = cursor.fetchall()
                        # Return id and name (using accountId as name since no Account table)
                        return [{"id": row["id"], "name": row["id"]} for row in rows], total_count
        except psycopg2.Error as e:
            logger.error(f"Database error while retrieving all account ids list: {str(e)}")
            return ([], 0)
        except Exception as e:
            logger.error(f"Unexpected error retrieving all account ids list: {str(e)}")
            return ([], 0)


class ConnectionError(Exception):
    """
    Raised when database connection cannot be established.

    Specific exception type for connection-related failures, allowing
    calling code to handle connection issues appropriately.
    """

    pass


# Lazy initialization to avoid instantiation on import
_postgres_instance = None


class _PostgresClientProxy:
    """
    Lazy-loading proxy for PostgresDBClient singleton.

    The actual PostgresDBClient instance is only created when first accessed,
    not when the module is imported. This prevents initialization errors in
    Lambda functions that don't use PostgreSQL.
    """
    def __getattr__(self, name):
        global _postgres_instance
        if _postgres_instance is None:
            _postgres_instance = PostgresDBClient()
        return getattr(_postgres_instance, name)


postgres_client = _PostgresClientProxy()
