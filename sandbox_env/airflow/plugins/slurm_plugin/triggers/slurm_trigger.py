from airflow.triggers.base import BaseTrigger, TriggerEvent
import asyncio
import paramiko
from airflow.hooks.base import BaseHook

class SlurmJobTrigger(BaseTrigger):
    def __init__(self, ssh_conn_id, job_id, poll_interval=60):
        super().__init__()
        self.ssh_conn_id = ssh_conn_id
        self.job_id = job_id
        self.poll_interval = poll_interval

    def serialize(self):
        return (
            "slurm_plugin.triggers.slurm_trigger.SlurmJobTrigger",
            {"ssh_conn_id": self.ssh_conn_id, "job_id": self.job_id, "poll_interval": self.poll_interval}
        )

    async def run(self):
        try:
            conn = BaseHook.get_connection(self.ssh_conn_id)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(conn.host, username=conn.login, key_filename=conn.extra_dejson.get("key_file"))

            while True:
                stdin, stdout, stderr = client.exec_command(f"squeue -j {self.job_id}")
                output = stdout.read().decode()

                if self.job_id not in output:
                    yield TriggerEvent({"status": "success"})
                    return
                await asyncio.sleep(self.poll_interval)
        except Exception as e:
            yield TriggerEvent({"status": "error", "message": str(e)})
