# UI Integration Parameter Structure

## UI Organization

The UI for the Airflow plugin should be organized into logical sections that guide users through the workflow creation process. Below is a proposed structure for the UI integration of parameters:

## 1. Workflow General Configuration

### Basic Information
- `workflow_name`: Name for the entire workflow (used to generate DAG IDs)
- `workflow_description`: Description of the workflow purpose
- `workflow_tags`: Tags for categorizing the workflow
- `workflow_owner`: Owner of the workflow
- `workflow_email`: Email for notifications

### Scheduling
- `schedule_type`: Selection between "Scheduled" or "Manual Trigger"
- `schedule_interval`: Cron expression or preset (only if scheduled)
- `start_date`: Initial date for DAG scheduling
- `catchup`: Enable/disable catchup for missed runs

## 2. MinIO to HPC Transfer Configuration

### MinIO Connection
- Connection selector with options:
  - `use_existing_connection`: Boolean to use existing Airflow connection
  - `connection_id`: Dropdown of existing MinIO connections (if using existing)
  - Custom connection fields (if not using existing):
    - `minio_endpoint`
    - `minio_access_key`
    - `minio_secret_key`
    - `minio_secure`
    - `minio_region`

### HPC Connection
- Connection selector with options:
  - `use_existing_connection`: Boolean to use existing Airflow connection
  - `connection_id`: Dropdown of existing SSH connections (if using existing)
  - Custom connection fields (if not using existing):
    - `hpc_host`
    - `hpc_port`
    - `hpc_username`
    - `hpc_key_file` (file upload or path input)
    - `hpc_key_passphrase`

### File Selection
- `minio_bucket_name`: Dropdown populated from MinIO (if connection is valid)
- `minio_object_path`: Path input with directory browser option
- `file_filter_regex`: Text input with regex validation
- Preview button to show matching files

### Destination Configuration
- `hpc_destination_path`: Path input with directory browser option
- `preserve_directory_structure`: Toggle switch
- `overwrite_existing`: Toggle switch

### Transfer Options
- `transfer_concurrency`: Numeric input with reasonable limits
- `chunk_size`: Numeric input with unit selector (KB, MB, GB)
- `timeout`: Numeric input for seconds
- `retry_count`: Numeric input
- `retry_delay`: Numeric input for seconds

## 3. HPC Training Job Configuration

### HPC Connection
- Option to reuse connection from transfer step or configure new one
- Same fields as in transfer step if configuring new

### Sbatch Script
- Script configuration with options:
  - `sbatch_script_path`: Path input if using existing

### Training Configuration
- `training_script_path`: Path input with file browser option
- `data_path`: Path input with option to use transferred data path
- `model_output_path`: Path input
- `hyperparameters`: Key-value editor for parameter name and value pairs
- `environment_setup`: Multi-line text input for setup commands
- `pre_commands`: Multi-line text input
- `post_commands`: Multi-line text input


## 4. Workflow Dependencies

### DAG Dependencies
- Visual graph representation of the workflow
- Option to add additional steps or dependencies
- `trigger_rule` selector for each step

### Notification Settings
- `email_on_failure`: Email input
- `email_on_retry`: Toggle switch
- `on_success_callback`: Selection from predefined callbacks
- `on_failure_callback`: Selection from predefined callbacks

## 5. Advanced Options
- Collapsible section for advanced users
- All remaining parameters not covered in main sections
- Option to add custom parameters

## UI Components and Interactions

### Dynamic Form Elements
- Fields should appear/disappear based on selections (conditional rendering)
- Validation should happen in real-time where possible
- Tooltips should provide context and examples for each field

### Preview and Validation
- Preview button to show the generated DAG code
- Validation to check for missing or invalid parameters
- Warning for potential issues or best practice violations

### Template Testing
- Option to test the template with sample data
- Validation of Jinja syntax in the template

### Save and Deploy
- Save as draft option
- Deploy option to create the actual DAGs
- Version control for saved templates
