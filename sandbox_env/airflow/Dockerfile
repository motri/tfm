FROM apache/airflow:2.5.1

USER root
RUN pip install apache-airflow-providers-ssh
USER airflow

COPY dags/ /opt/airflow/dags
COPY plugins/ /opt/airflow/plugins
COPY code/ /opt/airflow/code