<div align="center">

[![Testing Status][testing-image]][testing-url]
[![Documentation][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![PyPI Version][pypi-image]][pypi-url]
[![PyPI SDK Downloads][pypi-sdk-downloads-image]][pypi-sdk-downloads-url]
[![npm version][npm-image]][npm-url]
[![TraceRoot.AI Website][company-website-image]][company-website-url]
[![X][company-x-image]][company-x-url]
[![X][zecheng-x-image]][zecheng-x-url]
[![X][xinwei-x-image]][xinwei-x-url]
[![LinkedIn][company-linkedin-image]][company-linkedin-url]
[![WhatsApp][company-whatsapp-image]][company-whatsapp-url]
[![Wechat][wechat-image]][wechat-url]

</div>

# TraceRoot SDK

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

## Cloud Mode

Cloud mode is to use TraceRoot's cloud service to store the logs and traces.

### Prerequisite

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

### Priority of the Configuration

The priority of the configuration is as follows:

1. Environment variables
1. `traceroot.init(...)` parameters
1. `.traceroot-config.yaml` file

For example, if you provide the configuration in the environment variables, the configuration in the `.traceroot-config.yaml` file will be overridden.

## Local Mode

Local mode is to use TraceRoot's local database to store the logs and traces.

### Prerequisite

You need to set up a local database to store the logs and traces by running the jaeger docker container.

Download the Jaeger Docker image:

```bash
docker run cr.jaegertracing.io/jaegertracing/jaeger:2.8.0 --help
```

Run the Jaeger Docker container:

```bash
docker stop jaeger || true && docker rm jaeger || true && docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 4317:4317 \
  -p 4318:4318 \
  cr.jaegertracing.io/jaegertracing/jaeger:2.8.0

docker logs -f jaeger
```

Then you need to use following code to initialize the TraceRoot SDK in local mode:

```python
traceroot.init(
    service_name="sdk-example-service",
    github_owner="traceroot-ai",
    github_repo_name="traceroot-sdk",
    github_commit_hash="main"
    local_mode=True
)
```

Or you can just put them in a yaml file called `.traceroot-config.yaml` in the root of your project:

```yaml
service_name: "sdk-example-service"
github_owner: "traceroot-ai"
github_repo_name: "traceroot-sdk"
github_commit_hash: "main"
local_mode: true
```

There is an example of using the configuration file for the local mode in the `.traceroot-config-local.yaml` file.

## Other Settings

You can also set the following settings in the `.traceroot-config.yaml` file:

- `enable_span_console_export`: Whether to enable console export and print the spans to the console.
- `enable_log_console_export`: Whether to enable console export and print the logs to the console.

## Examples

For an end-to-end example that uses the TraceRoot SDK for a multi-agent system, please refer to the [Multi-agent System with TraceRoot SDK](https://docs.traceroot.ai/essentials/journey).

The source code of the multi-agent system example is available in [`traceroot-examples/examples/multi_agent`](https://github.com/traceroot-ai/traceroot-examples/tree/main/examples/multi_agent).

## Citation

If you use our exploratory TraceRoot SDK in your research, please cite the following paper:

```bibtex
@article{traceroot_2025,
  title={TraceRoot Is All You Need for Debugging and Tracing},
  author={Zecheng Zhang and Xinwei He},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/traceroot-ai/traceroot}
}
```

## Contact Us

Please reach out to founders@traceroot.ai or visit [TraceRoot.AI](https://traceroot.ai) if you do not have these credentials or have any questions.

[company-linkedin-image]: https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff
[company-linkedin-url]: https://www.linkedin.com/company/traceroot-ai/
[company-website-image]: https://img.shields.io/badge/website-traceroot.ai-148740
[company-website-url]: https://traceroot.ai
[company-whatsapp-image]: https://img.shields.io/badge/WhatsApp-25D366?logo=whatsapp&logoColor=white
[company-whatsapp-url]: https://chat.whatsapp.com/GzBii194psf925AEBztMir
[company-x-image]: https://img.shields.io/twitter/follow/TracerootAI?style=social
[company-x-url]: https://x.com/TracerootAI
[discord-image]: https://img.shields.io/discord/1395844148568920114?logo=discord&labelColor=%235462eb&logoColor=%23f5f5f5&color=%235462eb
[discord-url]: https://discord.gg/tPyffEZvvJ
[docs-image]: https://img.shields.io/badge/docs-traceroot.ai-0dbf43
[docs-url]: https://docs.traceroot.ai
[npm-image]: https://img.shields.io/npm/v/traceroot-sdk-ts?style=flat-square&logo=npm&logoColor=fff
[npm-url]: https://www.npmjs.com/package/traceroot-sdk-ts
[pypi-image]: https://badge.fury.io/py/traceroot.svg
[pypi-sdk-downloads-image]: https://img.shields.io/pypi/dm/traceroot
[pypi-sdk-downloads-url]: https://pypi.python.org/pypi/traceroot
[pypi-url]: https://pypi.python.org/pypi/traceroot
[testing-image]: https://github.com/traceroot-ai/traceroot/actions/workflows/test.yml/badge.svg
[testing-url]: https://github.com/traceroot-ai/traceroot/actions/workflows/test.yml
[wechat-image]: https://img.shields.io/badge/WeChat-TraceRoot.AI-brightgreen?logo=wechat&logoColor=white
[wechat-url]: https://raw.githubusercontent.com/traceroot-ai/traceroot/refs/heads/main/misc/images/wechat.jpg
[xinwei-x-image]: https://img.shields.io/twitter/follow/xinwei_97?style=social
[xinwei-x-url]: https://x.com/xinwei_97
[zecheng-x-image]: https://img.shields.io/twitter/follow/zechengzh?style=social
[zecheng-x-url]: https://x.com/zechengzh
