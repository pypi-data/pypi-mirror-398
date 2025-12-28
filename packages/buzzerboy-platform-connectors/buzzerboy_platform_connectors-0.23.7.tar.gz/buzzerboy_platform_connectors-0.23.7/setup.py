from setuptools import setup, find_packages
import os, toml

def parse_requirements(filename):
    absolute_path = os.path.join(os.path.dirname(__file__), filename)
    with open(absolute_path, 'r') as file:
        lines = file.readlines()
        return [line.strip() for line in lines if line.strip() and not line.startswith('#')]

def ensure_manifest_includes_requirements():
    manifest_file = 'MANIFEST.in'
    requirements_line = 'include requirements.txt\n'
    if os.path.exists(manifest_file):
        with open(manifest_file, 'r') as file:
            lines = file.readlines()
        if requirements_line not in lines:
            with open(manifest_file, 'a') as file:
                file.write(requirements_line)
    else:
        with open(manifest_file, 'w') as file:
            file.write(requirements_line)

# Ensure MANIFEST.in includes requirements.txt
ensure_manifest_includes_requirements()

# Read pyproject.toml
pyproject = toml.load('pyproject.toml')
project = pyproject['project']

setup(
    name=project['name'],
    version=project['version'],
    author=project['authors'][0]['name'],
    author_email=project['authors'][0]['email'],
    description=project['description'],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url=project['urls']['Homepage'],
    packages=find_packages(),
    classifiers=project['classifiers'],
    python_requires=project['requires-python'],
    install_requires=parse_requirements("requirements.txt"),
    license=project['license']
)