# setup.py
from setuptools import setup, find_packages
import os

default_requirements = [
    "argparse",
    # Add any other dependencies your package needs
]

try:
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file) as f:
            requirements = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    else:
        print("requirements.txt not found, using default requirements")
        requirements = default_requirements
except Exception as e:
    print(f"Error reading requirements.txt, using default requirements: {e}")
    requirements = default_requirements

setup(
    name="vyomcloudbridge",
    version="0.2.105",
    packages=find_packages(exclude=["tests", "tests.*", "extra", "extra.*"]),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vyomcloudbridge=vyomcloudbridge.cli:main",
        ],
    },
    author="Vyom OS Admin",
    author_email="admin@vyomos.org",
    description="A communication service for vyom cloud",
    python_requires=">=3.6",
    package_data={"vyomcloudbridge": ["scripts/*.sh"]},
    include_package_data=True
    # This puts install_script.sh in the data directory
    # data_files=[
    #     ("share/vyomcloudbridge", ["install_script.sh"]),
    # ],
    # # This installs install_script.sh as a script in the bin directory
    # scripts=["install_script.sh"],
)
