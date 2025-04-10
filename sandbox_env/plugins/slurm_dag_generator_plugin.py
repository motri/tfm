from airflow.plugins_manager import AirflowPlugin
from flask_appbuilder import BaseView
from flask import Blueprint, render_template, request
from airflow.www.app import csrf

# Optional: you can keep your original blueprint if needed for extra endpoints.
slurm_ui_blueprint = Blueprint(
    "slurm_ui", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/slurm-ui"
)

# Your previously defined route can remain if you like:
@slurm_ui_blueprint.route("/", methods=["GET", "POST"])
@csrf.exempt
def submit_form():
    if request.method == "POST":
        qos = request.form.get("qos")
        name = request.form.get("name")
        script = request.form.get("script")
        # Build the final sbatch argument string.
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

# Define your AppBuilder view
from flask_appbuilder import BaseView, expose

class SlurmConfigView(BaseView):
    default_view = "dag_config"

    @expose("/")
    def dag_config(self):
        return self.render_template("dag_form.html")

# Register the plugin, adding the custom view to the Admin section.
class SlurmUIPlugin(AirflowPlugin):
    name = "slurm_ui_plugin"
    flask_blueprints = [slurm_ui_blueprint]
    # This will add a new entry in the Admin dropdown
    appbuilder_views = [{
        "name": "SLURM DAG Config",
        "category": "Admin",
        "view": SlurmConfigView()
    }]
