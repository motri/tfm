import os
import json
from datetime import datetime
from airflow.configuration import conf
from airflow.models import Variable
import json


def build_dag_files(step_defs, global_cfg, jinja_env):

    # Registrar función personalizada
    def variable(key):
        return json.loads(Variable.get(key))
    jinja_env.globals['variable'] = variable

    dags_folder = conf.get('core', 'dags_folder')
    generated = []

    for idx, step in enumerate(step_defs):
        step_type = step['type']
        params    = step.get('params', {})

        now    = datetime.now()
        base   = global_cfg['workflow_name']
        dag_id = f"{base}_step{idx+1}_{step_type}_{now.strftime('%Y%m%dT%H%M%S')}"

        if idx + 1 < len(step_defs):
            nt = step_defs[idx+1]['type']
            next_dag = f"{base}_step{idx+2}_{nt}_{now.strftime('%Y%m%dT%H%M%S')}"
        else:
            next_dag = None

        year, month, day = now.year, now.month, now.day

        schedule_type = params.get("schedule_type", "manual")
        schedule_interval = params.get("schedule_interval") if schedule_type == "scheduled" else None

        var_key = f"{dag_id}_params"
        params_clean = {k: v for k, v in params.items() if k != "type"}
        Variable.set(var_key, json.dumps(params_clean))

        ctx = {
            **global_cfg,
            'dag_id': dag_id,
            'next_dag_id': next_dag,
            'start_date_year': year,
            'start_date_month': month,
            'start_date_day': day,
            'schedule_interval': schedule_interval,
            'params_var_key': var_key,  # clave que usarás en el template
        }

        template = jinja_env.get_template(f"dag_{step_type}.py.jinja")
        rendered = template.render(**ctx)

        filename = f"{dag_id}.py"
        full_path = os.path.join(dags_folder, filename)
        with open(full_path, 'w') as f:
            f.write(rendered)

        generated.append(filename)

    return generated
