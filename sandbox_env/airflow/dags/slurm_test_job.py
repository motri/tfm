from airflow import DAG
from datetime import datetime
from slurm_plugin.operators.slurm_operator import SubmitAndMonitorSlurmJobOperator

with DAG("slurm_async_job", start_date=datetime(2024, 1, 1), schedule_interval=None, catchup=False) as dag:
    run_job = SubmitAndMonitorSlurmJobOperator(
        task_id='submit_slurm',
        ssh_conn_id='hpc_ssh',
        script_path='/remote/path/script.sh',
        poll_interval=60
    )
