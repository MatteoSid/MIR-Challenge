#!/usr/bin/env python3

from sqlalchemy import create_engine, text
from loguru import logger
from dataset.init_database import create_connection, wait_for_postgres, DB_CONFIG
import argparse


def drop_schema_public():
    if not wait_for_postgres():
        raise RuntimeError("Cannot connect to PostgreSQL")

    engine = create_connection()
    user = DB_CONFIG.get("user", "mir_user")

    stmts = [
        "DROP SCHEMA IF EXISTS public CASCADE",
        "CREATE SCHEMA public",
        f"GRANT ALL ON SCHEMA public TO {user}",
        "GRANT ALL ON SCHEMA public TO public",
    ]

    with engine.connect() as conn:
        for s in stmts:
            logger.info(f"Executing: {s}")
            conn.execute(text(s))
        conn.commit()

    logger.success("Schema 'public' dropped and recreated successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Drop all tables in PostgreSQL (project DB) by recreating schema 'public'."
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip interactive confirmation."
    )
    args = parser.parse_args()

    if not args.yes:
        logger.warning(
            "This will DROP ALL TABLES and objects in schema 'public' of database '{db}'.".format(
                db=DB_CONFIG.get("database")
            )
        )
        confirm = input("Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            logger.info("Aborted by user.")
            return

    drop_schema_public()


if __name__ == "__main__":
    main()
