# Clarity API SDK for Python

[![PyPI - Downloads](https://badge.fury.io/py/clarity-api-sdk-python.svg)](https://pypi.org/project/clarity-api-sdk-python/)
[![Downloads](https://pepy.tech/badge/clarity-api-sdk-python)](ttps://test.pypi.org/project/clarity-api-sdk-python/)
![python](https://img.shields.io/badge/python-3.11%2B-blue)

A Python SDK for connecting to the CTI API server, with structured logging included.

## Installation

```bash
pip install clarity-api-sdk-python
```

## Logging

Logging support is built with [structlog](https://pypi.org/project/structlog/).

Set the root logger by setting the environment variable `LOG_LEVEL`. Otherwise, the default root logging is set to `INFO`.

```python
"""Example"""

import logging

from cti.logger import initialize_logger, get_logger, ExternalLoggerConfig

initialize_logger(
    external_logger_configurations=[
        ExternalLoggerConfig(name="urllib3"),
        ExternalLoggerConfig(name="httpcore"),
        ExternalLoggerConfig(name="httpx"),
        ExternalLoggerConfig(name="httpx_auth"),
        ExternalLoggerConfig(name="httpx_retries"),
    ],
    handlers=[logging.FileHandler("app.log")]
)

logger_a = get_logger("logger_a")
logger_b = get_logger("logger_b", "WARNING")

# root_logger = logging.getLogger()
# root_logger.setLevel("DEBUG")

logger_a.info("This is info message from logger_a")
logger_a.critical("This is critical message from logger_a")

# Dynamically change the log level of logger_a to WARNING
print("\nChanging logger_a level to WARNING...\n")
logging.getLogger("logger_a").setLevel(logging.WARNING)

logger_a.info("This info message from logger_a should NOT be visible.")
logger_a.warning("This is a new warning message from logger_a.")

logger_b.info("This info message from logger_b should NOT be visible.")
logger_b.warning("This is warning message from logger_b")
```

## API

### Singleton async client

```python
import asyncio
from cti.api.session import initialize_async_client, close_async_client

async def main():
    await initialize_async_client()
    # ... your application logic ...
    await close_async_client()

if __name__ == "__main__":
    asyncio.run(main())

# In other modules
from cti.api.session import async_client

async def fetch_data():
    if async_client:
        response = await async_client.get(...)
        return response.json()
```
