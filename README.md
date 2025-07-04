<div align="center">

[![Documentation][docs-image]][docs-url]
[![PyPI Version][pypi-image]][pypi-url]
[![TraceRoot.AI Website][company-website-image]][company-website-url]
[![X][company-x-image]][company-x-url]


</div>

# TraceRoot SDK

TraceRoot SDK is a clean and principled package built upon OpenTelemetry with enhanced debugging and tracing experience. It provides smart and cloud-stored logging and tracing with minimal setup and code changes.

## Quick Start

You can follow the [docs](https://docs.traceroot.ai/) here to get more details and have a deeper understanding of the TraceRoot SDK.

### Installation

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install traceroot
# or install the latest version from the source code
pip install -e .
```

### Prerequisite
For the TraceRoot SDK to work with your application, we need to set up some environment variables with some credentials.

Please visit [TraceRoot.AI](https://traceroot.ai) to get the credentials.

You also need to input following information to `traceroot.init(...)` at the beginning of your entry file for your Python program to have a full experience:

```python
traceroot.init(
    name="traceroot-ai",
    service_name="sdk-example-service",
    github_owner="traceroot-ai",
    github_repo_name="traceroot-sdk",
    github_commit_hash="main"
)
```


Or you can just put them in a yaml file called `.traceroot-config.yaml` in the root of your project:

```yaml
name: "traceroot-ai"
service_name: "sdk-example-service"
github_owner: "traceroot-ai"
github_repo_name: "traceroot-sdk"
github_commit_hash: "main"
``` 

* Notice that the `name` is the name of the user who is using the TraceRoot SDK.
* `service_name` is the name of the service or program you are going to keep track of.

Please reach out to founders@traceroot.ai or visit [TraceRoot.AI](https://traceroot.ai) if you do not have these credentials or have any questions.

[docs-image]: https://img.shields.io/badge/Documentation-0dbf43
[docs-url]: https://docs.traceroot.ai
[pypi-image]: https://badge.fury.io/py/traceroot.svg
[pypi-url]: https://pypi.python.org/pypi/traceroot
[company-website-image]: https://img.shields.io/badge/TraceRoot.AI-0dbf43
[company-website-url]: https://traceroot.ai
[company-x-url]: https://x.com/TracerootAI
[company-x-image]: https://img.shields.io/twitter/follow/TracerootAI?style=social

## Examples

For an end-to-end example that uses the TraceRoot SDK for a multi-agent system, please refer to the [Multi-agent System with TraceRoot SDK](https://docs.traceroot.ai/essentials/journey).

The source code of the multi-agent system example is available in [`traceroot-examples/examples/multi_agent`](https://github.com/traceroot-ai/traceroot-examples/tree/main/examples/multi_agent).