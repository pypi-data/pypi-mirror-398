from setuptools import setup, find_packages
from typing import List
import os
# from test import get_requirements

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()    


HYPEN_E_DOT='-e .'

def get_requirements(file_path:str)->List[str]:
    requirements = []

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_path)
    with open(file_path) as f:
        requirements=f.readlines()
        requirements=[req.replace("\n","")for req in requirements]
        
        if HYPEN_E_DOT in requirements:
            requirements.remove(HYPEN_E_DOT)
    return requirements

__version__ = "0.0.5"
REPO_NAME = "MLOPS-Project"
PKG_NAME= "dbautomater"
AUTHOR_USER_NAME = "mouryag"
AUTHOR_EMAIL = "mouryag99@gmail.com"

setup(
    name=PKG_NAME,
    version="0.0.5",
    author=AUTHOR_USER_NAME,
    author_email=AUTHOR_EMAIL,
    description="while learning mlops I created this python package for connecting with database.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}",
    project_urls={
        "Bug Tracker": f"https://github.com/{AUTHOR_USER_NAME}/{REPO_NAME}/issues",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    # install_requires = get_requirements("requirements_dev.txt")
    )