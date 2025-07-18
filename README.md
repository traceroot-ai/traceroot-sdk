<div align="center">

[![Documentation][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![PyPI Version][pypi-image]][pypi-url]
[![PyPI SDK Downloads][pypi-sdk-downloads-image]][pypi-sdk-downloads-url]
[![TraceRoot.AI Website][company-website-image]][company-website-url]
[![X][company-x-image]][company-x-url]
[![LinkedIn][company-linkedin-image]][company-linkedin-url]
[![WhatsApp][company-whatsapp-image]][company-whatsapp-url]


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

## Examples

For an end-to-end example that uses the TraceRoot SDK for a multi-agent system, please refer to the [Multi-agent System with TraceRoot SDK](https://docs.traceroot.ai/essentials/journey).

The source code of the multi-agent system example is available in [`traceroot-examples/examples/multi_agent`](https://github.com/traceroot-ai/traceroot-examples/tree/main/examples/multi_agent).


## Local Development

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

[docs-image]: https://img.shields.io/badge/Documentation-0dbf43
[docs-url]: https://docs.traceroot.ai
[discord-url]: https://discord.gg/CeuqGDQ58q/
[discord-image]: https://img.shields.io/discord/1395844148568920114?logo=discord&labelColor=%235462eb&logoColor=%23f5f5f5&color=%235462eb
[pypi-image]: https://badge.fury.io/py/traceroot.svg
[pypi-url]: https://pypi.python.org/pypi/traceroot
[company-website-image]: https://img.shields.io/badge/TraceRoot.AI-148740
[company-website-url]: https://traceroot.ai
[company-x-url]: https://x.com/TracerootAI
[company-x-image]: https://img.shields.io/twitter/follow/TracerootAI?style=social
[company-linkedin-url]: https://www.linkedin.com/company/traceroot-ai/
[company-linkedin-image]: https://custom-icon-badges.demolab.com/badge/LinkedIn-0A66C2?logo=linkedin-white&logoColor=fff
[company-whatsapp-url]: https://chat.whatsapp.com/GzBii194psf925AEBztMir
[company-whatsapp-image]: https://img.shields.io/badge/WhatsApp-25D366?logo=whatsapp&logoColor=white
[pypi-sdk-downloads-image]: https://img.shields.io/pypi/dm/traceroot
[pypi-sdk-downloads-url]: https://pypi.python.org/pypi/traceroot