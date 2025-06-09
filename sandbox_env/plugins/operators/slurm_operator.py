import os
from airflow.models import BaseOperator
from airflow.providers.ssh.hooks.ssh import SSHHook
from airflow.exceptions import TaskDeferred
from triggers.slurm_trigger import SlurmJobTrigger

class SubmitAndMonitorSlurmJobOperator(BaseOperator):
    """
    Operator diferido que envía un sbatch y monitoriza el job SLURM
    publicando cada estado en XCom bajo la clave 'slurm_status'
    y guarda el 'slurm_job_id' en XCom.
    """
    def __init__(
        self,
        *,
        ssh_conn_id: str,
        sbatch_args: str,
        job_alias: str = None,
        poll_interval: int = 30,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.ssh_conn_id   = ssh_conn_id
        self.sbatch_args   = sbatch_args
        self.job_alias     = job_alias
        self.poll_interval = poll_interval

    def execute(self, context):
        ti = context["ti"]
        ssh_hook = SSHHook(ssh_conn_id=self.ssh_conn_id)
        client   = ssh_hook.get_conn()

        # 1) Enviar sbatch
        stdin, stdout, stderr = client.exec_command(f"sbatch {self.sbatch_args}")
        output = stdout.read().decode().strip()
        job_id = output.split()[-1]
        self.log.info(f"Submitted SLURM job {job_id}: {output}")

        # 2) Guardar alias y job_id en XCom
        if self.job_alias:
            ti.xcom_push(key="job_alias", value=self.job_alias)
        ti.xcom_push(key="slurm_job_id", value=job_id)

        # 3) Deferir al trigger
        raise TaskDeferred(
            trigger=SlurmJobTrigger(
                ssh_conn_id=self.ssh_conn_id,
                job_id=job_id,
                poll_interval=self.poll_interval
            ),
            method_name="execute_complete"
        )

    def execute_complete(self, context, event: dict):
        ti     = context["ti"]
        status = event["status"]
        final  = event["final"]

        # 4) Publicar cada estado en XCom
        ti.xcom_push(key="slurm_status", value=status)

        # 5) Si no es estado final, deferir de nuevo
        if not final:
            raise TaskDeferred(
                trigger=SlurmJobTrigger(
                    ssh_conn_id=self.ssh_conn_id,
                    job_id=event["job_id"],
                    poll_interval=self.poll_interval
                ),
                method_name="execute_complete"
            )

        # 6) Final: SUCCESS or error
        if status == "COMPLETED":
            self.log.info(f"SLURM job {event['job_id']} COMPLETED")
            return "SUCCESS"
        else:
            raise RuntimeError(f"SLURM job {event['job_id']} ended with status {status}")
