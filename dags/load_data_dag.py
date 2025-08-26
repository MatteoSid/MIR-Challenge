from __future__ import annotations

import pendulum
import sys
import os

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with DAG(
    dag_id="load_data_to_postgres",
    start_date=pendulum.datetime(2025, 8, 25, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["data"],
) as dag:
    init_db = BashOperator(
        task_id="init_db",
        bash_command=f"{sys.executable} {PROJECT_ROOT}/dataset/init_database.py",
    )

    load_data = BashOperator(
        task_id="load_data",
        bash_command=f"{sys.executable} {PROJECT_ROOT}/dataset/load_csv_to_postgres.py",
    )

    init_db >> load_data
