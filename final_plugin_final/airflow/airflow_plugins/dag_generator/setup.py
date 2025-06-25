from setuptools import find_packages, setup

setup(
    name="",              # Package name
    version="0.1.0",                     # Your package version
    description="Airflow plugin for SLURM DAG configuration UI",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),            # Finds the slurm_ui_plugin package automatically
    include_package_data=True,           # Include package data as specified in MANIFEST.in
    install_requires=[
        "apache-airflow>=2.0.0",         # Airflow should be declared as required
        # Add any additional dependencies your plugin requires.
    ],
    entry_points={
        "airflow.plugins": [
            "dag_generator = dag_generator.dag_generator:SlurmUIPlugin"
        ]
    },
)
