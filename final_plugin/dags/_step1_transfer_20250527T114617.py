from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

default_args = {
    'owner': '',
    'start_date': datetime(2025, 5, 27),
}

with DAG(
    dag_id='_step1_transfer_20250527T114617',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags="",
) as dag:
    transfer = BashOperator(
        task_id='transfer_to_gpfs',
        bash_command=(
            'aws s3 sync '
            ''
            '  '
            ''
        )
    )

    