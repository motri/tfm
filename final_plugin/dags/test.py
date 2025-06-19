from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.sftp.operators.sftp import SFTPOperator
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
}

with DAG(
    dag_id="git_clone_and_scp_hello_world",
    default_args=default_args,
    start_date=datetime(2025, 6, 19),
    schedule_interval=None,
    catchup=False,
    tags=["example", "slurm", "git", "scp"],
) as dag:

    # 1) Clonar o actualizar el repo en /tmp/hello-world
    git_clone = BashOperator(
        task_id="git_clone",
        bash_command=(
            'git clone '
            ''
            'https://github.com/motri/hello-world /tmp/repo/'
        )
    )

    # 2) Copiar con SFTP al HPC usando la conexión 'hpc_ssh'
    scp_to_hpc = SFTPOperator(
        task_id="scp_to_hpc",
        ssh_conn_id="hpc_ssh",
        local_filepath="/tmp/repo",
        remote_filepath=".",  
        operation="put",
        create_intermediate_dirs=True
    )

    git_clone >> scp_to_hpc
