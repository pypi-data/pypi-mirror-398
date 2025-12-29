import os
from setuptools import setup, find_packages


setup(
    name="simple_calc_for_api_and_other",
    version="0.1.0",
    author="Xindorgi",
    description="A simple TDD-based calculator core with precision settings",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*", "app*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
