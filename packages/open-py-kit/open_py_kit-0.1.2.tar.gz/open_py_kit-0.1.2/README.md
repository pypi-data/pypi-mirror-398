# open-py-kit

![Build Status](https://github.com/kuldeep0020/open-py-kit/actions/workflows/test.yml/badge.svg)

A standardized Python toolkit for building robust applications.

## Installation

```bash
pip install open-py-kit
```

## Modules

### Logger

A structured logging library providing a unified interface for Python applications.

**Imports**
```python
# Import from the kit namespace
from open_py_kit.logger import NewFactory, LoggerConfig, Field
```

**Usage**
```python
# Configure
config = LoggerConfig(log_level="DEBUG", enable_console=True)
factory = NewFactory(config)

# Create Logger
log = factory.new_logger()

# Log
log.info("Application started")
log.debugw("User processed", user_id=123, status="active")

# Child Logger
router_log = log.child("router")
router_log.info("Request received")
```
