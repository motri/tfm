import json
from flask import Blueprint, render_template, request, jsonify
from flask_appbuilder import BaseView, expose
from airflow.plugins_manager import AirflowPlugin
from airflow.www.app import csrf
from airflow.models import DagRun, TaskInstance
from airflow.utils.state import State
from airflow.settings import Session

# Blueprint
slurm_ui_bp = Blueprint(
    "slurm_ui", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/slurm-ui"
)

@slurm_ui_bp.route("/status/<dag_id>/<task_id>")
@csrf.exempt
def slurm_status(dag_id, task_id):
    session = Session()
    # 1) Encontrar último DagRun para dag_id
    dr = session.query(DagRun)\
                .filter(DagRun.dag_id == dag_id)\
                .order_by(DagRun.execution_date.desc())\
                .first()
    if not dr:
        return jsonify(error="DagRun not found"), 404

    # 2) Encontrar TaskInstance
    ti = session.query(TaskInstance)\
                .filter_by(dag_id=dag_id, run_id=dr.run_id, task_id=task_id)\
                .first()
    if not ti:
        return jsonify(error="TaskInstance not found"), 404

    # 3) Leer XComs
    alias  = ti.xcom_pull(task_ids=task_id, key="job_alias")
    job_id = ti.xcom_pull(task_ids=task_id, key="slurm_job_id")
    status = ti.xcom_pull(task_ids=task_id, key="slurm_status")

    return jsonify({
        "dag_id":     dag_id,
        "task_id":    task_id,
        "run_id":     dr.run_id,
        "alias":      alias,
        "job_id":     job_id,
        "status":     status
    }), 200

# AppBuilder view
class SlurmMonitorView(BaseView):
    default_view = "monitor"

    @expose("/monitor")
    def monitor(self):
        # opcional: pasar una lista predefinida de dag/task a la plantilla
        return render_template("slurm_monitor.html")

class SlurmUIPlugin(AirflowPlugin):
    name = "slurm_ui_plugin"
    flask_blueprints = [slurm_ui_bp]
    appbuilder_views = [{
        "name": "Monitor SLURM Jobs",
        "category": "SLURM",
        "view": SlurmMonitorView()
    }]
