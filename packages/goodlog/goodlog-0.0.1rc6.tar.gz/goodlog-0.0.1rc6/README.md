# goodlog

Built on top the standard library's `logging`, this package allows for quick and simple logging configuration and provides useful, common utilities like JSON formatting and adding extra info to logs, with minimal configuration.

## Install

```bash
pip install goodlog
```

## Quick start

```python
import goodlog

# Configure logging once at application startup
goodlog.configure_logging(global_extra_info={"service": "my-app"})

# Create a logger and use it
logger = goodlog.create_logger(__name__)
logger.info("Application started")
```

Logs are emitted as JSON to stdout:

```json
{"logger_name": "__main__", "timestamp": "2025-01-01 12:00:00,000", "log_level": "INFO", "message": "Application started", "extra_info": {"service": "my-app"}, ...}
```

## Adding ephemeral extra info

Use the `ephemeral_info_context` context manager to attach extra fields to all logs within a scope:

```python
from goodlog import ephemeral_info_context, create_logger

logger = create_logger(__name__)

with ephemeral_info_context(user_id=42):
    logger.info("Some user action")
logger.info("Some later action")
```

Output log will be:

```json
{"logger_name": "__main__", "timestamp": "2025-01-01 12:00:00,000", "log_level": "INFO", "message": "Some user action", "extra_info": {"service": "my-app", "user_id": 42}, ...}
{"logger_name": "__main__", "timestamp": "2025-01-01 12:00:00,000", "log_level": "INFO", "message": "Some later action", "extra_info": {"service": "my-app"}, ...}
```

Inside the context, use `add` to add more info along the way:

```python
from goodlog import ephemeral_info_context, create_logger, add

logger = create_logger(__name__)

with ephemeral_info_context(user_id=42):
    logger.info("Some user action")
    ... # some logic discovering the user name
    add(user_name="John Doe")
    logger.info("Discovered user name")
logger.info("Some later action")
```

Output log will be:
```json
{... "message": "Some user action", "extra_info": {"service": "my-app", "user_id": 42}, ...}
{... "message": "Discovered user name", "extra_info": {"service": "my-app", "user_id": 42, "user_name": "John Doe"}, ...}
{... "message": "Some later action", "extra_info": {"service": "my-app"}, ...}
```

The `remove` function can be used to remove ephemeral info to add more info along the way:

```python
from goodlog import ephemeral_info_context, create_logger, add, remove

logger = create_logger(__name__)

with ephemeral_info_context(user_id=42):
    logger.info("Some user action")
    ... # some logic discovering the user name
    add(user_name="John Doe")
    logger.info("Discovered user name")
    remove()
    logger.info("No extra info here")
```

Output log will be:
```json
{... "message": "Some user action", "extra_info": {"service": "my-app", "user_id": 42}, ...}
{... "message": "Discovered user name", "extra_info": {"service": "my-app", "user_id": 42, "user_name": "John Doe"}, ...}
{... "message": "No extra info here", "extra_info": {"service": "my-app"}, ...}
```
As you can see, calling `remove` explicitly inside the context has the same effect as if we are already out of the context's scope.

## Links

- Source: https://github.com/benronen8/goodlog
- Docs: https://benronen8.github.io/goodlog
