import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

def generate_dag_file(params, dag_folder):
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template("dag_template.py.jinja")
    rendered = template.render(**params)

    dag_filename = f"{params['dag_id']}.py"
    dag_path = os.path.join(dag_folder, dag_filename)
    with open(dag_path, "w") as f:
        f.write(rendered)
    return dag_path
