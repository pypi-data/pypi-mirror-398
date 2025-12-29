"""
Setup configuration for PAB - APCloudy Deployment Tool
"""

import os

from setuptools import setup, find_packages


# Read the README file for long description
def read_readme():
    try:
        with open("README.md", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "PAB CLI - APCloudy Deployment Tool for Scrapy Spiders"


# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "click>=8.0.0",
            "requests>=2.25.0",
            "colorama>=0.4.4",
            "tabulate>=0.9.0",
            "cryptography>=3.4.0"
        ]


setup(
    name="pab-cli",
    version="0.2.4",
    author="Fawad Ali",
    author_email="fawadstar6@gmail.com",
    description="PAB CLI - APCloudy Deployment Tool for Scrapy Spiders",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/fawadss1/pab-cli",
    project_urls={
        "Bug Tracker": "https://github.com/fawadss1/pab-cli/issues",
        "Documentation": "https://pab-cli.readthedocs.io/",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "pab=pab_cli.cli:main",
        ],
    },
    keywords="scrapy deployment apcloudy cli spider web-scraping",
    include_package_data=True,
)
