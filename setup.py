#!/usr/bin/env python3
"""Setup script for TraceRoot package."""

import os

from setuptools import find_packages, setup


# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
    return ""


# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__),
                                     'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements


setup(
    name="traceroot",
    version="0.1.0",
    author="TraceRoot Team",
    author_email="",
    description=(
        "A clean, principled wrapper around OpenTelemetry, AWS CloudWatch, "
        "and AWS X-Ray for enhanced debugging experience"),
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/traceroot",  # Update with actual repo URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black",
            "flake8",
            "mypy",
        ],
        "fastapi": [
            "fastapi==0.115.12",
            "uvicorn==0.34.3",
            "pre-commit==4.2.0",
            "pytest==8.4.0",
            "httpx==0.27.0",
            "numpy",
            "opentelemetry-instrumentation-fastapi>=0.41b0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="opentelemetry aws cloudwatch xray tracing logging debugging",
    project_urls={
        "Bug Reports": "https://github.com/your-org/traceroot/issues",
        "Source": "https://github.com/your-org/traceroot",
        "Documentation": "https://github.com/your-org/traceroot#readme",
    },
)
