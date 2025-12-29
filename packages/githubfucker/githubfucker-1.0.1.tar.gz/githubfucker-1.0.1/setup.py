from setuptools import setup, find_packages
import os
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="githubfucker",           
    version="1.0.1",
    author="pythonxueba",
    description="Dev All-in-One Accelerator (Github, Pip, Docker, Apt, UV)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pythonxueba", 
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests",
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "fuckit=githubfucker.cli:main",
        ],
    },
)