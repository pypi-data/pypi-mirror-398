# Crash Reporting

When an unhandled exception occurs while using the Avatar Python client, a crash report is automatically generated to help diagnose the issue.

## What Happens When an Error Occurs

If your script encounters an unexpected error, you will see:

1. The standard Python traceback (the familiar error message format)
2. A message indicating that a crash report has been saved

Example output:

```text
Traceback (most recent call last):
  File "my_script.py", line 42, in <module>
    runner.run()
  File ".../avatars/runner.py", line 667, in run
    ...
ValueError: Some error message

[!] A crash report has been generated at '/path/to/crash_report.txt'.
    Please include this file if you want to be assisted at support@octopize.io.
```

## What's in the Crash Report

The crash report (`crash_report.txt`) contains detailed information to help our support team diagnose your issue:

- **System Information**: Your operating system, Python version, and working directory
- **Exception Details**: The full error type and message
- **Stack Trace**: The complete call stack with source code context for your code
- **Your Script**: The full content of your script file
- **Configuration**: The YAML configuration of any Runner instances you created

## Getting Help

If you encounter an issue:

1. Check the error message in your terminal for immediate guidance
2. If you need assistance, email [support@octopize.io](mailto:support@octopize.io) and attach the `crash_report.txt` file
3. The crash report contains all the information needed to help you quickly

## Crash Report Location

By default, the crash report is saved as `crash_report.txt` in your current working directory.

You can customize this location by setting the `AVATAR_CRASH_REPORT_PATH` environment variable:

```bash
export AVATAR_CRASH_REPORT_PATH="/path/to/my_crash_report.txt"
```

## Privacy Note

The crash report includes your script's source code and configuration. Review the file before sharing if you have concerns about sensitive information.
