
import os 
from datetime import datetime 
from jinja2 import Environment, FileSystemLoader

def generate_dags(params, dag_folder):

    """ Generates one or multiple DAG files based on params. 
    If downloading a repo, generate 3 DAGs: clone, copy, submit. Else, 
    generate a single submit DAG. """   

    env = Environment( loader=FileSystemLoader(os.path.join(os.path.dirname(file), 
            'templates')), trim_blocks=True, lstrip_blocks=True )    

    base_id = params['dag_id']
    generated_paths = []    

    if params.get('download'):
        clone_id = f"{base_id}_clone"
        copy_id = f"{base_id}_copy"
        submit_id = f"{base_id}_submit" 

        clone_tpl = env.get_template('clone_template.py.jinja')
        clone_rendered = clone_tpl.render(
            owner=params['owner'], year=params['year'], month=params['month'], day=params['day'],
            schedule_interval=params['schedule_interval'], dag_id=base_id,
            clone_dag_id=clone_id, copy_dag_id=copy_id,
            repo_type=params['repo_type'], repo_url=params['repo_url'], ssh_conn=params['ssh_conn'],
            script_path=params['script_path']
        )
        path = os.path.join(dag_folder, f"{clone_id}.py")
        with open(path, 'w') as f: f.write(clone_rendered)
        generated_paths.append(path)    

        copy_tpl = env.get_template('copy_template.py.jinja')
        copy_rendered = copy_tpl.render(
            owner=params['owner'], year=params['year'], month=params['month'], day=params['day'],
            schedule_interval=params['schedule_interval'], copy_dag_id=copy_id, submit_dag_id=submit_id,
            ssh_conn=params['ssh_conn'], script_path=params['script_path']
        )
        path = os.path.join(dag_folder, f"{copy_id}.py")
        with open(path, 'w') as f: f.write(copy_rendered)
        generated_paths.append(path)    

        submit_tpl = env.get_template('submit_template.py.jinja')
        submit_rendered = submit_tpl.render(
            owner=params['owner'], year=params['year'], month=params['month'], day=params['day'],
            schedule_interval=params['schedule_interval'], submit_dag_id=submit_id,
            ssh_conn=params['ssh_conn'], qos=params.get('qos'), job_name=params.get('job_name'),
            download=params['download'], script_path=params['script_path'], dag_tags=params.get('dag_tags', '')
        )
        path = os.path.join(dag_folder, f"{submit_id}.py")
        with open(path, 'w') as f: f.write(submit_rendered)
        generated_paths.append(path)
    else:
        submit_id = f"{base_id}_submit"
        submit_tpl = env.get_template('submit_template.py.jinja')
        submit_rendered = submit_tpl.render(
            owner=params['owner'], year=params['year'], month=params['month'], day=params['day'],
            schedule_interval=params['schedule_interval'], submit_dag_id=submit_id,
            ssh_conn=params['ssh_conn'], qos=params.get('qos'), job_name=params.get('job_name'),
            download=False, script_path=params['script_path'], dag_tags=params.get('dag_tags', '')
        )
        path = os.path.join(dag_folder, f"{submit_id}.py")
        with open(path, 'w') as f: f.write(submit_rendered)
        generated_paths.append(path)    

    return generated_paths