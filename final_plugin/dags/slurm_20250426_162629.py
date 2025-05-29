
from airflow import DAG
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator

# Default args for the DAG
default_args = {
    'owner': 'data_scientist',
    'start_date': datetime(2025, 4, 26),
    'retries': 0
}

with DAG(
    dag_id="slurm_20250426_162629",
    default_args=default_args,
    schedule_interval="@once",
    catchup=False,
    tags=['Generated', 'test_1']
) as dag:    # Task: Clone the repository from github
    clone = BashOperator(
        task_id="clone_repo",
        bash_command="git clone https://github.com/motri/tfm /tmp/slurm_20250426_162629_repo"
    )

    # Task: Copy the script to HPC workspace
    copy_script = SSHOperator(
        task_id="copy_to_hpc",
        ssh_conn_id="hpc_ssh",
        command="scp /tmp/slurm_20250426_162629_repo/ user@hpc:/workspace/"
    )
    # Build the sbatch argument string

    # Task: Submit SLURM job with deferrable operator
    submit = SubmitAndMonitorSlurmJobOperator(
        task_id="submit_slurm",
        ssh_conn_id="hpc_ssh",
        sbatch_args="--qos=qos_di14 /workspace/"
    )    
    clone >> copy_script >> submit