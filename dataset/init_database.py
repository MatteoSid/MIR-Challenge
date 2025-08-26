#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from pathlib import Path
from loguru import logger

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "mir_db",
    "user": "mir_user",
    "password": "mir_password",
}


def create_connection():
    connection_string = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(connection_string)
    return engine


def wait_for_postgres():
    import time

    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        try:
            engine = create_connection()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL is ready!")
            return True
        except Exception as e:
            attempt += 1
            logger.info(
                f"Waiting for PostgreSQL... (attempt {attempt}/{max_attempts}) - last error: {e}"
            )
            time.sleep(2)

    logger.error("PostgreSQL is not responding after maximum attempts")
    return False


def create_tables():
    if not wait_for_postgres():
        raise Exception("Cannot connect to PostgreSQL")

    engine = create_connection()
    sql_file = Path(__file__).parent / "create_tables.sql"

    with open(sql_file, "r") as file:
        sql_content = file.read()

    try:
        with engine.connect() as conn:
            with conn.begin():  # Start a transaction
                conn.execute(text(sql_content))
        logger.info("Database tables created successfully!")

    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise


def main():
    try:
        logger.info("Initializing database schema...")
        create_tables()
        logger.info("Database initialization completed!")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
