from setuptools import setup, find_packages
from pathlib import Path

# Read requirements.txt
requirements = Path(__file__).parent.joinpath('requirements.txt').read_text().splitlines()

sdk_packages = find_packages(where='src')
packages = ['gmi_ieops'] + [f'gmi_ieops.{p}' for p in sdk_packages]

setup(
    name="gmi_ieops",
    version="0.2.5",
    author="GMICloud Inc.",
    packages=packages,
    package_dir={'gmi_ieops': 'src'},
    python_requires=">=3.10",
    install_requires=requirements
) 