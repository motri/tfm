from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.models import Variable
from datetime import datetime



default_args = {
    'owner': p.get('workflow_owner', 'airflow'),
    'start_date': datetime(2025, 6, 23),
}


with DAG(
    dag_id='test_unai_step1_git_20250623T085043',
    default_args=default_args,
    schedule_interval="@daily",
    catchup=p.get('catchup', False),
    tags=[""],
) as dag:

    git_clone = BashOperator(
        task_id='git_clone',
        bash_command=(
            'git clone '
            ''
            'https://github.com/motri/hello-world '
            ''
        )
    )

    

    