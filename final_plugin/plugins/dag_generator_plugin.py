import json
from flask import Blueprint, render_template
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
