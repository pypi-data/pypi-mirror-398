from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='rpc_rfsoc_handler',
    version='1.1.0',
    description='a pip-installable handler',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    author='Pascal Stoever',
    author_email='',
    keywords=['example'],
    url='',
    install_requires=[
        "grpcio-tools",
    ],
)