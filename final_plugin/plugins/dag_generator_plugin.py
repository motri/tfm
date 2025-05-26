import json, os, datetime
from flask import (
    Blueprint, render_template, request, session,
    flash, redirect, url_for, current_app
)
from flask_appbuilder import BaseView, expose
from airflow.plugins_manager import AirflowPlugin
from airflow.www.app import csrf
from airflow.www.app import app as flask_app
from airflow.models import Connection
from airflow.settings import Session
from airflow.configuration import conf


def conn_list(conn_type: str):
    sess = Session()
    try:
        ct = conn_type.lower()
        if ct in ("minio", "s3"):
            rows = sess.query(Connection).filter(Connection.conn_type.ilike("s3")).all()
        elif ct == "ssh":
            rows = sess.query(Connection).filter(Connection.conn_type == "ssh").all()
        else:
            rows = sess.query(Connection).all()
        return [c.conn_id for c in rows]
    finally:
        sess.close()

# ────────────────────────────────────────────────────────────────────────────
# 1) THE BLUEPRINT: serves builder & configure pages, static files, templates,
#    and injects base_template + appbuilder into every render.
# ─────────────────────────────────────────────────────────────────────────────
dag_generator_bp = Blueprint(
    "dag_generator",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/dag-generator"
)

@dag_generator_bp.context_processor
def _inject_base_and_appbuilder():
    return {
        "base_template": current_app.appbuilder.base_template,
        "appbuilder":   current_app.appbuilder
    }

@dag_generator_bp.route("/builder", methods=["GET"])
def show_builder():
    return render_template("builder.html")

@dag_generator_bp.route("/configure", methods=["POST","GET"])
@csrf.exempt
def configure_workflow():
    if request.method == "POST" and "workflow" in request.form:
        session["workflow_steps"] = request.form["workflow"]
        return redirect(url_for("dag_generator.configure_workflow"))

    steps_json = session.get("workflow_steps")
    if not steps_json:
        flash("Please define workflow steps first.", "warning")
        return redirect(url_for("dag_generator.show_builder"))

    steps = json.loads(steps_json)
    # Pass conn_list into the template context
    return render_template(
        "configure.html",
        steps=steps,
        conn_list=conn_list
    )
@dag_generator_bp.route("/generate", methods=["POST"])
@csrf.exempt
def generate_dags():
    raw = session.pop("workflow_steps", "[]")
    step_defs = json.loads(raw)

    template = current_app.jinja_env.get_template("dag_template.py.jinja")
    dags_folder = conf.get("core", "dags_folder")

    now = datetime.utcnow()
    dag_id = f"slurm_workflow_{now.strftime('%Y%m%dT%H%M%S')}"
    ctx = {
        "dag_id": dag_id,
        "owner": current_app.config.get("AIRFLOW__CORE__DEFAULT_OWNER", "airflow"),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "schedule_interval": "@once",
        "dag_tags": "Generated",
        # defaults for optional bits
        "download": False,
        "repo_type": "",
        "repo_url": "",
        "ssh_conn": "",
        "script_path": "",
        "qos": "",
        "job_name": ""
    }

    # 4) Merge in each step’s parameters
    for step in step_defs:
        t = step.get("type")
        p = step.get("params", {})

        if t == "git":
            ctx["download"]  = True
            ctx["repo_type"] = p.get("repo_type", "")
            ctx["repo_url"]  = p.get("repo_url", "")

        elif t == "transfer":
            # we assume a transfer step delivers the script to the HPC path
            ctx["script_path"] = p.get("dest", "")

        elif t == "slurm":
            ctx["ssh_conn"]    = p.get("ssh_conn", "")
            ctx["script_path"] = p.get("script", "")
            ctx["qos"]         = p.get("qos", "")
            ctx["job_name"]    = p.get("job_name", "")

        else:
            # unknown step type—skip or log as needed
            current_app.logger.warning(f"Unknown step type in workflow: {t}")

    # 5) Render the DAG and write it to a file
    rendered = template.render(**ctx)
    filename = f"{dag_id}.py"
    full_path = os.path.join(dags_folder, filename)
    with open(full_path, "w") as f:
        f.write(rendered)

    # 6) Notify the user and go back
    flash(f"Generated DAG: {filename}", "success")
    return redirect(url_for("dag_generator.show_builder"))
# ─────────────────────────────────────────────────────────────────────────────
# 2) The tiny BaseView — just to get the Admin dropdown link.
# ─────────────────────────────────────────────────────────────────────────────
class WorkflowBuilderView(BaseView):
    default_view = "builder"

    @expose("/builder")
    def builder(self):
        # Redirect into your blueprint’s builder route
        return redirect(url_for("dag_generator.show_builder"))

# ─────────────────────────────────────────────────────────────────────────────
# 3) Register everything in the plugin
# ─────────────────────────────────────────────────────────────────────────────
class DagGeneratorPlugin(AirflowPlugin):
    name = "dag_generator_plugin"
    flask_blueprints = [dag_generator_bp]
    appbuilder_views = [{
        "name": "Workflow Builder",
        "category": "Admin",
        "view": WorkflowBuilderView()
    }]
