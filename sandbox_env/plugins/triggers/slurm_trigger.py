from airflow.triggers.base import BaseTrigger, TriggerEvent
from airflow.providers.ssh.hooks.ssh import SSHHook
import asyncio

class SlurmJobTrigger(BaseTrigger):
    """
    Trigger que hace polling de sacct para un job SLURM dado.
    Emite un evento por cada cambio de estado, incluyendo un flag 'final'.
    """
    def __init__(self, ssh_conn_id: str, job_id: str, poll_interval: int = 30):
        super().__init__()
        self.ssh_conn_id   = ssh_conn_id
        self.job_id        = job_id
        self.poll_interval = poll_interval

    def serialize(self):
        return (
            "slurm_trigger.SlurmJobTrigger",
            {
                "ssh_conn_id": self.ssh_conn_id,
                "job_id": self.job_id,
                "poll_interval": self.poll_interval,
            }
        )

    async def run(self):
        ssh_hook = SSHHook(ssh_conn_id=self.ssh_conn_id)
        client   = ssh_hook.get_conn()

        while True:
            stdin, stdout, stderr = client.exec_command(
                f"sacct --jobs={self.job_id} --format=State"
            )
            output = stdout.read().decode().strip()
            err_output = stderr.read().decode().strip()

            self.log.info(f"[SLURM Trigger] sacct output:\n{output}")

            states = {line.strip() for line in output.splitlines() if line.strip()}

            if not states:
                self.log.warning("No state returned for job %s; sleeping...", self.job_id)
                await asyncio.sleep(self.poll_interval)
                state, final = "AWAITING", True

            elif "COMPLETED" in output:
                state, final = "COMPLETED", True
            elif "RUNNING" in output:
                state, final = "RUNNING", False
            elif "PENDING" in output:
                state, final = "PENDING", False
            else:
                state, final = "ERROR", True
                self.log.error(f"Run failed due to: {err_output}")

            yield TriggerEvent({
                "job_id": self.job_id,
                "status": state,
                "final":  final,
            })

            if final:
                return

            await asyncio.sleep(self.poll_interval)
