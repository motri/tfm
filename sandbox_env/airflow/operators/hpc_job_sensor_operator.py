from airflow.models import BaseOperator
from airflow.triggers.base import BaseTrigger, TriggerEvent
from airflow.utils.context import Context

class HPCJobSensorOperator(BaseOperator):
    def __init__(self, job_id, ssh_conn_id, poll_interval=60, **kwargs):
        super().__init__(**kwargs)
        self.job_id = job_id
        self.ssh_conn_id = ssh_conn_id
        self.poll_interval = poll_interval

    def execute(self, context:Context):
        self.defer(trigger=T)

