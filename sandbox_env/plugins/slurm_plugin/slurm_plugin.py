from airflow.plugins_manager import AirflowPlugin
from slurm_plugin.operators.slurm_operator import SubmitAndMonitorSlurmJobOperator
from slurm_plugin.triggers.slurm_trigger import SlurmJobTrigger
import sys

class SlurmAirflowPlugin(AirflowPlugin):
    print("pythonpath:", sys.path )
    name = "slurm_plugin"
    operators = [SubmitAndMonitorSlurmJobOperator]
    triggers = [SlurmJobTrigger]
