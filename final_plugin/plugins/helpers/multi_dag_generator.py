import os
from datetime import datetime
from airflow.configuration import conf

def build_dag_files(step_defs, global_cfg, jinja_env):
    """
    Render one DAG per step, chaining with TriggerDagRunOperator.
    
    :param step_defs: List[Dict] with keys "type" and "params"
    :param global_cfg: Dict with keys like workflow_name, owner, start_date, etc.
    :param jinja_env:  Jinja2 Environment (e.g. current_app.jinja_env)
    :returns: List of filenames written
    """
    dags_folder = conf.get('core', 'dags_folder')
    generated = []

    for idx, step in enumerate(step_defs):
        step_type = step['type']
        params    = step.get('params', {})

        # Build unique dag_id and next_dag_id
        now    = datetime.now()
        base   = global_cfg['workflow_name']
        dag_id = f"{base}_step{idx+1}_{step_type}_{now.strftime('%Y%m%dT%H%M%S')}"
        if idx + 1 < len(step_defs):
            nt = step_defs[idx+1]['type']
            # next dag id uses same timestamp prefix
            next_dag = f"{base}_step{idx+2}_{nt}_{now.strftime('%Y%m%dT%H%M%S')}"
        else:
            next_dag = None

        # Prepare context for Jinja
        year, month, day = now.year, now.month, now.day
        ctx = {
            **global_cfg,
            **params,
            'dag_id': dag_id,
            'next_dag_id': next_dag,
            'start_date_year': year,
            'start_date_month': month,
            'start_date_day': day,
        }

        # Render
        template = jinja_env.get_template(f"dag_{step_type}.py.jinja")
        rendered = template.render(**ctx)

        # Write out
        filename = f"{dag_id}.py"
        full_path = os.path.join(dags_folder, filename)
        with open(full_path, 'w') as f:
            f.write(rendered)
        generated.append(filename)

    return generated
