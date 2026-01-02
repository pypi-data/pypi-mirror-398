from setuptools import setup, find_packages

with open("README.md","r") as f:
    description = f.read()

setup(
    name = 'tathaagat_pip',
    version='0.2',
    packages = find_packages(), 
    entry_points={
        "console_scripts":[
            "tathaagat_pip = tathaagat_pip:example",
        ],
    },
    long_description=description,
    long_description_content_type="text/markdown",
)