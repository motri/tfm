from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 3, 20),
}

# Define the DAG
with DAG(
    'slurm_sbatch_example',
    default_args=default_args,
    schedule_interval=None,  # Can set it to any cron schedule or None for manual trigger
    catchup=False,
) as dag:

    # Define the slurm sbatch command
    sbatch_command = """
    sbatch <<EOF
    #!/bin/bash
    #SBATCH -J Serial # Jobname
    #SBATCH --ntasks=1 # Processors
    #SBATCH --time=10:00 # Walltime
    #SBATCH --mem-per-cpu=10M # Memory/cpu
    #SBATCH --partition=slurmpar # Queue
    srun sleep 30
    srun echo "My first serial Slurm job
    EOF
    """

    # SSHOperator to execute the sbatch command on the remote SLURM server
    submit_sbatch_job = SSHOperator(
        task_id='submit_sbatch_job',
        ssh_conn_id='slurm_ssh_connection',  # You need to set up this SSH connection in Airflow
        command=sbatch_command,
        dag=dag
    )

    # You can add more tasks here if needed

    submit_sbatch_job
