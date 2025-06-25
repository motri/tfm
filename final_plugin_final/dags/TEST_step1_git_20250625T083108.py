from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
from helpers.transfer import transfer_repo_to_hpc

default_args = {
    'owner': 'Unai Motriko',
    'start_date': datetime(2025, 6, 25),
}

with DAG(
    dag_id='TEST_step1_git_20250625T083108',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=[""],
) as dag:

    git_clone = BashOperator(
        task_id='git_clone',
        bash_command=(
            'rm -rf /tmp/repo && '
            'git clone https://github.com/motri/hello-world /tmp/repo'
        )
    )

    
    scp_to_hpc = PythonOperator(
        task_id='scp_to_hpc',
        python_callable=transfer_repo_to_hpc,
        op_kwargs={
            'ssh_conn_id': 'hpc_ssh',
            'local_path': '/tmp/repo',
            'remote_path': '.',
        }
    )
    git_clone >> scp_to_hpc
    

    
    trigger = TriggerDagRunOperator(
        task_id='trigger_TEST_step2_slurm_20250625T083108',
        trigger_dag_id='TEST_step2_slurm_20250625T083108'
    )
    
    scp_to_hpc >> trigger
    
    