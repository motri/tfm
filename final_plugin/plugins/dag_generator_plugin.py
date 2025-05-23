import json
from flask import Blueprint, session, flash, redirect, url_for, request, render_template
from flask_appbuilder import BaseView, expose
from airflow.plugins_manager import AirflowPlugin
from airflow.www.app import csrf

dag_generator_bp = Blueprint(
    "dag_generator",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/dag-generator"
)

@dag_generator_bp.route("/builder", methods=["GET"])
def show_builder():
    return render_template("builder.html")

@dag_generator_bp.route("/configure", methods=["POST", "GET"])
@csrf.exempt
def configure_workflow():
    # STEP 1: receive the step‐type definitions from builder.html
    if request.method == "POST" and "workflow" in request.form:
        session["workflow_steps"] = request.form["workflow"]
        # Redirect to GET so that reloads don't repost the form
        return redirect(url_for("dag_generator.configure_workflow"))

    # STEP 2: on GET, ensure we have workflow_steps in session
    steps_json = session.get("workflow_steps")
    if not steps_json:
        flash("Please define workflow steps first.", "warning")
        return redirect(url_for("dag_generator.show_builder"))

    # STEP 3: parse the JSON into a Python list and render the configure form
    steps = json.loads(steps_json)
    return render_template("configure.html", steps=steps)

class WorkflowBuilderView(BaseView):
    default_view = "builder"

    @expose("/builder", methods=["GET"])
    def builder(self):
        return self.render_template("builder.html")


class DagGeneratorPlugin(AirflowPlugin):
    name = "dag_generator_plugin"
    flask_blueprints = [dag_generator_bp]
    appbuilder_views = [{
        "name": "Workflow Builder",
        "category": "Admin",
        "view": WorkflowBuilderView()
    }]
