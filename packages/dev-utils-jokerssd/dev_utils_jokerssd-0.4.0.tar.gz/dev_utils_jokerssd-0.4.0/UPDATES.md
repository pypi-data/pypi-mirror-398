2025-12-26

What's New:
  - dev_utils/lark_wrapper/messege_lark.py
    - Implemented Lark messaging functionality with the LarkRelated class.
  - dev_utils/lark_wrapper/msg_bot.py
    - Introduced the MsgBot class for a unified messaging interface.
  - dev_utils/lark_wrapper/sheet_utils.py
    - Added the LarkSheetAPI class for interacting with Lark sheets.
  - tests/test_msg_bot.py
    - Added unit tests for the new MsgBot.

Refactor:
  - AGENT.md
    - Removed an outdated testing instruction.

Configuration:
  - pyproject.toml
    - Added 'requests' and 'aiohttp' to dependencies.
    - Added 'pytest' to dev dependencies.
  - uv.lock
    - Updated lock file to reflect dependency changes.

Documentation
* Added AI Coding Assistant instructions (AGENT.md).
* Updated README.md with installation instructions for dev-utils-jokerssd and detailed usage of Logging Utils.

Features
* Introduced new package dev_utils with exports for LoggingUtils, LogTagging, LogType, and AsyncTimedRotatingFileHandler (from dev_utils/__init__.py and dev_utils/logging_utils/__init__.py).

Chore
* Updated package version to 0.2.0 (__version__.py).
* Configured pyproject.toml for building and distributing the dev-utils-jokerssd package.

Warnings:
None

What's New:
- `logging_utils/logging_utils.py` (2025-12-24)
  - Implemented `LoggingUtils` class for structured logging with `structlog`.
  - Supports JSON and plain text output.
  - Features asynchronous file rotation and dynamic context binding.
  - Includes a comprehensive test suite for various logging scenarios.
- `logging_utils/rotateHandler.py` (2025-12-24)
  - Added `AsyncTimedRotatingFileHandler` and other asynchronous logging handlers for efficient log management.

Chore:
- `.gitignore` (2025-12-24)
  - Configured to ignore common Python artifacts, build outputs, and virtual environments.
- `.python-version` (2025-12-24)
  - Set project Python version to 3.12.
- `__version__.py` (2025-12-24)
  - Added initial project version "0.0.1".
- `main.py` (2025-12-24)
  - Created a basic application entry point.
- `pyproject.toml` (2025-12-24)
  - Defined project metadata and dependencies, including `structlog`.
- `uv.lock` (2025-12-24)
  - Locked dependency versions for `dev-utils` and `structlog`.
