#!/usr/bin/env python3

from loguru import logger
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import io

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "mir_db",
    "user": "mir_user",
    "password": "mir_password",
}

DATA_FOLDER = Path(__file__).parent.parent / "data"


def create_connection():
    connection_string = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(connection_string)
    return engine


def load_csv_files():
    engine = create_connection()

    # Year conversion mapping
    year_mapping = {
        "2018JJ00": "2018",
        "2019JJ00": "2019",
        "2020JJ00": "2020",
        "2021JJ00": "2021",
        "2022JJ00": "2022",
    }

    csv_files = {
        "population.csv": "population",
        "region.csv": "region",
        "travel_mode.csv": "travel_mode",
        "travel_motives.csv": "travel_motives",
        "trips.csv": "trips",
        "urbanization_level.csv": "urbanization_level",
    }

    for csv_file, table_name in csv_files.items():
        csv_path = DATA_FOLDER / csv_file

        if not csv_path.exists():
            logger.warning(f"File {csv_path} not found, skipping...")
            continue

        logger.info(f"Loading {csv_file} into table {table_name}...")

        try:
            if csv_file == "travel_mode.csv":
                df = pd.read_csv(csv_path, delimiter="|")
            elif csv_file == "urbanization_level.csv":
                df = pd.read_csv(csv_path, delimiter=";")
            else:
                df = pd.read_csv(csv_path)

            df.replace(".", None, inplace=True)

            # Apply year conversion mapping to all columns
            for col in df.columns:
                if df[col].dtype == "object":  # Only apply to string columns
                    df[col] = df[col].replace(year_mapping)

            if table_name == "trips":
                df = df.drop(columns=[df.columns[0]], errors="ignore")
            elif table_name == "urbanization_level":
                df = df.drop(columns=[df.columns[0]], errors="ignore")

            try:
                # Bulk load via COPY for reliability and speed
                copy_df_to_table(engine, df, table_name)
            except Exception as e:
                if "duplicate key value violates unique constraint" in str(e):
                    logger.info(
                        f"Table {table_name} already contains data, skipping..."
                    )
                else:
                    raise
            logger.info(f"Successfully loaded {len(df)} rows into {table_name}")

        except Exception as e:
            logger.error(f"Error loading {csv_file}: {str(e)}")

    logger.info("CSV loading completed!")


def copy_df_to_table(engine, df: pd.DataFrame, table_name: str):
    # Prepare CSV buffer with explicit NULL marker
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, na_rep="\\N")
    buffer.seek(0)

    # Quote column names to preserve case/special chars
    cols = ", ".join([f'"{col}"' for col in df.columns])
    copy_sql = f"COPY {table_name} ({cols}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',', NULL '\\N', QUOTE '\"')"

    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        try:
            cur.copy_expert(copy_sql, buffer)
        finally:
            cur.close()
        conn.commit()
    finally:
        conn.close()


def main():
    try:
        logger.info("Starting CSV to PostgreSQL loading process...")
        load_csv_files()
    except Exception as e:
        logger.error(f"Failed to load CSV files: {str(e)}")
        raise


if __name__ == "__main__":
    main()
