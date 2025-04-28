
from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator

# Default args for the DAG
default_args = {
    'owner': 'data_scientist',
    'start_date': datetime(2025, 4, 28),
    'retries': 0
}

with DAG(
    dag_id="slurm_20250428_073538",
    default_args=default_args,
    schedule_interval="@once",
    catchup=False,
    tags=['c', 'Unai_test1']
) as dag:
    # Build the sbatch argument string

    # Task: Submit SLURM job with deferrable operator
    submit = SubmitAndMonitorSlurmJobOperator(
        task_id="submit_slurm",
        ssh_conn_id="hpc_ssh",
        sbatch_args="--qos=qos_di14 example_run.sh"
    )