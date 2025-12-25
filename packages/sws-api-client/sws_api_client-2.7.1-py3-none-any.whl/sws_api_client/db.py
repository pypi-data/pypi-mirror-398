"""Database Management Module for SWS API.

This module provides functionality for managing database operations and credentials
through the SWS API client.
"""

import logging
from typing import Optional, Dict, Any
from sws_api_client.sws_api_client import SwsApiClient

logger = logging.getLogger(__name__)

class DB:
    """Class for managing database operations through the SWS API.

    This class provides methods for retrieving database credentials,
    establishing connections, and executing queries.

    Args:
        sws_client (SwsApiClient): An instance of the SWS API client
    """

    def __init__(self, sws_client: SwsApiClient) -> None:
        """Initialize the DB manager with SWS client.
        
        Args:
            sws_client: An instance of the SWS API client
        """
        self.sws_client = sws_client
        self._cached_credentials: Dict[bool, Dict[str, Any]] = {}
        self._connection = None
        self._connection_write_mode: Optional[bool] = None

    def get_credentials(self, write: bool = False, use_cache: bool = True) -> Dict[str, Any]:
        """Get database credentials.

        Retrieves database credentials including host, port, username, and password
        from the discover get sessions API /credentials endpoint.

        Args:
            write: Whether write access credentials are required

        Returns:
            Dict[str, Any]: Dictionary containing database credentials with host, 
                           port, username, password, and database

        Raises:
            Exception: If failed to retrieve database credentials
        """
        url = "/db/credentials"
        params = {"write": "true"} if write else None

        if use_cache and write in self._cached_credentials:
            logger.debug("Using cached database credentials (write=%s)", write)
            return self._cached_credentials[write]

        logger.debug(f"Requesting database credentials from {url} (write={write})")

        try:
            result = self.sws_client.discoverable.get("session_api", url, params=params)
            
            # Extract the credentials from the nested structure and add default database if missing
            if result.get('credentials'):
                creds = result['credentials']
                
                # Add default database if not provided
                if not creds.get('database'):
                    creds['database'] = 'sws_data'
                
                logger.info("Database credentials retrieved successfully")
                logger.debug(
                    "Processed credentials - Host: %s, Port: %s, Database: %s, Username: %s",
                    creds.get('host'),
                    creds.get('port'),
                    creds.get('database'),
                    creds.get('username'),
                )

                if use_cache:
                    self._cached_credentials[write] = creds

                return creds
            else:
                if use_cache:
                    self._cached_credentials[write] = result
                return result
                
        except Exception as e:
            logger.error(f"Failed to retrieve database credentials: {str(e)}")
            raise Exception(f"Failed to retrieve database credentials: {str(e)}")

    def connect(self, use_cache: bool = True, write: bool = False) -> Any:
        """Create or get existing database connection.

        Creates a new database connection or returns the existing one if still valid.

        Args:
            use_cache: Boolean indicating whether to use cached credentials
            write: Whether the connection must use write-enabled credentials

        Returns:
            Any: A database connection object

        Raises:
            ImportError: If required database packages are not installed
            Exception: If database connection fails
        """
        try:
            import psycopg2
            from psycopg2 import sql
        except ImportError:
            raise ImportError("The psycopg2 package is required but not installed. "
                            "Please install it to use connect.")

        # Check if we have a valid existing connection
        if self._connection and self._connection_write_mode == write:
            try:
                # Test if connection is still valid
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                logger.debug("Reusing existing database connection")
                return self._connection
            except Exception:
                logger.debug("Existing connection invalid, creating new one")
                self._connection = None
                self._connection_write_mode = None
        elif self._connection and self._connection_write_mode != write:
            logger.debug(
                "Existing connection uses write=%s but write=%s requested; refreshing",
                self._connection_write_mode,
                write,
            )
            self.disconnect()

        # Get credentials (use cache if available and requested)
        if use_cache and write in self._cached_credentials:
            logger.debug("Using cached database credentials (write=%s)", write)
            creds = self._cached_credentials[write]
        else:
            logger.debug("Retrieving fresh database credentials (write=%s)", write)
            creds = self.get_credentials(write=write, use_cache=use_cache)

        # Create new PostgreSQL connection
        try:
            self._connection = psycopg2.connect(
                host=creds['host'],
                port=int(creds['port']),
                database=creds['database'],
                user=creds['username'],
                password=creds['password'],
                options="-c search_path=aproduction,operational_data,reference_data,public"
            )
            
            self._connection_write_mode = write
            logger.debug("New database connection established (write=%s)", write)
            return self._connection
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {str(e)}")
            raise Exception(f"Database connection failed: {str(e)}")

    def disconnect(self) -> None:
        """Close database connection.

        Closes the current database connection if it exists.
        """
        if self._connection:
            try:
                self._connection.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Failed to close connection: {str(e)}")
            self._connection = None
            self._connection_write_mode = None
        else:
            logger.debug("No active connection to close")

    def execute_query(
        self,
        query: str,
        use_cache: bool = True,
        avoid_connection_closure: bool = False,
        write: bool = False,
    ) -> list:
        """Execute a database query.

        Executes a SQL query against the database. Automatically manages connection.

        Args:
            query: The SQL query string to execute
            use_cache: Boolean indicating whether to use cached credentials
            avoid_connection_closure: Boolean indicating whether to keep connection open after query
            write: Whether the query requires write-enabled credentials

        Returns:
            list: List of dictionaries containing the query results

        Raises:
            Exception: If database query execution fails
        """
        logger.debug("Executing database query")
        
        # Get or create connection
        con = self.connect(use_cache=use_cache, write=write)
        
        # Execute query
        try:
            cursor = con.cursor()
            cursor.execute(query)
            
            # Fetch results if it's a SELECT query
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
            else:
                result = []
                con.commit()  # Commit for non-SELECT queries
            
            cursor.close()
            
            logger.info(f"Query executed successfully. Retrieved {len(result)} rows")
            
            # Close connection if requested
            if not avoid_connection_closure:
                self.disconnect()
            
            return result
            
        except Exception as e:
            logger.error(f"Database query execution failed: {str(e)}")
            
            # Always try to close connection on error unless specifically avoiding it
            if not avoid_connection_closure:
                self.disconnect()
            
            raise Exception(f"Database query execution failed: {str(e)}")

    def get_cached_credentials(self, write: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Return cached credentials for the requested access level, if available."""

        if write is None:
            write = self._connection_write_mode
        if write is None:
            return None
        return self._cached_credentials.get(write)