from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime

default_args = {
    'owner': 'Unai Motriko',
    'start_date': datetime(2025, 6, 23),
}

with DAG(
    dag_id='Daige_step1_git_20250623T095733',
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

    

    
    trigger = TriggerDagRunOperator(
        task_id='trigger_Daige_step2_slurm_20250623T095733',
        trigger_dag_id='Daige_step2_slurm_20250623T095733'
    )
    
    git_clone >> trigger
    
    