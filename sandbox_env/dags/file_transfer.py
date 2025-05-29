from airflow.decorators import dag, task
from datetime import datetime
import boto3
import subprocess
import os
from pathlib import Path

@dag(schedule_interval=None, start_date=datetime(2024, 1, 1), catchup=False, tags=["minio", "hpc"])
def minio_to_hpc_transfer():

    @task()
    def download_from_minio():
        # Setup
        endpoint_url = "http://minio.example.com:9000"
        access_key = "MINIO_ACCESS_KEY"
        secret_key = "MINIO_SECRET_KEY"
        bucket = "my-images"

        local_dir = "/tmp/images"
        os.makedirs(local_dir, exist_ok=True)

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        # List and download images
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                file_key = obj["Key"]
                local_path = Path(local_dir) / Path(file_key).name
                s3.download_file(bucket, file_key, str(local_path))

        return local_dir

    @task()
    def push_to_hpc(local_dir: str):
        remote_user = "your_user"
        remote_host = "hpc.example.edu"
        remote_path = "/home/your_user/datasets/images"

        cmd = [
            "rsync", "-azP",
            "-e", "ssh",
            f"{local_dir}/",  # Trailing slash to copy contents, not dir
            f"{remote_user}@{remote_host}:{remote_path}"
        ]

        subprocess.run(cmd, check=True)
        return f"Transferred images from {local_dir} to HPC:{remote_path}"

    local_dir = download_from_minio()
    push_to_hpc(local_dir)

minio_to_hpc_transfer()
