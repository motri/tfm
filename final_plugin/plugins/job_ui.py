from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint
from flask_appbuilder import BaseView, expose
from airflow.models import XCom
from airflow.settings import Session

bp = Blueprint(
    "job_ui",
    __name__,
    template_folder="templates",
    url_prefix="/job-ui"
)


class SlurmDashboardView(BaseView):
    default_view = "dashboard"

    @expose('/')
    def dashboard(self):
        session = Session()

        job_xcoms = (
            session.query(XCom)
                   .filter(XCom.key == "slurm_job_id")
                   .order_by(XCom.timestamp.desc())
                   .all()
        )

        executions = []
        for x in job_xcoms:
            alias = (
                session.query(XCom)
                       .filter_by(
                           key="job_alias",
                           dag_id=x.dag_id,
                           task_id=x.task_id,
                           run_id=x.run_id
                       )
                       .first()
            )
            status = (
                session.query(XCom)
                       .filter_by(
                           key="slurm_status",
                           dag_id=x.dag_id,
                           task_id=x.task_id,
                           run_id=x.run_id
                       )
                       .first()
            )

            executions.append({
                "alias":    alias.value if alias else None,
                "dag_id":   x.dag_id,
                "run_id":   x.run_id,
                "task_id":  x.task_id,
                "job_id":   x.value,
                "status":   status.value if status else None,
            })

        return self.render_template(
            "slurm_dashboard.html",
            executions=executions
        )

class SlurmUIPlugin(AirflowPlugin):
    name = "slurm_ui_plugin",
    flask_blueprints = [bp]
    appbuilder_views = [{
        "name":     "SLURM Dashboard",
        "category": "SLURM",
        "view":     SlurmDashboardView()
    }]
