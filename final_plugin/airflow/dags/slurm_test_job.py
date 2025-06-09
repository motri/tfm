from airflow import DAG
from datetime import datetime
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator

with DAG("slurm_async_job", start_date=datetime(2024, 1, 1), schedule_interval=None, catchup=False, tags=["SLURM"]) as dag:
    run_job = SubmitAndMonitorSlurmJobOperator(
        task_id='submit_slurm',
        job_alias='Test manual Unai',
        ssh_conn_id='hpc_ssh',
        sbatch_args='--qos=qos_di14 example_run.sh',
        poll_interval=60
    )
