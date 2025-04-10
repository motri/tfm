import asyncio
import paramiko
from airflow.hooks.base import BaseHook
from airflow.triggers.base import BaseTrigger, TriggerEvent

class SlurmJobTrigger(BaseTrigger):
    def __init__(self, ssh_conn_id, job_id, poll_interval=60):
        super().__init__()
        self.ssh_conn_id = ssh_conn_id
        self.job_id = job_id
        self.poll_interval = poll_interval

    def serialize(self):
        return (
            "triggers.slurm_trigger.SlurmJobTrigger",
            {
                "ssh_conn_id": self.ssh_conn_id,
                "job_id": self.job_id,
                "poll_interval": self.poll_interval
            }
        )

    async def run(self):
        try:
            conn = BaseHook.get_connection(self.ssh_conn_id)

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=conn.host,
                username=conn.login,
                password=conn.password,
                key_filename=conn.extra_dejson.get("key_file", None)
            )

            while True:
                try:
                    stdin, stdout, stderr = client.exec_command(
                        f"sacct --parsable2 --noheader --jobs={self.job_id} --format=State"
                    )
                    output = stdout.read().decode().strip()
                    err_output = stderr.read().decode().strip()

                    if err_output:
                        yield TriggerEvent({"status": "error", "message": err_output})
                        return

                    self.log.info(f"[SLURM Trigger] sacct output:\n{output}")

                    states = {line.strip() for line in output.splitlines() if line.strip()}
                    #NOT sure about the first condition as it might just trigger infinitedely if no States in ouput,
                    #which would suggest it is somehow not in the queue, but if this keeps happening we need a 
                    #a circuit breaker 
                    if not states:
                        self.log.warning("No state returned for job %s; sleeping...", self.job_id)
                        await asyncio.sleep(self.poll_interval)
                        continue

                    if states <= {"RUNNING", "PENDING"}:
                        await asyncio.sleep(self.poll_interval)
                    elif "COMPLETED" in states:
                        yield TriggerEvent({"status": "success"})
                        return
                    else:
                        yield TriggerEvent({
                            "status": "error",
                            "message": f"SLURM job {self.job_id} ended with state(s): {', '.join(states)}"
                        })
                        return

                except Exception as poll_err:
                    yield TriggerEvent({"status": "error", "message": f"Polling error: {str(poll_err)}"})
                    return

        except Exception as conn_err:
            yield TriggerEvent({"status": "error", "message": f"SSH connection failed: {str(conn_err)}"})
        finally:
            try:
                client.close()
            except Exception:
                pass
