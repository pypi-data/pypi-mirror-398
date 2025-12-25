"""Python setup.py for project_name package"""
import io
import os
from setuptools import find_packages, setup



# Load version string from package
from vidrlhiv import __version__ as version



setup(
    name="vidrl-hiv",
    version=version,
    description="project_description",
    url="https://github.com/abcdtree/vidrl-hiv",
    long_description="nothing by long",
    long_description_content_type="text/markdown",
    author="Josh Zhang and Ammar Aziz",
    #packages=find_packages(exclude=["tests", ".github"]),
    packages=find_packages(exclude=["contrib", "docs", "tests", ".git"]),
    package_data={
        'vidrlhiv':['resources/Snakefile', 'resources/envs/*', 
        'resources/config.yaml', 'dirty_pipeline_ammar/*', 
        'dirty_pipeline_ammar/resources/*', 'dirty_pipeline_ammar/rules/*', 
        'dirty_pipeline_ammar/scripts/*', 'dirty_pipeline_ammar/wrappers/*',
        'dirty_pipeline_ammar/resources/references/*', 'dirty_pipeline_ammar/resources/superceded/*']
    },
    install_requires=[
        "snakemake >= 9.0",
        "pandas"
    ],
    entry_points={
        'console_scripts': [
            'vidrl-hiv = vidrlhiv.hiv:main',
        ]
    }
    #extras_require={"test": read_requirements("requirements-test.txt")},
)