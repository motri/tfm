from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

default_args = {
    'owner': 'Unai Motriko',
    'start_date': datetime(2025, 5, 29),
}

with DAG(
    dag_id='tags_test_step1_git_20250529T084124',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=["test_git,tags_test"]
) as dag:
    git_clone = BashOperator(
        task_id='git_clone',
        bash_command=(
            'git clone '
            ''
            'https://github.com/motri/tfm tmp'
        )
    )

    