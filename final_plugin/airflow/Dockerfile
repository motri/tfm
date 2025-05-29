FROM apache/airflow:2.10.5

USER root
RUN apt-get update \
 && apt-get install -y git \
 && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install apache-airflow-providers-ssh
RUN pip install apache-airflow-providers-amazon
RUN which git && git --version

# RUN pip install airflow-code-editor
USER airflow

