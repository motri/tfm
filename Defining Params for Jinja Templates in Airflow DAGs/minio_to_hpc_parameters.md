# MinIO to HPC Transfer DAG Parameters

## Connection Parameters

### MinIO Connection
- `minio_endpoint`: URL endpoint for the MinIO server (e.g., `minio.example.com:9000`)
- `minio_access_key`: Access key for MinIO authentication
- `minio_secret_key`: Secret key for MinIO authentication
- `minio_secure`: Boolean flag to use HTTPS (true) or HTTP (false)
- `minio_region`: Optional region parameter for MinIO

### HPC Connection
- `hpc_host`: Hostname or IP address of the HPC system
- `hpc_port`: SSH port for the HPC system (default: 22)
- `hpc_username`: Username for SSH authentication to HPC
- `hpc_key_file`: Path to SSH private key file or connection ID referencing a stored key
- `hpc_key_passphrase`: Optional passphrase for the SSH private key

## File Transfer Parameters

### Source Configuration
- `minio_bucket_name`: Name of the MinIO bucket containing the files
- `minio_object_path`: Path to the object(s) within the bucket (supports wildcards)
- `file_filter_regex`: Optional regex pattern to filter files

### Destination Configuration
- `hpc_destination_path`: Target directory path on the HPC system
- `preserve_directory_structure`: Boolean to maintain directory structure from MinIO
- `overwrite_existing`: Boolean to control overwriting existing files

## Execution Parameters
- `transfer_concurrency`: Number of concurrent file transfers
- `chunk_size`: Size of chunks for large file transfers (in MB)
- `timeout`: Maximum time allowed for the transfer operation (in seconds)
- `retry_count`: Number of retry attempts for failed transfers
- `retry_delay`: Delay between retry attempts (in seconds)

## DAG Configuration
- `dag_id`: Unique identifier for the transfer DAG
- `schedule_interval`: Cron expression or preset for scheduling
- `start_date`: Initial date for DAG scheduling
- `catchup`: Boolean to enable/disable catchup for missed runs
- `tags`: List of tags for DAG organization
- `owner`: Owner of the DAG
- `email_on_failure`: Email address for failure notifications
- `email_on_retry`: Boolean to send email on retry attempts
- `retries`: Number of task retries
- `retry_delay`: Delay between task retries (in seconds)
- `max_active_runs`: Maximum number of active DAG runs

## Trigger Configuration
- `trigger_rule`: Rule for downstream task triggering (e.g., all_success, all_done)
- `depends_on_past`: Boolean to make execution dependent on past runs
- `wait_for_downstream`: Boolean to wait for downstream tasks
- `trigger_dag_id`: ID of the DAG to trigger after completion (training DAG)
