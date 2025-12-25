"""
Database creation script for a2a service.

This script connects to PostgreSQL using environment variables and creates
the database for a2a service if it doesn't already exist.
"""

import sys

from sqlalchemy import URL, create_engine, make_url, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from aixtools.a2a.google_sdk.store.config import POSTGRES_URL
from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


def database_exists(db_url: URL) -> bool:
    """
    Check if database exists.

    Args:
        db_url: SQLAlchemy URL to connect to PostgreSQL server

    Returns:
        bool: True if database exists, False otherwise
    """
    engine = create_engine(
        db_url,
        connect_args={
            "gssencmode": "disable",
        },
    )
    try:
        with engine.connect():
            logger.info("Successfully connected")
            return True
    except SQLAlchemyError as e:
        msg = str(e)
        if "does not exist" in msg and db_url.database and db_url.database in msg:
            return False
        raise e


def build_database_url(db_name: str | None = None) -> URL:
    """
    Build the PostgreSQL database URL.

    Args:
        db_name: Name of the database

    Returns:
        str: PostgreSQL connection URL
    """
    db_url = make_url(POSTGRES_URL)
    db_url = db_url.set(drivername="postgresql+psycopg2")
    if db_name is not None:
        db_url = db_url.set(database=db_name)
    return db_url


def create_database_if_not_exists() -> bool:
    """
    Create the database if it doesn't exist.

    Returns:
        bool: True if database was created or already exists, False on error
    """
    engine = None

    try:
        db_url = build_database_url()
        logger.info("Connecting to PostgreSQL server at %s:%s...", db_url.host, db_url.port)
        logger.info("Using credentials: %s@%s", db_url.username, db_url.host)

        # Check if database already exists
        if database_exists(db_url):
            logger.info("Database '%s' already exists", db_url.database)
            return True

        # Create the database
        logger.info("Creating database '%s'...", db_url.database)
        postgres_db_url = db_url.set(database="postgres")
        engine = create_engine(
            postgres_db_url,
            connect_args={
                "gssencmode": "disable",
            },
        )
        # PostgreSQL CREATE DATABASE must be executed outside a transaction block
        # Use connection with autocommit isolation level - DO NOT extend this query with other commands blindly
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(f'CREATE DATABASE "{db_url.database}"'))
        logger.info("Database '%s' created successfully", db_url.database)
        return True

    except OperationalError as e:
        logger.error("Database connection error: %s", str(e))
        logger.error("Please check your connection parameters and ensure PostgreSQL is running")
        return False
    except SQLAlchemyError as e:
        logger.error("SQLAlchemy error: %s", str(e))
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error: %s", str(e))
        return False
    finally:
        # Clean up engine
        if engine:
            engine.dispose()
            logger.info("Database connection closed")


def check_database_connection() -> bool:
    """
    Test connection to the newly created database.

    Returns:
        bool: True if connection successful, False otherwise
    """
    engine = None
    target_db_url = build_database_url()
    try:
        # Build connection URL to the target database
        logger.info("Testing connection to database '%s'...", target_db_url.database)

        # Create engine for the target database with optimized settings
        engine = create_engine(
            target_db_url,
            connect_args={
                "gssencmode": "disable",  # Disable GSS encryption to avoid delays
            },
        )

        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            row = result.fetchone()
            if row:
                version = row[0]
                logger.info("Successfully connected to database '%s'", target_db_url.database)
                logger.info("PostgreSQL version: %s", version)
            else:
                logger.info("Successfully connected to database '%s'", target_db_url.database)

        return True

    except OperationalError as e:
        logger.error("Failed to connect to database '%s': %s", target_db_url.database, str(e))
        return False
    except SQLAlchemyError as e:
        logger.error("SQLAlchemy error testing connection: %s", str(e))
        return False
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected error testing connection: %s", str(e))
        return False
    finally:
        if engine:
            engine.dispose()


def main():
    """Main function to create database and test connection."""
    logger.info("Starting database creation script...")
    if not create_database_if_not_exists():
        logger.error("Failed to create database")
        sys.exit(1)
    if not check_database_connection():
        logger.error("Failed to connect to the created database")
        sys.exit(1)
    logger.info("Database creation script completed successfully!")


if __name__ == "__main__":
    main()
