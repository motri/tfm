from airflow.plugins_manager import AirflowPlugin
from operators.slurm_operator import SubmitAndMonitorSlurmJobOperator
from triggers.slurm_trigger import SlurmJobTrigger

class SlurmAirflowPlugin(AirflowPlugin):
    name = "slurm_plugin"
    operators = [SubmitAndMonitorSlurmJobOperator]
    triggers = [SlurmJobTrigger]
