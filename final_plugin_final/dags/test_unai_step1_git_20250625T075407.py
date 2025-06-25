from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime

default_args = {
    'owner': 'Unai Motriko',
    'start_date': datetime(2025, 6, 25),
}

with DAG(
    dag_id='test_unai_step1_git_20250625T075407',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=[""],
) as dag:

    git_clone = BashOperator(
        task_id='git_clone',
        bash_command=(
            'git clone https://github.com/motri/hello-world /tmp/repo'
        )
    )

    
    scp_to_hpc = SSHOperator(
        task_id='scp_to_hpc',
        ssh_conn_id='hpc_ssh',
        command=(
            'scp -r /tmp/repo '
            'umotriko@10.75.0.21:.'
        )
    )
    git_clone >> scp_to_hpc
    

    
    trigger = TriggerDagRunOperator(
        task_id='trigger_test_unai_step2_slurm_20250625T075407',
        trigger_dag_id='test_unai_step2_slurm_20250625T075407'
    )
    
    scp_to_hpc >> trigger
    
    