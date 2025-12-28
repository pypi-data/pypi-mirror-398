from setuptools import setup, find_packages

setup(
    name="mctech_core",
    version="1.1.4",
    packages=find_packages(
        include=["mctech_core**"],
        exclude=["*.tests", "testmain.py"]
    ),
    install_requires=["log4py", "pyyaml", "pyDes"]
)
