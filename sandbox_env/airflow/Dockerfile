FROM apache/airflow:2.10.5

USER airflow
RUN pip install apache-airflow-providers-ssh
USER airflow

COPY dags/ /opt/airflow/dags
COPY plugins/ /opt/airflow/plugins
COPY code/ /opt/airflow/code