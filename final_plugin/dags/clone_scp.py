from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 6, 19),
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id="clone_and_scp_hello_world",
    default_args=default_args,
    start_date=datetime(2025, 6, 19),
    schedule_interval=None,
    catchup=False,
    tags=["example", "slurm", "git", "scp"],
) as dag:

    clone_task = BashOperator(
        task_id="git_clone",
        bash_command=(
            'git clone '
            ''
            'https://github.com/motri/hello-world /tmp/repo/'
        )
    )
# 2. SCP the repo to remote using SSHOperator
    scp_command = """
    scp -r -o StrictHostKeyChecking=no /tmp/repo {{ conn.my_ssh_connection.login }}@{{ conn.my_ssh_connection.host }}:/home/{{ conn.my_ssh_connection.login }}/
    """

    scp_task = SSHOperator(
        task_id='scp_repo_to_remote',
        ssh_conn_id='hpc_ssh',
        command=scp_command)

    clone_task >> scp_task
