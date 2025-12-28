"""Utilities for logging."""
import logging
from pathlib import Path
from typing import Any

import structlog
from structlog.processors import (
    EventRenamer,
    JSONRenderer,
    KeyValueRenderer,
    TimeStamper,
    format_exc_info,
)
from structlog.stdlib import (
    ExtraAdder,
    LoggerFactory,
    ProcessorFormatter,
    add_log_level,
    add_logger_name,
)

from .rotateHandler import AsyncTimedRotatingFileHandler


class LogType:
    """Log type constants."""

    LOG_TYPE = "log_type"


LOG_LEVEL_MAPPINGS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class LogTagging:
    """A class for tagging log messages."""

    def __init__(self, base_logging: dict | None = None) -> None:
        """Initialize the LogTagging class."""
        self.base_logging = base_logging or {}

    def get_log_kwargs(self, log_type: str | None = None) -> dict:
        """Get the log keyword arguments."""
        if log_type is None:
            return self.base_logging
        return {LogType.LOG_TYPE: log_type, **self.base_logging}


class LoggingUtils:
    """A utility class for setting up structured logging."""

    def __init__(
        self,
        log_file: str | None = None,
        log_dir: str | None = None,
        log_level: int | str | None = None,
        *,
        print_output: bool = False,
        binding_dict: dict | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the LoggingUtils class."""
        # read options
        json_formatter = kwargs.get("json_formatter", True)
        structlog_enabled = kwargs.get("structlog_enabled", True)
        plain_text_format = (
            kwargs.get("log_format")
            or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        log_when = kwargs.get("log_when", "D")

        self.binding_dict = binding_dict or {}

        if log_level and isinstance(log_level, str):
            # convert to log Int
            log_level = LOG_LEVEL_MAPPINGS.get(log_level.upper())
        if log_level and isinstance(log_level, int):
            # check set to log int to log str
            log_level = logging.getLevelName(log_level)

        # default to INFO
        log_level = log_level or logging.getLevelName(logging.INFO)
        self.binding_dict["Min Log lvl"] = log_level

        # standard root logger (keeps behavior same as before)
        self.logger = logging.getLogger()

        # set logger level (support string or int)
        self.logger.setLevel(log_level)

        self.log_dir = log_dir or f'{Path(__file__).parent.parent/"Logs"}'
        if log_file:
            self.log_file = f"{self.log_dir}/{log_file}"
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        else:
            self.log_file = None

        file_handler, console_handler = self._setup_handlers(
            print_output=print_output, log_when=log_when,
        )

        self._setup_formatters_and_structlog(
            structlog_enabled=structlog_enabled,
            json_formatter=json_formatter,
            plain_text_format=plain_text_format,
            file_handler=file_handler,
            console_handler=console_handler,
        )

        # add handlers if not already present (avoid duplicate handlers on re-init)
        if file_handler and not self._handler_already_added(file_handler):
            self.logger.addHandler(file_handler)
        if console_handler and not self._handler_already_added(console_handler):
            self.logger.addHandler(console_handler)

        if structlog_enabled:
            self.logger = structlog.get_logger()
            if self.binding_dict:
                self.logger = self.logger.bind(**self.binding_dict)

        # Informational startup message.
        # Using structlog API yields structured output if enabled.
        try:
            # Prefer structlog logger so we get structured binding easily
            self.logger.info(
                "logging set up",
                log_file=self.log_file or "None",
                json=json_formatter,
            )
        except OSError:
            # fallback to stdlib
            self.logger.info("logging set up in %s", self.log_file or "None")

    def get_logger(self) -> logging.Logger:
        """Return the stdlib root logger to preserve compatibility.

        If you prefer structured logging calls, you can also use
        structlog.get_logger(...) directly.
        """
        return self.logger

    def add_bindings(self, bindings: dict) -> None:
        """Add new key-value pairs to the logger's bound context.

        Args:
            bindings: A dictionary of keys and values to bind to the logger.

        """
        self.binding_dict.update(bindings)
        if hasattr(self.logger, "bind"):
            self.logger = self.logger.bind(**bindings)

    def rm_bindings(self, keys: list[str]) -> None:
        """Remove keys from the logger's bound context.

        Args:
            keys: A list of keys to remove from the logger's context.

        """
        # Also remove from our internal tracking dict
        for key in keys:
            self.binding_dict.pop(key, None)

        if hasattr(self.logger, "unbind") and hasattr(self.logger, "_context"):
            # Get keys that actually exist in the logger's context to avoid KeyError
            bound_keys = self.logger._context.keys()
            keys_to_unbind = [k for k in keys if k in bound_keys]
            if keys_to_unbind:
                self.logger = self.logger.unbind(*keys_to_unbind)

    def _setup_handlers(
        self, *, print_output: bool, log_when: str,
    ) -> tuple[AsyncTimedRotatingFileHandler | None, logging.StreamHandler | None]:
        """Create and return file and console handlers."""
        file_handler = (
            AsyncTimedRotatingFileHandler(self.log_file, when=log_when)
            if self.log_file
            else None
        )
        console_handler = logging.StreamHandler() if print_output else None
        return file_handler, console_handler

    def _setup_formatters_and_structlog(
        self,
        *,
        structlog_enabled: bool,
        json_formatter: bool,
        plain_text_format: str,
        file_handler: AsyncTimedRotatingFileHandler | None,
        console_handler: logging.StreamHandler | None,
    ) -> None:
        """Configure formatters and structlog."""
        if structlog_enabled:
            struct_processors = [
                add_logger_name,
                ExtraAdder(),
                TimeStamper(fmt="iso"),
                format_exc_info,
                EventRenamer("msg"),
            ]
            renderer = (
                JSONRenderer()
                if json_formatter
                else KeyValueRenderer(key_order=["timestamp", "level", "msg", "logger"])
            )
            processor_formatter = ProcessorFormatter(
                processor=renderer,
                foreign_pre_chain=struct_processors,
            )
            if file_handler:
                file_handler.setFormatter(processor_formatter)
            if console_handler:
                console_handler.setFormatter(processor_formatter)
            structlog.configure(
                processors=[
                    add_logger_name,
                    add_log_level,
                    TimeStamper(fmt="iso"),
                    format_exc_info,
                    EventRenamer("msg"),
                    structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
                ],
                logger_factory=LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
        else:
            plain_formatter = logging.Formatter(plain_text_format)
            if file_handler:
                file_handler.setFormatter(plain_formatter)
            if console_handler:
                console_handler.setFormatter(plain_formatter)

    def _handler_already_added(self, target_handler: logging.Handler) -> bool:
        """Check if a handler has already been added to the logger."""
        for h in list(self.logger.handlers):
            if isinstance(h, type(target_handler)):
                if hasattr(h, "baseFilename") and hasattr(
                    target_handler, "baseFilename",
                ):
                    try:
                        if str(h.baseFilename) == str(target_handler.baseFilename):
                            return True
                    except OSError:
                        pass
                elif getattr(h, "stream", None) == getattr(
                    target_handler, "stream", None,
                ):
                    return True
        return False
if __name__ == "__main__":
    import shutil

    # --- Test Suite Setup ---
    TEST_LOG_DIR = Path("./logs_test")
    test_logger = logging.getLogger("test_logger")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(logging.StreamHandler())


    def cleanup_handlers() -> None:
        """Remove all handlers from the root logger to ensure test isolation."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)


    # Clean slate before starting
    cleanup_handlers()
    if TEST_LOG_DIR.exists():
        shutil.rmtree(TEST_LOG_DIR)
    TEST_LOG_DIR.mkdir(parents=True)

    test_logger.info("--- Running Logger Test Suite ---")

    # --- Test Case 1: JSON logging with native structlog context ---
    test_logger.info("\n--- Test Case 1: JSON with native structlog context ---")
    logging_utils_json = LoggingUtils(
        log_file="demo_json.log",
        log_dir=str(TEST_LOG_DIR),
        log_level="INFO",
        print_output=True,
        json_formatter=True,
        binding_dict={"session_id": "abc-123"},
    )
    logger_json = logging_utils_json.get_logger()
    logger_json.info(
        "Trade executed via stdlib logger",
        strategy="funding_rate_arbitrage",
        symbol="BTCUSDT",
        exec_size=1.5,
    )
    test_logger.info(
        "Check %s for flattened JSON output.",
        TEST_LOG_DIR / "demo_json.log",
    )
    cleanup_handlers()  # Isolate test

    # --- Test Case 2: Plain text logging with native structlog context ---
    test_logger.info(
        "\n--- Test Case 2: Plain Text Formatting with native context ---",
    )
    logging_utils_text = LoggingUtils(
        log_file="demo_text.log",
        log_dir=str(TEST_LOG_DIR),
        log_level="INFO",
        print_output=True,
        json_formatter=False,  # KeyValueRenderer will be used
        binding_dict={"user": "abc-123"},
    )
    logger_text = logging_utils_text.get_logger()
    logger_text.warning("This is a plain-text warning.", user="test")
    test_logger.info("Check %s for key=value output.", TEST_LOG_DIR / "demo_text.log")
    cleanup_handlers()  # Isolate test

    # --- Test Case 3 & 4 require a logger to be configured, let's set one up ---
    # This will also test native structlog and exception logging
    test_logger.info(
        "\n--- Test Cases 3 & 4: Native Structlog and Exception Logging ---",
    )
    lu_for_structlog = LoggingUtils(
        log_file="demo_structlog_exceptions.log",
        log_dir=str(TEST_LOG_DIR),
        log_level="DEBUG",
        print_output=True,
        json_formatter=True,
    )
    s_logger = structlog.get_logger("structlog_native")
    s_logger.info(
        "Market data received",
        source="binance",
        latency_ms=120,
        instrument_count=53,
    )
    try:
        result = 1 / 0
    except ZeroDivisionError:
        s_logger.exception("Calculation failed")
    test_logger.info(
        "Check %s for native and exception logs.",
        TEST_LOG_DIR / "demo_structlog_exceptions.log",
    )
    cleanup_handlers()

    # --- Test Case 5: No binding_dict ---
    test_logger.info("\n--- Test Case 5: No binding_dict ---")
    logging_utils_no_bind = LoggingUtils(
        log_file="demo_no_bind.log",
        log_dir=str(TEST_LOG_DIR),
        log_level="INFO",
        print_output=True,
        json_formatter=True,
    )
    logger_no_bind = logging_utils_no_bind.get_logger()
    logger_no_bind.info("Log entry without pre-bound context", log_settings="GE")
    test_logger.info(
        "Check %s to verify 'log_settings' is present.",
        TEST_LOG_DIR / "demo_no_bind.log",
    )
    cleanup_handlers()

    # --- Test Case 6: Add and Remove Bindings ---
    test_logger.info("\n--- Test Case 6: Add and Remove Bindings ---")
    lu = LoggingUtils(
        log_file="demo_bindings.log",
        log_dir=str(TEST_LOG_DIR),
        log_level="INFO",
        print_output=True,
        binding_dict={"initial_key": "initial_value"},
    )
    log = lu.get_logger()
    log.info("Initial log with one binding")
    lu.add_bindings({"user_id": 123, "request_id": "xyz-789"})
    log.info("Log after adding two new bindings")
    lu.rm_bindings(["initial_key", "non_existent_key"])
    log.info("Log after removing one binding")
    test_logger.info(
        "Check %s to verify binding changes.",
        TEST_LOG_DIR / "demo_bindings.log",
    )
    cleanup_handlers()

    # --- User Requested Tests ---
    test_logger.info("\n--- User Requested Test 1: No log file when not provided ---")
    # The log dir is already created, but the constructor shouldn't create a file in it.
    start_files = {p.name for p in TEST_LOG_DIR.iterdir()}
    lu_no_file = LoggingUtils(log_dir=str(TEST_LOG_DIR), print_output=False)
    assert not any(
        isinstance(h, AsyncTimedRotatingFileHandler)
        for h in logging.getLogger().handlers
    ), "FAIL: File handler created when log_file was not provided."
    end_files = {p.name for p in TEST_LOG_DIR.iterdir()}
    assert start_files == end_files, "FAIL: A log file was created unexpectedly."
    test_logger.info("PASS: No file handler or log file was created.")
    cleanup_handlers()

    test_logger.info("\n--- User Requested Test 2: Daily rotation is default ---")
    lu_daily = LoggingUtils(
        log_file="test_daily.log", log_dir=str(TEST_LOG_DIR), print_output=False,
    )
    file_handler = next(
        (
            h
            for h in logging.getLogger().handlers
            if isinstance(h, AsyncTimedRotatingFileHandler)
        ),
        None,
    )
    assert file_handler is not None, "FAIL: AsyncTimedRotatingFileHandler not found."
    assert file_handler.when == "D", f"FAIL: Expected rotation 'D', but got '{file_handler.when}'"
    test_logger.info("PASS: Default rotation is daily ('D').")
    cleanup_handlers()

    test_logger.info("\n--- User Requested Test 3: Creates only one log file ---")
    lu_single = LoggingUtils(
        log_file="test_single.log", log_dir=str(TEST_LOG_DIR), print_output=False,
    )
    lu_single.get_logger().info("Test message")
    file_handlers = [
        h
        for h in logging.getLogger().handlers
        if isinstance(h, AsyncTimedRotatingFileHandler)
    ]
    assert len(file_handlers) == 1, f"FAIL: Expected 1 file handler, but found {len(file_handlers)}"
    test_logger.info("PASS: Exactly one file handler created.")
    log_path = TEST_LOG_DIR / "test_single.log"
    assert log_path.exists(), f"FAIL: Log file '{log_path}' was not created."
    test_logger.info("PASS: Log file '%s' was created.", log_path)
    cleanup_handlers()

    # --- Test Suite Teardown ---
    shutil.rmtree(TEST_LOG_DIR)
    test_logger.info("\nCleaned up test directory: %s", TEST_LOG_DIR)
    test_logger.info("\n--- Test Suite Finished ---")