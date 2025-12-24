# Decorpack

[![PyPI](https://img.shields.io/pypi/v/pedros)](https://pypi.org/project/pedros/)  

A small collection of reusable Python decorators and utilities.

## Features
 
- `logger`: pre-configured Python logger ready to use
- `timed`: decorator to measure execution time

## Installation

```bash
  pip install pedros
```

## Quickstart

You can check the [init](src/pedros/__init__.py) and [main](src/pedros/__main__.py) files for examples.

### Logger
```python
from pedros.logger import get_logger

logger = get_logger()

logger.info("This is an info message")
```
You can also override the default logger level and name:
```python
import logging
from pedros.logger import setup_logging, get_logger

setup_logging(logging.ERROR)
logger = get_logger("my_logger")

logger.info("This is an info message")
```

### Timed
```python
from pedros.timed import timed

@timed
def func():
    ...
```

## License

This project is licensed under the MIT [License](LICENSE).
