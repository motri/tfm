
from airflow import DAG
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator
from datetime import datetime

with DAG(
    dag_id='Daige_step2_slurm_20250623T101654',
    start_date=datetime(2025, 6, 23),
    schedule_interval=None,
    catchup=False,
    tags=["test_git,tags_test"]
) as dag:

    run_job = SubmitAndMonitorSlurmJobOperator(
        task_id='submit_slurm',
        ssh_conn_id='hpc_ssh',
        sbatch_args='example_run.sh --qos=qos_di14',
        poll_interval=60,
    )