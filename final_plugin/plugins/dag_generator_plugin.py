import json, os, datetime
from flask import (
    Blueprint, render_template, request, session,
    flash, redirect, url_for, current_app
)
from flask_appbuilder import BaseView, expose
from airflow.plugins_manager import AirflowPlugin
from airflow.www.app import csrf
from helpers.multi_dag_generator import build_dag_files
from helpers.connection_list import conn_list

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

    form = request.form

    global_cfg = {
        'workflow_name':      request.form.get('workflow_name', ''),
        'workflow_description': request.form.get('workflow_description', ''),
        'workflow_tags':      request.form.get('workflow_tags', ''),
        'owner':              request.form.get('workflow_owner', ''),
        'workflow_email':     request.form.get('workflow_email', ''),
        'schedule_type':      request.form.get('schedule_type', ''),
        'schedule_interval':  request.form.get('schedule_interval', ''),
        'catchup':            'catchup' in request.form,
    }

    for idx, step in enumerate(step_defs):
        prefix = f"step{idx}_"
        params = {}
        for key, val in form.items():
            if key.startswith(prefix):
                name = key[len(prefix):]   # e.g. "ssh_conn_id"
                # Si fuera checkbox
                if isinstance(val, str) and val.lower() in ("on", "true"):
                    params[name] = True
                else:
                    params[name] = val
        step['params'] = params
    
    generated = build_dag_files(step_defs, global_cfg, current_app.jinja_env)

    flash(f"Generated {len(generated)} DAG(s): {', '.join(generated)}", "success")
    return redirect(url_for("dag_generator.show_builder"))


class WorkflowBuilderView(BaseView):
    default_view = "builder"

    @expose("/builder")
    def builder(self):
        return redirect(url_for("dag_generator.show_builder"))


class DagGeneratorPlugin(AirflowPlugin):
    name = "dag_generator_plugin"
    flask_blueprints = [dag_generator_bp]
    appbuilder_views = [{
        "name": "Workflow Builder",
        "category": "Admin",
        "view": WorkflowBuilderView()
    }]
