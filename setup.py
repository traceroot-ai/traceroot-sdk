#!/usr/bin/env python3
"""Setup script for TraceRoot.AI SDK package."""

import os

from setuptools import find_packages, setup


def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, encoding='utf-8') as f:
            return f.read()
    return ""


setup(
    name="traceroot",
    version="0.0.2",
    author="TraceRoot Team",
    author_email="",
    description=(
        "A clean, principled wrapper around OpenTelemetry, AWS CloudWatch, "
        "and AWS X-Ray for enhanced debugging experience"),
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://traceroot.ai/",
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
    install_requires=[
        "opentelemetry-api==1.34.1",
        "opentelemetry-sdk==1.34.1",
        "opentelemetry-exporter-otlp==1.34.1",
        "opentelemetry-exporter-otlp-proto-common==1.34.1",
        "opentelemetry-exporter-otlp-proto-grpc==1.34.1",
        "opentelemetry-exporter-otlp-proto-http==1.34.1",
        "opentelemetry-instrumentation==0.55b1",
        "opentelemetry-instrumentation-asgi==0.55b1",
        "opentelemetry-instrumentation-fastapi==0.55b1",
        "opentelemetry-proto==1.34.1",
        "opentelemetry-sdk-extension-aws==2.1.0",
        "opentelemetry-propagator-aws-xray==1.0.2",
        "opentelemetry-semantic-conventions==0.55b1",
        "opentelemetry-util-http==0.55b1",
        "watchtower==3.4.0",
        "pandas==2.3.0",
        "PyYAML==6.0.2",
    ],
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
            "opentelemetry-instrumentation-fastapi==0.55b1",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="artificial-intelligence agent-systems opentelemetry tracing logging debugging",
    project_urls={
        "Bug Reports": "https://github.com/traceroot-ai/traceroot-sdk/issues",
        "Source": "https://github.com/traceroot-ai/traceroot-sdk",
        "Documentation": "https://docs.traceroot.ai",
    },
)
