from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint, request, redirect, url_for, flash
from airflow.www.app import csrf
from flask_appbuilder import BaseView, expose
from airflow.models import Variable
from dag_generator import generate_dag_file
from datetime import datetime
import os

# Blueprint to handle form GET/POST
dag_generator_bp = Blueprint(
    "dag_generator", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/dag-generator"
)

@dag_generator_bp.route("/builder", methods=["GET", "POST"])



class DagGeneratorPlugin(AirflowPlugin):
    name = "dag_generator_plugin"
    flask_blueprints = [dag_generator_bp]
