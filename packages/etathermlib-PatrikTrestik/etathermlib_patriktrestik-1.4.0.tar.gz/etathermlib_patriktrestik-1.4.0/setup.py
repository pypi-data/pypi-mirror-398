from setuptools import setup, find_packages
import distutils.command.clean

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="etathermlib-PatrikTrestik",
    version="1.4.0",
    author="Patrik Trestik",
    author_email="patrikt@volny.cz",
    description="Etatherm heating regulation TCP interface library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PatrikTrestik/etathermlib",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)