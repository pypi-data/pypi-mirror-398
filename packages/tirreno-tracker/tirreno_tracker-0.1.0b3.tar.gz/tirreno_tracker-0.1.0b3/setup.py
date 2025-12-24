import os
from setuptools import setup, find_packages


setup(
    name="tirreno_tracker",
    version="0.1.0b3",
    description="Python client for tirreno security analytics API",
    license="BSD-3-Clause",
    author="tirreno technologies sàrl",
    author_email="team@tirreno.com",
    url="https://github.com/tirrenotechnologies/tirreno-python-tracker",
    project_urls={
        "Homepage": "https://www.tirreno.com",
        "Source Code": "https://github.com/tirrenotechnologies/tirreno-python-tracker"
    },
    long_description="This is a Python implementation of the tirreno security analytics API based on PHP version.",
    long_description_content_type="text/x-rst",
    keywords=[
        "tirreno",
        "fraud-detection",
        "audit-trail",
        "analytics",
        "monitoring",
        "bot-detection",
        "antispam",
        "application-monitoring"
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2",
        "typing_extensions<4.2; python_version == \"3.6\"",
        "typing_extensions<4.8; python_version == \"3.7\"",
        "typing_extensions<4.14; python_version == \"3.8\"",
        "importlib_metadata<=4.5; python_version == \"3.6\"",
        "importlib_metadata<=7.0; python_version < \"3.8\"",
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    zip_safe=False
)
