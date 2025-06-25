from airflow.providers.ssh.hooks.ssh import SSHHook
import os

def transfer_repo_to_hpc(ssh_conn_id, local_path='/tmp/repo', remote_path='.'):
    ssh_hook = SSHHook(ssh_conn_id=ssh_conn_id)
    ssh_client = ssh_hook.get_conn()
    sftp = ssh_client.open_sftp()

    # Recursively upload local folder
    for root, dirs, files in os.walk(local_path):
        rel_path = os.path.relpath(root, local_path)
        remote_root = os.path.join(remote_path, rel_path).replace('\\', '/')
        try:
            sftp.mkdir(remote_root)
        except IOError:
            pass  # Directory already exists

        for file in files:
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_root, file).replace('\\', '/')
            sftp.put(local_file, remote_file)

    sftp.close()
    ssh_client.close()
