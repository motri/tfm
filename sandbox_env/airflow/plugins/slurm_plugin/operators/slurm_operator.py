from airflow.models import BaseOperator
from airflow.triggers.base import TriggerEvent
from airflow.providers.ssh.hooks.ssh import SSHHook
from slurm_plugin.triggers.slurm_trigger import SlurmJobTrigger

class SubmitAndMonitorSlurmJobOperator(BaseOperator):
    def __init__(self, ssh_conn_id, script_path, poll_interval=60, **kwargs):
        super().__init__(**kwargs)
        self.ssh_conn_id = ssh_conn_id
        self.script_path = script_path
        self.poll_interval = poll_interval

    def execute(self, context):
        hook = SSHHook(ssh_conn_id=self.ssh_conn_id)
        with hook.get_conn() as ssh_client:
            stdin, stdout, stderr = ssh_client.exec_command(f"sbatch {self.script_path}")
            output = stdout.read().decode()
            self.log.info(f"sbatch output: {output}")
            job_id = output.strip().split()[-1]

        self.defer(
            trigger=SlurmJobTrigger(self.ssh_conn_id, job_id, self.poll_interval),
            method_name="execute_complete"
        )

    def execute_complete(self, context, event: TriggerEvent):
        if event.payload["status"] == "success":
            self.log.info("SLURM job completed.")
        else:
            raise Exception(f"SLURM job failed: {event.payload.get('message', 'Unknown error')}")
