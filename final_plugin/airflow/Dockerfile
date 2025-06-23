FROM apache/airflow:2.10.5

USER root
RUN apt-get update \
 && apt-get install -y git \
 && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install apache-airflow-providers-ssh
RUN pip install apache-airflow-providers-amazon
RUN which git && git --version

# Switch to root to install system packages
USER root

# Install git and cleanup
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# RUN pip install airflow-code-editor
USER airflow

