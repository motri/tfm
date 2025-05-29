# HPC Training Job (sbatch) DAG Parameters

## Connection Parameters

### HPC Connection
- `hpc_host`: Hostname or IP address of the HPC system
- `hpc_port`: SSH port for the HPC system (default: 22)
- `hpc_username`: Username for SSH authentication to HPC
- `hpc_key_file`: Path to SSH private key file or connection ID referencing a stored key
- `hpc_key_passphrase`: Optional passphrase for the SSH private key

## Sbatch Job Parameters

### Job Configuration
- `sbatch_script_path`: Path to the sbatch script on the HPC system or script content as a template
- `job_name`: Name for the sbatch job
- `partition`: HPC partition/queue to submit the job to
- `num_nodes`: Number of nodes to allocate
- `num_tasks`: Number of tasks to run
- `cpus_per_task`: Number of CPUs per task
- `memory_per_node`: Memory allocation per node (e.g., '32GB')
- `gpu_count`: Number of GPUs to allocate
- `gpu_type`: Type of GPU to request (if applicable)
- `time_limit`: Maximum runtime for the job (e.g., '24:00:00')
- `job_output_path`: Path for job output logs
- `job_error_path`: Path for job error logs

### Training Specific Parameters
- `training_script_path`: Path to the training script on HPC
- `data_path`: Path to the input data directory (should match with transferred data location)
- `model_output_path`: Path to save trained models
- `hyperparameters`: Dictionary of training hyperparameters (learning rate, batch size, etc.)
- `environment_setup`: Commands to set up the environment (module load, activate conda, etc.)
- `pre_commands`: Commands to run before the main training script
- `post_commands`: Commands to run after the main training script

## Execution Parameters
- `timeout`: Maximum time to wait for job submission (in seconds)
- `poll_interval`: Interval to check job status (in seconds)
- `wait_for_completion`: Boolean to wait for job completion or just submit
- `job_status_check_interval`: Interval to check job status if waiting for completion

## DAG Configuration
- `dag_id`: Unique identifier for the training DAG
- `schedule_interval`: Usually set to None for triggered DAGs
- `start_date`: Initial date for DAG scheduling
- `catchup`: Boolean to enable/disable catchup for missed runs (usually False for triggered DAGs)
- `tags`: List of tags for DAG organization
- `owner`: Owner of the DAG
- `email_on_failure`: Email address for failure notifications
- `email_on_retry`: Boolean to send email on retry attempts
- `retries`: Number of task retries
- `retry_delay`: Delay between task retries (in seconds)
- `max_active_runs`: Maximum number of active DAG runs

## Trigger Configuration
- `trigger_rule`: Rule for task triggering (e.g., all_success, all_done)
- `depends_on_past`: Boolean to make execution dependent on past runs
- `external_dag_id`: ID of the upstream DAG (MinIO transfer DAG)
- `external_task_id`: ID of the specific task in the upstream DAG to depend on
- `execution_delta`: Time delta for selecting the upstream DAG run
- `execution_date_fn`: Function to determine the execution date of the upstream DAG run

## Callback Parameters
- `on_success_callback`: Function to call when job completes successfully
- `on_failure_callback`: Function to call when job fails
- `on_retry_callback`: Function to call when job is retried
- `sla_miss_callback`: Function to call when SLA is missed
