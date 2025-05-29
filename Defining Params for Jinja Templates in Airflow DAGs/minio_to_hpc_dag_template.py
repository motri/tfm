# Jinja Template for MinIO to HPC Transfer DAG

```python
"""
MinIO to HPC File Transfer DAG
Generated from template for {{ workflow_name }}
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from airflow.hooks.base import BaseHook
import boto3
import paramiko
import os
import re
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
    description='Transfer files from MinIO to HPC for {{ workflow_name }}',
    schedule_interval='{{ schedule_interval | default("None") }}',
    start_date=datetime.fromisoformat('{{ start_date }}'),
    catchup={{ catchup | default(False) }},
    tags=['{{ workflow_tags | join("', '") }}'],
    max_active_runs={{ max_active_runs | default(1) }},
)

def transfer_files_from_minio_to_hpc(**kwargs):
    """
    Transfer files from MinIO to HPC system.
    """
    # MinIO connection setup
    {% if use_existing_connection %}
    conn = BaseHook.get_connection('{{ connection_id }}')
    minio_endpoint = conn.host
    minio_access_key = conn.login
    minio_secret_key = conn.password
    minio_secure = conn.extra_dejson.get('secure', {{ minio_secure | default(True) }})
    minio_region = conn.extra_dejson.get('region', '{{ minio_region | default("") }}')
    {% else %}
    minio_endpoint = '{{ minio_endpoint }}'
    minio_access_key = '{{ minio_access_key }}'
    minio_secret_key = '{{ minio_secret_key }}'
    minio_secure = {{ minio_secure | default(True) }}
    minio_region = '{{ minio_region | default("") }}'
    {% endif %}
    
    # MinIO client setup
    s3_client = boto3.client(
        's3',
        endpoint_url='http{% if minio_secure %}s{% endif %}://' + minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        region_name=minio_region if minio_region else None,
        use_ssl=minio_secure,
    )
    
    # HPC connection setup
    {% if use_existing_hpc_connection %}
    hpc_conn = BaseHook.get_connection('{{ hpc_connection_id }}')
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
    
    # File transfer parameters
    bucket_name = '{{ minio_bucket_name }}'
    object_path = '{{ minio_object_path }}'
    file_filter_regex = r'{{ file_filter_regex | default(".*") }}'
    hpc_destination_path = '{{ hpc_destination_path }}'
    preserve_directory_structure = {{ preserve_directory_structure | default(True) }}
    overwrite_existing = {{ overwrite_existing | default(False) }}
    
    # Execution parameters
    transfer_concurrency = {{ transfer_concurrency | default(5) }}
    chunk_size = {{ chunk_size | default(8) }} * 1024 * 1024  # Convert to bytes
    timeout = {{ timeout | default(3600) }}
    retry_count = {{ retry_count | default(3) }}
    retry_delay = {{ retry_delay | default(5) }}
    
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
        
        # Create SFTP client
        sftp_client = ssh_client.open_sftp()
        
        # Ensure destination directory exists
        mkdir_command = f"mkdir -p {hpc_destination_path}"
        stdin, stdout, stderr = ssh_client.exec_command(mkdir_command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error_message = stderr.read().decode('utf-8')
            raise Exception(f"Failed to create destination directory: {error_message}")
        
        # List objects in MinIO
        if object_path.endswith('/'):
            # List objects with prefix
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=object_path
            )
        else:
            # Get specific object
            try:
                s3_client.head_object(Bucket=bucket_name, Key=object_path)
                objects = [{'Key': object_path}]
                response = {'Contents': objects}
            except Exception as e:
                logging.error(f"Object {object_path} not found: {str(e)}")
                response = {'Contents': []}
        
        # Filter objects based on regex if provided
        filtered_objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if re.match(file_filter_regex, os.path.basename(key)):
                    filtered_objects.append(key)
        
        # Transfer files
        transferred_files = []
        for obj_key in filtered_objects:
            try:
                # Determine local temp file path and remote destination path
                local_temp_file = f"/tmp/{os.path.basename(obj_key)}"
                
                if preserve_directory_structure and object_path.endswith('/'):
                    # Calculate relative path
                    rel_path = obj_key[len(object_path):]
                    remote_path = os.path.join(hpc_destination_path, rel_path)
                    # Ensure remote directory exists
                    remote_dir = os.path.dirname(remote_path)
                    mkdir_command = f"mkdir -p {remote_dir}"
                    stdin, stdout, stderr = ssh_client.exec_command(mkdir_command)
                else:
                    remote_path = os.path.join(hpc_destination_path, os.path.basename(obj_key))
                
                # Check if file exists and handle overwrite flag
                if not overwrite_existing:
                    try:
                        sftp_client.stat(remote_path)
                        logging.info(f"File {remote_path} already exists, skipping")
                        continue
                    except FileNotFoundError:
                        pass
                
                # Download from MinIO to local temp
                s3_client.download_file(
                    Bucket=bucket_name,
                    Key=obj_key,
                    Filename=local_temp_file
                )
                
                # Upload to HPC
                sftp_client.put(local_temp_file, remote_path)
                
                # Clean up temp file
                os.remove(local_temp_file)
                
                transferred_files.append(remote_path)
                logging.info(f"Transferred {obj_key} to {remote_path}")
                
            except Exception as e:
                logging.error(f"Error transferring {obj_key}: {str(e)}")
                # Implement retry logic here if needed
        
        # Return the list of transferred files
        return {
            'transferred_files': transferred_files,
            'transfer_count': len(transferred_files),
            'destination_path': hpc_destination_path
        }
        
    finally:
        # Close connections
        if 'sftp_client' in locals():
            sftp_client.close()
        ssh_client.close()

# Task to transfer files
transfer_task = PythonOperator(
    task_id='transfer_files_from_minio_to_hpc',
    python_callable=transfer_files_from_minio_to_hpc,
    provide_context=True,
    dag=dag,
)

# Task to trigger the training DAG
trigger_training_dag = TriggerDagRunOperator(
    task_id='trigger_training_dag',
    trigger_dag_id='{{ trigger_dag_id }}',
    conf={'data_path': '{{ hpc_destination_path }}'},
    wait_for_completion={{ wait_for_completion | default(False) }},
    poke_interval={{ job_status_check_interval | default(60) }},
    dag=dag,
)

# Set task dependencies
transfer_task >> trigger_training_dag
```
