# BTP Scheduler - Setup for Binary Distribution
from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import os
import glob

# 收集所有 Python 文件（排除 setup.py）
py_files = []
for root, dirs, files in os.walk('.'):
    # 排除目录
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'build', 'dist', '.egg-info', 'scripts', 'docs', 'tests']]
    
    for file in files:
        if file.endswith('.py') and file != 'setup.py':
            py_files.append(os.path.join(root, file))

# 创建 Extension 对象
extensions = [
    Extension(
        name=py_file[2:-3].replace(os.sep, '.'),  # ./path/file.py -> path.file
        sources=[py_file],
    )
    for py_file in py_files
]

setup(
    name="mp-btp",
    version="2.0.5",
    packages=find_packages(),
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'embedsignature': True,
        }
    ),
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "click>=8.1.0",
        "playwright>=1.40.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'btp-scheduler=api.server:main',
            'btp-admin=admin:cli',
        ],
    },
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
    options={
        'bdist_wheel': {
            'plat_name': 'manylinux2014_x86_64'
        }
    }
)
