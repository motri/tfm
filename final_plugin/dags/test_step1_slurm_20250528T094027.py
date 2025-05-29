from airflow import DAG
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

default_args = {
    'owner': 'test',
    'start_date': datetime(2025, 5, 28),
}

with DAG(
    dag_id='test_step1_slurm_20250528T094027',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags="",
) as dag:
    slurm = SubmitAndMonitorSlurmJobOperator(
        task_id='submit_slurm',
        ssh_conn_id='',
        sbatch_args='',
        poll_interval=30,
    )

    