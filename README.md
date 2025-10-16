# TraceRoot Python SDK

<div align="center">
  <a href="https://traceroot.ai/">
    <img src="https://raw.githubusercontent.com/traceroot-ai/traceroot/main/misc/images/traceroot_logo.png" alt="TraceRoot Logo">
  </a>
</div>

<div align="center">

[![Testing Status][testing-image]][testing-url]
[![Documentation][docs-image]][docs-url]
[![PyPI Version][pypi-image]][pypi-url]
[![PyPI SDK Downloads][pypi-sdk-downloads-image]][pypi-sdk-downloads-url]
[![TraceRoot.AI Website](https://raw.githubusercontent.com/traceroot-ai/traceroot/refs/heads/main/misc/images/custom-website-badge.svg)][company-website-url]

</div>

Please see the [Python SDK Docs](https://docs.traceroot.ai/sdk/python) for details.

## Installation

```bash
pip install traceroot
```

## Examples

```python
import traceroot
import asyncio

logger = traceroot.get_logger()

@traceroot.trace()
async def greet(name: str) -> str:
    logger.info(f"Greeting inside traced function: {name}")
    # Simulate some async work
    await asyncio.sleep(0.1)
    return f"Hello, {name}!"

async def main():
    result = await greet("world")
    logger.info(f"Greeting result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Contact Us

Please reach out to founders@traceroot.ai if you have any questions.

[company-website-url]: https://traceroot.ai
[docs-image]: https://img.shields.io/badge/docs-traceroot.ai-0dbf43
[docs-url]: https://docs.traceroot.ai
[pypi-image]: https://badge.fury.io/py/traceroot.svg
[pypi-sdk-downloads-image]: https://static.pepy.tech/badge/traceroot
[pypi-sdk-downloads-url]: https://pypi.python.org/pypi/traceroot
[pypi-url]: https://pypi.python.org/pypi/traceroot
[testing-image]: https://github.com/traceroot-ai/traceroot/actions/workflows/test.yml/badge.svg
[testing-url]: https://github.com/traceroot-ai/traceroot/actions/workflows/test.yml
