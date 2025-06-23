# Traceroot SDK

Traceroot SDK is a clean, principled wrapper around OpenTelemetry, AWS CloudWatch, and AWS X-Ray for enhanced debugging experience. It provides smart logging and tracing for AWS-based applications with minimal setup.

## Quick Start

### Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev,fastapi]"
```

### Prerequisite
For the Traceroot SDK to work with your application, we need to set up the
following environment variable
```
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='your_region'
```
and run `def initialize_tracing(...)` in the beginning, where we need to set up
the following environment variable
```
- aws_region
- otlp_endpoint
```
Please reachout to founders@traceroot.ai if you do not have these credentials
yet.

### Running examples
```bash
python tests/test_e2e.py
python tests/test_e2e_complex.py
```
