from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint, request, redirect, url_for, flash
from airflow.www.app import csrf
from flask_appbuilder import BaseView, expose
from airflow.models import Variable
from dag_generator import generate_dag_file
from datetime import datetime
import os

# Blueprint to handle form GET/POST
slurm_ui = Blueprint(
    "slurm_ui", __name__,
    template_folder="templates",
    url_prefix="/slurm-ui"
)

@slurm_ui.route("/dag", methods=["GET", "POST"])
@csrf.exempt
def submit_form():
    if request.method == "POST":
        # collect inputs
        download = request.form.get("download") == "true"
        repo_type = request.form.get("repo_type")
        repo_url = request.form.get("repo_url")
        script = request.form["script"]
        qos = request.form.get("qos", "").strip()
        job_name = request.form.get("job_name", "").strip()
        dag_tags = request.form.get("dag_tags", "").strip()
        ssh_conn = request.form.get("ssh_conn", "").strip()

        # build params
        now = datetime.now()
        dag_id = f"slurm_{now.strftime('%Y%m%d_%H%M%S')}"
        params = {
            "owner": "data_scientist",
            "year": now.year, "month": now.month, "day": now.day,
            "dag_id": dag_id,
            "schedule_interval": "@once",
            "download": download,
            "repo_type": repo_type,
            "repo_url": repo_url,
            "script": script,
            "qos": qos,
            "job_name": job_name,
            "dag_tags": dag_tags,
            "ssh_conn": ssh_conn
        }

        # generate DAG file
        dag_folder = os.environ.get("AIRFLOW__CORE__DAGS_FOLDER", "/opt/airflow/dags")
        try:
            path = generate_dag_file(params, dag_folder)
            flash(f"DAG generated: {path}", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")

        return redirect(url_for("SlurmConfigView.dag_config"))

    return render_template("dag_form.html")


# AppBuilder view to hook into Admin menu
class SlurmConfigView(BaseView):
    default_view = "dag_config"

    @expose("/dag-config", methods=["GET"])
    def dag_config(self):
        return self.render_template("dag_form.html")


class SlurmUIGeneratorPlugin(AirflowPlugin):
    name = "slurm_ui_generator"
    flask_blueprints = [slurm_ui]
    appbuilder_views = [{
        "name": "Generate SLURM DAG",
        "category": "Admin",
        "view": SlurmConfigView()
    }]
