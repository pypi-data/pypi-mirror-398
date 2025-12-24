from setuptools import setup, find_packages

airflow="2.10.5"

setup(
    name='test-dataflow-airflow',
    version="2.10.10",
    packages=find_packages(),
    author="Dataflow",
    description="Airflow customized for Dataflow",
    install_requires=[
        f'apache-airflow=={airflow}',
        'apache-airflow-providers-postgres',
        'apache-airflow-providers-amazon',
        'apache-airflow-providers-cncf-kubernetes',
        'eval_type_backport'
    ],
    package_data={
        'airflow': [
            'www/static/**/*',
            "www/templates/**/*",
        ]
    },
    include_package_data=True,
    url="https://github.com/Digital-Back-Office/dataflow-airflow"    
)