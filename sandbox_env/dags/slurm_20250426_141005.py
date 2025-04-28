"""
Auto-generated SLURM DAG (slurm_20250426_141005)
"""

from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from slurm_plugin.operators.slurm_operator import SubmitAndMonitorSlurmJobOperator

default_args = {
    'owner': 'data_scientist',
    'start_date': datetime(2025, 4, 26),
    'retries': 0
}

with DAG(
    dag_id="slurm_20250426_141005",
    default_args=default_args,
    schedule_interval="@once",
    catchup=False
) as dag:


    # 3. Submit SLURM job
    submit = SubmitAndMonitorSlurmJobOperator(
        task_id="submit_slurm",
        ssh_conn_id="hpc_ssh",
        script_path=(
            ""
            "--qos= "
            "example.sh"
            ""
        ).strip()
    )

