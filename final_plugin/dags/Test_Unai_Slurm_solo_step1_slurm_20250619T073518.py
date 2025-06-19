
from airflow import DAG
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator
from datetime import datetime

with DAG(
    dag_id='Test_Unai_Slurm_solo_step1_slurm_20250619T073518',
    start_date=datetime(2025, 6, 19),
    schedule_interval=None,
    catchup=False,
    tags=[""]
) as dag:

    run_job = SubmitAndMonitorSlurmJobOperator(
        task_id='submit_slurm',
        ssh_conn_id='hpc_ssh',
        sbatch_args='example_run.sh --qos=qos_di14',
        poll_interval=60,
    )