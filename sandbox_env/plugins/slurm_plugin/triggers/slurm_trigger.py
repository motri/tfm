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
            client.connect(conn.host, username=conn.login, password=conn.password)

            while True:
                stdin, stdout, stderr = client.exec_command(f"sacct --jobs={self.job_id} --format=State")
                output = stdout.read().decode()
                #RUNNING esto indica que aun esta en ejecucion, por lo tanto sleep
                if output == "RUNNING":
                    await asyncio.sleep(self.poll_interval)
                #COMPLETED esto indica que todos los procesos salieron con exit code 0 por lo que return
                if output == "COMPLETED":
                    yield TriggerEvent({"status": "success"})
                    return
                # todo lo demas, error
                else:
                    yield TriggerEvent({"status": "error", "message": str(e)})
        except Exception as e:
            yield TriggerEvent({"status": "error", "message": str(e)})
