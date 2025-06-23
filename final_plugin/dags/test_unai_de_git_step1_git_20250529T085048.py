from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(
    dag_id="safe_git_clone",
    start_date=datetime(2025, 6, 19),
    schedule_interval=None,
    catchup=False,
)

repo_url = "https://github.com/motri/hello-world"
clone_path = "/tmp/repo/"  # shared path

git_clone = BashOperator(
    task_id="git_clone",
    bash_command=f"""
        rm -rf {clone_path} && \
        git clone {repo_url} {clone_path} && \
        ls -l {clone_path}
    """,
    dag=dag
)
