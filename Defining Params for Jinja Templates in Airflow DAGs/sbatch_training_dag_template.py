# Jinja Template for HPC Training Job (sbatch) DAG

```python
"""
HPC Training Job (sbatch) DAG
Generated from template for {{ workflow_name }}
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.models import Variable
from airflow.hooks.base import BaseHook
import paramiko
import time
import json
import logging

# Default arguments
default_args = {
    'owner': '{{ workflow_owner }}',
    'depends_on_past': {{ depends_on_past | default(False) }},
    'email': ['{{ workflow_email }}'],
    'email_on_failure': {{ email_on_failure | default(True) }},
    'email_on_retry': {{ email_on_retry | default(False) }},
    'retries': {{ retries | default(1) }},
    'retry_delay': timedelta(seconds={{ retry_delay | default(300) }}),
}

# DAG definition
dag = DAG(
    '{{ dag_id }}',
    default_args=default_args,
    description='Run training job on HPC using sbatch for {{ workflow_name }}',
    schedule_interval=None,  # Triggered by upstream DAG
    start_date=datetime.fromisoformat('{{ start_date }}'),
    catchup={{ catchup | default(False) }},
    tags=['{{ workflow_tags | join("', '") }}'],
    max_active_runs={{ max_active_runs | default(1) }},
)

# Sensor to wait for the upstream MinIO transfer DAG
wait_for_transfer = ExternalTaskSensor(
    task_id='wait_for_minio_transfer',
    external_dag_id='{{ external_dag_id }}',
    external_task_id='transfer_files_from_minio_to_hpc',
    allowed_states=['success'],
    execution_delta={{ execution_delta | default("None") }},
    execution_date_fn={{ execution_date_fn | default("None") }},
    mode='poke',
    poke_interval={{ poke_interval | default(60) }},
    timeout={{ sensor_timeout | default(3600) }},
    dag=dag,
)

def submit_sbatch_job(**kwargs):
    """
    Submit sbatch job to HPC system and optionally wait for completion.
    """
    # Get data path from trigger configuration if available
    ti = kwargs['ti']
    dag_run = kwargs['dag_run']
    data_path = dag_run.conf.get('data_path', '{{ data_path }}')
    
    # HPC connection setup
    {% if use_existing_connection %}
    hpc_conn = BaseHook.get_connection('{{ connection_id }}')
    hpc_host = hpc_conn.host
    hpc_port = hpc_conn.port or 22
    hpc_username = hpc_conn.login
    hpc_key_file = hpc_conn.extra_dejson.get('key_file')
    hpc_key_passphrase = hpc_conn.password
    {% else %}
    hpc_host = '{{ hpc_host }}'
    hpc_port = {{ hpc_port | default(22) }}
    hpc_username = '{{ hpc_username }}'
    hpc_key_file = '{{ hpc_key_file }}'
    hpc_key_passphrase = '{{ hpc_key_passphrase | default("") }}'
    {% endif %}
    
    # Sbatch job parameters
    {% if use_existing_script %}
    sbatch_script_path = '{{ sbatch_script_path }}'
    {% else %}
    # Generate sbatch script content
    sbatch_script_content = """#!/bin/bash
#SBATCH --job-name={{ job_name }}
#SBATCH --partition={{ partition }}
#SBATCH --nodes={{ num_nodes | default(1) }}
#SBATCH --ntasks={{ num_tasks | default(1) }}
#SBATCH --cpus-per-task={{ cpus_per_task | default(1) }}
#SBATCH --mem={{ memory_per_node | default("32G") }}
{% if gpu_count %}#SBATCH --gres=gpu:{{ gpu_type | default("") }}:{{ gpu_count }}{% endif %}
#SBATCH --time={{ time_limit | default("24:00:00") }}
#SBATCH --output={{ job_output_path | default("slurm-%j.out") }}
#SBATCH --error={{ job_error_path | default("slurm-%j.err") }}

# Environment setup
{{ environment_setup }}

# Pre-commands
{{ pre_commands }}

# Main training command
cd $(dirname {{ training_script_path }})
python {{ training_script_path | basename }} \\
    --data_path={{ data_path }} \\
    --output_path={{ model_output_path }} \\
{% for param_name, param_value in hyperparameters.items() %}
    --{{ param_name }}={{ param_value }} {% if not loop.last %}\\{% endif %}
{% endfor %}

# Post-commands
{{ post_commands }}
"""
    {% endif %}
    
    # Execution parameters
    timeout = {{ timeout | default(3600) }}
    wait_for_completion = {{ wait_for_completion | default(False) }}
    job_status_check_interval = {{ job_status_check_interval | default(60) }}
    
    # SSH client setup
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to HPC
        if hpc_key_file:
            private_key = paramiko.RSAKey.from_private_key_file(
                hpc_key_file, 
                password=hpc_key_passphrase if hpc_key_passphrase else None
            )
            ssh_client.connect(
                hostname=hpc_host,
                port=hpc_port,
                username=hpc_username,
                pkey=private_key,
                timeout=timeout
            )
        else:
            # Fallback to password authentication if needed
            ssh_client.connect(
                hostname=hpc_host,
                port=hpc_port,
                username=hpc_username,
                timeout=timeout
            )
        
        {% if not use_existing_script %}
        # Create temporary script file on HPC
        sftp_client = ssh_client.open_sftp()
        temp_script_path = f"/tmp/sbatch_script_{dag_run.run_id}.sh"
        with sftp_client.open(temp_script_path, 'w') as f:
            f.write(sbatch_script_content)
        
        # Make script executable
        chmod_command = f"chmod +x {temp_script_path}"
        stdin, stdout, stderr = ssh_client.exec_command(chmod_command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_message = stderr.read().decode('utf-8')
            raise Exception(f"Failed to make script executable: {error_message}")
        
        # Use the temporary script
        sbatch_script_path = temp_script_path
        {% endif %}
        
        # Submit job
        submit_command = f"sbatch {sbatch_script_path}"
        stdin, stdout, stderr = ssh_client.exec_command(submit_command)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error_message = stderr.read().decode('utf-8')
            raise Exception(f"Failed to submit job: {error_message}")
        
        # Parse job ID from sbatch output
        sbatch_output = stdout.read().decode('utf-8').strip()
        job_id = None
        if "Submitted batch job" in sbatch_output:
            job_id = sbatch_output.split()[-1]
            logging.info(f"Submitted batch job with ID: {job_id}")
        else:
            raise Exception(f"Failed to parse job ID from output: {sbatch_output}")
        
        # Wait for job completion if requested
        job_status = "SUBMITTED"
        if wait_for_completion and job_id:
            start_time = time.time()
            while True:
                # Check if timeout exceeded
                if time.time() - start_time > timeout:
                    logging.warning(f"Timeout exceeded while waiting for job {job_id}")
                    break
                
                # Check job status
                status_command = f"sacct -j {job_id} --format=State --noheader --parsable2"
                stdin, stdout, stderr = ssh_client.exec_command(status_command)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_message = stderr.read().decode('utf-8')
                    logging.warning(f"Failed to check job status: {error_message}")
                else:
                    status_output = stdout.read().decode('utf-8').strip()
                    if status_output:
                        job_status = status_output.split('\n')[0]
                        logging.info(f"Job {job_id} status: {job_status}")
                        
                        # Check if job completed
                        if job_status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
                            break
                
                # Wait before checking again
                time.sleep(job_status_check_interval)
        
        # Return job information
        return {
            'job_id': job_id,
            'job_status': job_status,
            'script_path': sbatch_script_path,
            'data_path': data_path,
            'model_output_path': '{{ model_output_path }}'
        }
        
    finally:
        # Close connections
        if 'sftp_client' in locals():
            sftp_client.close()
        ssh_client.close()

# Task to submit sbatch job
submit_job_task = PythonOperator(
    task_id='submit_sbatch_job',
    python_callable=submit_sbatch_job,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
wait_for_transfer >> submit_job_task

{% if on_success_callback or on_failure_callback %}
# Add callback tasks if specified
{% if on_success_callback %}
def success_callback(**kwargs):
    """Success callback function"""
    ti = kwargs['ti']
    job_result = ti.xcom_pull(task_ids='submit_sbatch_job')
    # Implement success callback logic here
    logging.info(f"Job completed successfully: {job_result}")
    
success_task = PythonOperator(
    task_id='success_callback',
    python_callable=success_callback,
    provide_context=True,
    trigger_rule='all_success',
    dag=dag,
)

submit_job_task >> success_task
{% endif %}

{% if on_failure_callback %}
def failure_callback(**kwargs):
    """Failure callback function"""
    ti = kwargs['ti']
    job_result = ti.xcom_pull(task_ids='submit_sbatch_job')
    # Implement failure callback logic here
    logging.info(f"Job failed: {job_result}")
    
failure_task = PythonOperator(
    task_id='failure_callback',
    python_callable=failure_callback,
    provide_context=True,
    trigger_rule='all_failed',
    dag=dag,
)

submit_job_task >> failure_task
{% endif %}
{% endif %}
```
