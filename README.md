# TraceRoot SDK

<div align="center">
  <a href="https://traceroot.ai/">
    <img src="https://raw.githubusercontent.com/traceroot-ai/traceroot/main/misc/images/traceroot_logo.png" alt="TraceRoot Logo">
  </a>
</div>

<div align="center">

[![Testing Status][testing-image]][testing-url]
[![Documentation][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![PyPI Version][pypi-image]][pypi-url]
[![PyPI SDK Downloads][pypi-sdk-downloads-image]][pypi-sdk-downloads-url]
[![TraceRoot.AI Website][company-website-image]][company-website-url]

</div>

TraceRoot SDK is a clean and principled package built upon OpenTelemetry with enhanced debugging and tracing experience. It provides smart logging and tracing with minimal setup and code changes.

## Quick Start

You can follow the [docs](https://docs.traceroot.ai/) here to get more details and have a deeper understanding of the TraceRoot SDK.

## Installation

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install traceroot
# or install the latest version from the source code
pip install -e .
```

## Prerequisite

For the TraceRoot SDK to work with your application, you need to set up some environment variables with some credentials.

Please visit [TraceRoot.AI](https://traceroot.ai) to get the credentials.

You also need to input following information to `traceroot.init(...)` at the beginning of your entry file for your Python program to have a full experience:

```python
traceroot.init(
    token="traceroot-********************************",
    service_name="sdk-example-service",
    github_owner="traceroot-ai",
    github_repo_name="traceroot-sdk",
    github_commit_hash="main"
)
```

Or you can just put them in a yaml file called `.traceroot-config.yaml` in the root of your project:

```yaml
token: "traceroot-********************************"
service_name: "sdk-example-service"
github_owner: "traceroot-ai"
github_repo_name: "traceroot-sdk"
github_commit_hash: "main"
```

- `token` is the token for the TraceRoot API.
- `service_name` is the name of the service or program you are going to keep track of.
- `github_owner` is the owner of the GitHub repository.
- `github_repo_name` is the name of the GitHub repository.
- `github_commit_hash` is the commit hash of the GitHub repository.
- You can disable the cloud export of spans and logs by setting the `enable_span_cloud_export` and `enable_log_cloud_export` to `false`. Notice that if you disable the cloud export of spans, the cloud export of logs will also be disabled.
- You can also choose to whether export the spans and logs to the console by setting the `enable_span_console_export` and `enable_log_console_export` to `true` or `false`.

The GitHub information is optional. If you do not provide them, the TraceRoot SDK will not be able to provide you with the GitHub information in the logs.

You can also provide the configuration in the environment variables. The environment variables are the same as the configuration parameters, but with the prefix `TRACEROOT_`. For example, you can set the `TRACEROOT_TOKEN` environment variable to the `token` for the TraceRoot API.

You can run following example to see how to use the environment variables:

```bash
TRACEROOT_TOKEN=traceroot-* TRACEROOT_SERVICE_NAME=new_name TRACEROOT_ENABLE_LOG_CLOUD_EXPORT=1 python3 examples/override_example.py
```

## Priority of the Configuration

The priority of the configuration is as follows:

1. Environment variables
1. `traceroot.init(...)` parameters
1. `.traceroot-config.yaml` file

For example, if you provide the configuration in the environment variables, the configuration in the `.traceroot-config.yaml` file will be overridden.

## Examples

For an end-to-end example that uses the TraceRoot SDK for a multi-agent system, please refer to the [Multi-agent System with TraceRoot SDK](https://docs.traceroot.ai/essentials/journey).

The source code of the multi-agent system example is available in [`traceroot-examples/examples/multi_agent`](https://github.com/traceroot-ai/traceroot-examples/tree/main/examples/multi_agent).

## Contact Us

Please reach out to founders@traceroot.ai or visit [TraceRoot.AI](https://traceroot.ai) if you have any questions.

[company-website-image]: https://img.shields.io/badge/website-traceroot.ai-black
[company-website-url]: https://traceroot.ai
[discord-image]: https://img.shields.io/discord/1395844148568920114?logo=discord&labelColor=%235462eb&logoColor=%23f5f5f5&color=%235462eb
[discord-url]: https://discord.gg/tPyffEZvvJ
[docs-image]: https://img.shields.io/badge/docs-traceroot.ai-0dbf43
[docs-url]: https://docs.traceroot.ai
[pypi-image]: https://badge.fury.io/py/traceroot.svg
[pypi-sdk-downloads-image]: https://static.pepy.tech/badge/traceroot
[pypi-sdk-downloads-url]: https://pypi.python.org/pypi/traceroot
[pypi-url]: https://pypi.python.org/pypi/traceroot
[testing-image]: https://github.com/traceroot-ai/traceroot/actions/workflows/test.yml/badge.svg
[testing-url]: https://github.com/traceroot-ai/traceroot/actions/workflows/test.yml
