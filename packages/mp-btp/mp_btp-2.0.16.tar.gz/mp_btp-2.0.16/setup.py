# BTP Scheduler - Setup for Source Distribution
from setuptools import setup, find_packages

setup(
    name="mp-btp",
    version="2.0.16",
    packages=['mp_btp', 'mp_btp.api', 'mp_btp.api.routes', 'mp_btp.config', 'mp_btp.integrations', 'mp_btp.models', 'mp_btp.scheduler', 'mp_btp.tasks', 'mp_btp.utils'],
    package_data={
        'config': ['*.yaml'],
    },
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "click>=8.1.0",
        "playwright>=1.40.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "apscheduler>=3.10.0",
        "pytz>=2023.3",
        "psycopg2-binary>=2.9.0",
    ],
    entry_points={
        'console_scripts': [
            'btp-scheduler=mp_btp.api.server:main',
            'btp-admin=mp_btp.admin:cli',
        ],
    },
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
)
