#!/usr/bin/env python3

from dataset.init_database import main as init_db
from dataset.load_csv_to_postgres import main as load_csv, create_connection
from loguru import logger
from sqlalchemy import text


def check_if_db_is_populated():
    """Checks if the database is already populated with tables."""
    try:
        engine = create_connection()
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public');"
                )
            ).scalar()
            return result
    except Exception as e:
        logger.warning(f"Could not check if database is populated: {e}")
        # Assume not populated if check fails, to allow setup to proceed
        return False


def main():
    try:
        logger.info("Checking database status...")
        if check_if_db_is_populated():
            logger.info("Database already appears to be populated. Aborting setup.")
            return

        logger.info("Starting complete database setup...")

        logger.info("Step 1: Creating database tables...")
        init_db()

        logger.info("Step 2: Loading CSV data...")
        load_csv()

        logger.info("Database setup completed successfully!")

    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
