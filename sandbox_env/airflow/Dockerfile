FROM apache/airflow:2.10.5

USER airflow
RUN pip install apache-airflow-providers-ssh
RUN pip install airflow-code-editor
USER airflow

COPY dags/slurm_test_job.py /opt/airflow/dags
COPY plugins/ /opt/airflow/plugins
COPY code/ /opt/airflow/code