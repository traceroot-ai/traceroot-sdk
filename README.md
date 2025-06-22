# TraceRoot

TraceRoot is a clean, principled wrapper around OpenTelemetry, AWS CloudWatch, and AWS X-Ray for enhanced debugging experience. It provides smart logging and tracing for AWS-based applications with minimal setup.

## Quick Start

### Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='us-west-2'
```

### Running an example
```bash
python tests/test_e2e.py
```