# loggez: Python EZ logging

Control logging levels with env vars and have a unique logger per name, for library purposes...

Only writes to stderr, no files or stuff. Use something else for file logging though you can hack this library too.

## Installation

```
pip install loggez
```

## Usage:
```python
# run.py
from loggez import make_logger, loggez_logger
from loguru import logger

logger.info("loguru hi")
my_logger = make_logger("my_logger")
my_logger.add_file_handler("/path/to/logs.txt") # optional
my_logger.info("my_logger hi")
my_logger.debug("my_logger hi")
my_logger.debug2("my_logger hi")
my_logger.debug4("my_logger hi")

my_logger2 = make_logger("my_logger2")
my_logger2.info("my_logger2 hi")
my_logger2.debug("my_logger2 hi")
my_logger2.debug2("my_logger2 hi")
my_logger2.debug4("my_logger hi")

loggez_logger.info("loggez_logger hi")
loggez_logger.debug("loggez_logger hi")
loggez_logger.debug2("loggez_logger hi")
loggez_logger.debug4("loggez_logger hi")

```

Run with:
```
my_logger_LOGLEVEL=0 run.py
my_logger_LOGLEVEL=1 run.py
my_logger_LOGLEVEL=2 run.py
LOGGEZ_LOGLEVEL=4 run.py
```

Additional env vars:
- `my_logger_MESSAGE=...`: see the default in `loggez/loggez.py` to control colors and stuff.
- `my_logger_INFO_MESSAGE=...`, `my_logger_DEBUG_MESSAGE=...` etc.

Note: You can use also use the global predefined logger: `from loggez import loggez_logger as logger; logger.info(...)`.
Env variables are: `LOGGEZ_LOGLEVEL=...`, `LOGGEZ_INFO_MESSAGE=....` etc.

That's all.
