# Crash Handler - Developer Documentation

The crash handler module (`src/avatars/crash_handler.py`) provides automatic crash reporting for the Avatar Python client. It captures detailed diagnostic information when unhandled exceptions occur.

## Architecture Overview

### Auto-Installation

The crash handler is automatically installed when the `avatars` package is imported:

```python
# In src/avatars/__init__.py
from avatars import crash_handler as _crash_handler  # Auto-installs the hook
```

The hook replaces `sys.excepthook` with a custom handler that:

1. Captures Runner YAML configurations
2. Generates a detailed crash report
3. Saves the report to a file
4. Displays the standard Python traceback to the user

### Runner Registry

Runners are tracked using a `WeakSet` to avoid memory leaks.

Each `Runner` instance registers itself in `__init__`:

```python
# In src/avatars/runner.py
from avatars.crash_handler import register_runner

class Runner:
    def __init__(self, ...):
        # ... initialization ...
        register_runner(self)
```

## Crash Report Contents

The generated report includes:

| Section                    | Description                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| System Information         | OS, Python version, executable path, working directory                                       |
| Exception                  | Exception type and message                                                                   |
| Stack Trace                | Full traceback with source context for user code                                             |
| Full User File             | Complete source of the first user code file in the traceback (with sensitive lines redacted) |
| Runner YAML Configurations | `get_yaml()` output from all registered Runners                                              |

### User Code Detection

The `is_user_code()` function uses a heuristic to distinguish user code from library code:

```python
LIBRARY_PATHS = ["site-packages", "dist-packages", "lib/python"]

def is_user_code(filename: str) -> bool:
    for path_pattern in LIBRARY_PATHS:
        if path_pattern in filename:
            return False
    return True
```

Library code frames show `[Library Code - Context Hidden]` instead of source context.

### Sensitive Information Redaction

The crash handler uses AST parsing to automatically redact sensitive information from crash reports:

1. **`.authenticate()` calls**: Any line containing a call to `.authenticate(...)` is replaced with `[REDACTED - SENSITIVE]`
2. **Password variables**: Variables used as the password argument (2nd positional or `password=` keyword) are tracked, and any lines that assign values to these variables are also redacted

Example:

```python
# Original user code
password = os.environ.get("PASSWORD")
manager.authenticate(username, password)

# In crash report
   5: [REDACTED - SENSITIVE]
   6: [REDACTED - SENSITIVE]
```

This prevents accidental exposure of credentials when sharing crash reports with support.

## Configuration

| Environment Variable       | Default            | Description                        |
| -------------------------- | ------------------ | ---------------------------------- |
| `AVATAR_CRASH_REPORT_PATH` | `crash_report.txt` | Path where crash reports are saved |

## Testing

To test the crash handler manually:

```python
import avatars

# Create a runner to test YAML capture
manager = avatars.Manager()
manager.authenticate("user", "password")
runner = manager.create_runner("test")
runner.add_table("my_table", my_dataframe)
runner.set_parameters("my_table", k=5)

# Trigger an error
raise RuntimeError("Test crash")
```

Check `crash_report.txt` for the generated report.

## Design Decisions

1. **Silent operation**: The crash handler produces no output except the standard traceback and the "crash report generated" message. This keeps the user experience clean.
