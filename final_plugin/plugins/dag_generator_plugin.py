from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from airflow.www.app import csrf
from flask_appbuilder import BaseView, expose
from airflow.models import Variable
from dag_generator import generate_dag_file
from datetime import datetime
import os
import json
import session

class DagGeneratorView(BaseView):
    default_view = "builder"

    @expose("/builder", methods=["GET","POST"])
    @csrf.exempt
    def builder(self):
        if request.method == "POST":
            steps = request.form["workflow"]
            session["workflow_steps"] = steps
            return redirect(url_for(".configure"))
        return self.render_template("builder.html")
    
    @expose("/configure", methods=["GET","POST"])
    @csrf.exempt
    def configure(self):
        steps = session.get("workflow_steps")  # list of dicts
        if request.method == "POST":
            # Collect filled parameters for each step
            full_workflow = []
            for idx, step in enumerate(steps):
                params = {}
                for key in request.form:  
                    if key.startswith(f"step{idx}_"):
                        params[key[len(f"step{idx}_"):]] = request.form[key]
                full_workflow.append({"type": step["type"], "params": params})
            # Generate DAGs
            paths = generate_multi_step_dags(full_workflow)
            flash(f"Generated {len(paths)} DAG(s)", "success")
            return redirect(url_for(".builder"))
        
class DagGeneratorPlugin(AirflowPlugin):
    name = "dag_generator_plugin"
    appbuilder_views = [{
        "name": "Generate SLURM DAG",
        "category": "Admin",
        "view": DagGeneratorView()
    }]

