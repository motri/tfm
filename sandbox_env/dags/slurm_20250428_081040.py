
from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator

default_args = {
    'owner': 'tezt_user',
    'start_date': datetime(2025, 4, 28),
    'retries': 0
}

with DAG(
    dag_id="slurm_20250428_081040",
    default_args=default_args,
    schedule_interval="@once",
    catchup=False,
    tags=['satelite']
) as dag:

    submit = SubmitAndMonitorSlurmJobOperator(
        task_id="submit_slurm",
        ssh_conn_id="hpc_ssh",
        sbatch_args="--qos=qos_di14 example_run.sh"
    )