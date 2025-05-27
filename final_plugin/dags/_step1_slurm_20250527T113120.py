from airflow import DAG
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

default_args = {
    'owner': '',
    'start_date': datetime(2025, 5, 27),
}

with DAG(
    dag_id='_step1_slurm_20250527T113120',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags="",
) as dag:
    slurm = SubmitAndMonitorSlurmJobOperator(
        task_id='submit_slurm',
        ssh_conn_id='',
        script_path='',
        
        
        
        
        
        
        
        poll_interval=30,
    )

    