"""Debugging utilities for OpenDAPI"""

import logging
import os
import sys
import tempfile
import time
from enum import Enum
from importlib.metadata import version
from typing import Optional

import sentry_sdk
from deepmerge import always_merger

DAPI_API_KEY_HEADER = "X-DAPI-Server-API-Key"
WOVEN_DENY_LIST = sentry_sdk.scrubber.DEFAULT_DENYLIST + [DAPI_API_KEY_HEADER]


def _create_logfile() -> Optional[str]:
    """Create a temporary log file and return the path"""
    try:
        with tempfile.NamedTemporaryFile(
            prefix="opendapi_pipeline_", delete=False
        ) as temp_file:
            return temp_file.name
    except (FileNotFoundError, PermissionError):
        return None


LOG_FILENAME = _create_logfile()
ADDITIONAL_LOGFILES = [os.environ.get("BUILDKITE_JOB_LOG_TMPFILE")]


def _reset_logs() -> None:
    """Clear up the logs in the log file"""
    if LOG_FILENAME is not None:
        with open(LOG_FILENAME, "w", encoding="utf-8"):
            pass


def _get_logs() -> Optional[str]:
    """Get the logs from the log file"""
    logs = ""
    logfiles = [LOG_FILENAME, *ADDITIONAL_LOGFILES]

    for logfile in logfiles:
        if logfile:
            with open(logfile, "r", encoding="utf-8") as f:
                content = f.read()
                content += "\n" if content else ""
                logs += content
    return logs or None


class LogDistKey(Enum):
    """Set of Dist keys for logging"""

    ASK_DAPI_SERVER = "ask_dapi_server"
    CLI_INIT = "cli_init"
    CLI_GENERATE = "cli_generate"
    CLI_ENRICH = "cli_enrich"
    CLI_REGISTER = "cli_register"
    CLI_SERVER_SYNC = "cli_server_sync"
    VALIDATE_AND_COLLECT = "validate_and_collect"
    COLLECT_FILES = "collect_files"
    PERSIST_COLLECTED_FILES = "persist_collected_files"
    LOAD_COLLECTED_FILES = "load_collected_files"
    SERVER_SYNC_TO_SERVER = "server_sync_to_server"
    WRITE_FILES = "write_files"


class LogCounterKey(Enum):
    """Set of Counter keys for logging"""

    ASK_DAPI_SERVER_PAYLOAD_ITEMS = "ask_dapi_server_payload_items"
    VALIDATOR_ERRORS = "validator_errors"
    VALIDATOR_ITEMS = "validator_items"
    USER_PR_CREATED = "user_pr_created"
    SUGGESTIONS_PR_CREATED = "suggestions_pr_created"
    SUGGESTIONS_FILE_COUNT = "suggestions_file_count"


class Timer:
    """A context manager to measure the time taken for a block of code and publish to sentry."""

    def __init__(self, dist_key: LogDistKey, tags=None) -> None:
        """Initialize the timer"""
        self.dist_key = dist_key
        self.tags = tags
        self.start = None

    def __enter__(self):
        """Start the timer"""
        self.start = time.time()
        return self

    def set_tags(self, tags):
        """Set tags for the timer"""
        self.tags = always_merger.merge(self.tags, tags)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the timer and log the distribution metric to sentry."""
        _end = time.time()
        _elapsed = _end - self.start
        key_name = (
            self.dist_key.value
            if isinstance(self.dist_key, LogDistKey)
            else self.dist_key
        )
        logger.info(
            "Timer %s took %s milliseconds",
            key_name,
            _elapsed * 1000,
            extra={
                "key": key_name,
                "elapsed": _elapsed * 1000,
                "tags": self.tags,
            },
        )


def increment_counter(key: LogCounterKey, value: int = 1, tags: dict = None):
    """Increment a counter metric in sentry."""
    key_name = key.value if isinstance(key, LogCounterKey) else key
    logger.info(
        "Counter %s incremented by %s",
        key_name,
        value,
        extra={
            "key": key_name,
            "value": value,
            "tags": tags,
        },
    )


def sentry_init(
    sentry_config: dict,
    tags: dict = None,
):
    """Initialize sentry, but silently fail in case of errors"""
    # Silently return if we don't have the required information
    sentry_config["release"] = version("opendapi")
    sentry_config["event_scrubber"] = sentry_sdk.scrubber.EventScrubber(
        denylist=WOVEN_DENY_LIST,
        recursive=True,
    )
    sentry_sdk.init(**sentry_config)

    # Set sentry tags
    sentry_tags = tags or {}
    for tag, value in sentry_tags.items():
        sentry_sdk.set_tag(tag, value)


class OpenDAPILogger(logging.Logger):
    """Custom logger class for OpenDAPI."""

    # Add specific things here later such as timers


def setup_logger(name="opendapi") -> OpenDAPILogger:
    """Setup the logger for the application."""

    logging.setLoggerClass(OpenDAPILogger)
    _logger = logging.getLogger(name)

    # Need to set explicitly for sentry to capture info+ logs
    # Note that each handler will set their own levels
    _logger.setLevel(logging.INFO)

    # Do not propagate to the root logger
    _logger.propagate = False

    if _logger.hasHandlers():
        _logger.handlers = []  # pragma: no cover

    if LOG_FILENAME is not None:
        file_handler = logging.FileHandler(LOG_FILENAME, encoding="utf-8")
        # Because we want to capture as much info in the logfile
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s"
            )
        )
        _logger.addHandler(file_handler)
        _logger.info("Enabling file handler")

    _logger.get_logs = _get_logs
    _logger.reset_logs = _reset_logs

    # Add the std out stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    # Because we do not want to show trivial logs
    # all UX message should be done through print_cli_output
    stream_handler.setLevel(logging.ERROR)
    _logger.addHandler(stream_handler)

    return _logger


logger: OpenDAPILogger = setup_logger()
