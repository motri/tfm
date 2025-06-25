import os
from datetime import datetime
from airflow.configuration import conf
from airflow.hooks.base import BaseHook  # <-- Added to retrieve connection details

def build_dag_files(step_defs, global_cfg, jinja_env):
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

        ctx = {
            **global_cfg,
            **params,
            'dag_id': dag_id,
            'next_dag_id': next_dag,
            'start_date_year': year,
            'start_date_month': month,
            'start_date_day': day,
        }

        # Special handling for SLURM
        if step_type == 'slurm':
            parts = []
            parts.append(params["script"]) 
            if params.get("qos"):
                parts.append(f"--qos={params['qos']}")
            if params.get("job_name"):
                parts.append(f"--job-name={params['job_name']}")
            if params.get("extra_args"):
                parts.append(params['extra_args'])
            ctx["sbatch_args"]   = " ".join(parts)
            ctx["ssh_conn_id"]   = params["ssh_conn_id"]
            ctx["poll_interval"] = params.get("poll_interval", 60)

        # Special handling for Git + SCP
        elif step_type == 'git' and params.get("scp_enabled") and params.get("scp_conn_id"):
            try:
                conn = BaseHook.get_connection(params["scp_conn_id"])
                ctx["ssh_user"] = conn.login or "airflow"
                ctx["ssh_host"] = conn.host or "localhost"
            except Exception as e:
                ctx["ssh_user"] = "undefined"
                ctx["ssh_host"] = "undefined"
                print(f"Warning: could not retrieve SSH connection info: {e}")

        template = jinja_env.get_template(f"dag_{step_type}.py.jinja")
        rendered = template.render(**ctx)

        filename = f"{dag_id}.py"
        full_path = os.path.join(dags_folder, filename)
        with open(full_path, 'w') as f:
            f.write(rendered)
        generated.append(filename)

    return generated
