from airflow.plugins_manager import AirflowPlugin
from flask_appbuilder import BaseView
from flask import Blueprint, render_template, request
from airflow.www.app import csrf

slurm_ui_blueprint = Blueprint(
    "slurm_ui", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/slurm-ui"
)

@slurm_ui_blueprint.route("/generator", methods=["GET", "POST"])
@csrf.exempt
def submit_form():
    if request.method == "POST":
        qos = request.form.get("qos")
        name = request.form.get("name")
        script = request.form.get("script")
        sbatch_args_parts = []
        if qos:
            sbatch_args_parts.append(f"--qos={qos}")
        if name:
            sbatch_args_parts.append(f"--job-name={name}")
        sbatch_args_parts.append(script)
        sbatch_args = " ".join(sbatch_args_parts)
        
        # Optionally, store this in a variable or process as needed.
        from airflow.models import Variable
        Variable.set("slurm_dag_params", {"sbatch_args": sbatch_args})
        
        return f"Generated sbatch args: {sbatch_args}"
    return render_template("dag_form.html")

from flask_appbuilder import BaseView, expose

class SlurmConfigView(BaseView):
    default_view = "dag_config"

    @expose("/")
    def dag_config(self):
        return self.render_template("dag_form.html")

class SlurmUIPlugin(AirflowPlugin):
    name = "slurm_ui_plugin"
    flask_blueprints = [slurm_ui_blueprint]

    appbuilder_views = [{
        "name": "SLURM DAG Generator",
        "category": "Admin",
        "view": SlurmConfigView()
    }]
