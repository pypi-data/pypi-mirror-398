from __future__ import annotations

"""
Copyright (C) 2025 Luciano Guerche

This file is part of rabbitmq-mcp-server.

rabbitmq-mcp-server is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

rabbitmq-mcp-server is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with rabbitmq-mcp-server. If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import atexit
import functools
import logging
import signal
import sys
import threading
import time
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, cast

import orjson
import structlog
import structlog.stdlib
import structlog.types

from models.log_config import LogConfig, LogLevel
from models.log_entry import LogCategory
from utils.async_writer import AsyncLogWriter

from .handlers.console import ConsoleLogHandler
from .handlers.file import FileLogHandler
from .processors import add_correlation_id, redact_sensitive_data

__all__ = [
    "configure_structlog",
    "get_logger",
    "log_duration",
    "log_timing",
    "reset_structlog_configuration",
    "shutdown_all_loggers",
    "StructuredLogger",
]

F = TypeVar("F", bound=Callable[..., Any])


_STRUCTLOG_CONFIGURED = False
_LOGGER_REGISTRY: dict[str, _LoggerState] = {}
_REGISTRY_LOCK = threading.Lock()
_LOGGER_NAME_FIELD = "_logger_name"
_SIGNAL_HANDLERS_REGISTERED = False

_METHOD_TO_LEVEL = {
    "error": LogLevel.ERROR,
    "exception": LogLevel.ERROR,
    "warning": LogLevel.WARN,
    "warn": LogLevel.WARN,
    "info": LogLevel.INFO,
    "debug": LogLevel.DEBUG,
}

_LEVEL_TO_NUM = {
    LogLevel.ERROR: logging.ERROR,
    LogLevel.WARN: logging.WARNING,
    LogLevel.INFO: logging.INFO,
    LogLevel.DEBUG: logging.DEBUG,
}


def _json_serializer(obj: structlog.types.EventDict, **kwargs: Any) -> str:
    default = kwargs.pop("default", str)
    event = dict(obj)

    timestamp = event.get("timestamp")
    if isinstance(timestamp, str) and timestamp.endswith("+00:00"):
        event["timestamp"] = f"{timestamp[:-6]}Z"

    event.setdefault("schema_version", "1.0.0")

    dispatched = _dispatch_to_log_manager(None, "", event)
    return orjson.dumps(dispatched, default=default).decode("utf-8")


def _dispatch_to_log_manager(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    manager_name = event_dict.pop(_LOGGER_NAME_FIELD, None)
    if not manager_name:
        return event_dict

    state = _LOGGER_REGISTRY.get(manager_name)
    if not state:
        return event_dict

    try:
        state.emit(dict(event_dict))
    except Exception:
        # Fallback to console to avoid losing logs if file handling breaks unexpectedly.
        state.console_handler.write_batch([dict(event_dict)])
    return event_dict


def configure_structlog(*, logger_factory: Any | None = None) -> None:
    global _STRUCTLOG_CONFIGURED
    if _STRUCTLOG_CONFIGURED:
        return

    if logger_factory is None:
        logger_factory = structlog.PrintLoggerFactory()

    processor_chain = [
        cast(
            structlog.types.Processor,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        ),
        cast(structlog.types.Processor, add_correlation_id),
        cast(structlog.types.Processor, redact_sensitive_data),
        cast(structlog.types.Processor, structlog.processors.StackInfoRenderer()),
        cast(structlog.types.Processor, structlog.processors.format_exc_info),
        cast(
            structlog.types.Processor,
            structlog.processors.JSONRenderer(serializer=_json_serializer),
        ),
    ]

    structlog.configure(
        processors=processor_chain,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=logger_factory,
        cache_logger_on_first_use=True,
    )

    _STRUCTLOG_CONFIGURED = True


def get_logger(name: str = "rabbitmq-mcp", *, config: LogConfig | None = None) -> StructuredLogger:
    """
    Get or create a structured logger.

    Automatically registers signal handlers for graceful shutdown on first call.

    Args:
        name: Logger name (default: "rabbitmq-mcp")
        config: Optional logger configuration

    Returns:
        StructuredLogger instance with configured handlers
    """
    configure_structlog()
    _register_signal_handlers()

    existing_config: LogConfig | None = None
    with _REGISTRY_LOCK:
        current_state = _LOGGER_REGISTRY.get(name)
        if current_state is not None:
            existing_config = current_state.config

    if config is None:
        config = existing_config if existing_config is not None else LogConfig()  # type: ignore[call-arg]

    state = _get_or_create_state(name, config)
    bound = structlog.get_logger(name)
    return StructuredLogger(bound, state)


def reset_structlog_configuration() -> None:
    global _STRUCTLOG_CONFIGURED
    shutdown_all_loggers()
    structlog.reset_defaults()
    _STRUCTLOG_CONFIGURED = False


def shutdown_all_loggers() -> None:
    """
    Gracefully shutdown all active loggers, flushing buffered logs.

    This function ensures zero log loss by blocking until all buffered
    logs are written to their destinations. Called automatically on:
    - Normal program exit (via atexit)
    - SIGTERM signal (graceful shutdown request)
    - SIGINT signal (Ctrl+C)

    Thread-safe and idempotent.
    """
    _shutdown_all_loggers()


def _shutdown_all_loggers() -> None:
    with _REGISTRY_LOCK:
        states = list(_LOGGER_REGISTRY.values())
        _LOGGER_REGISTRY.clear()
    for state in states:
        state.shutdown()


def _register_signal_handlers() -> None:
    """
    Register signal handlers for graceful shutdown.

    Registers handlers for:
    - SIGTERM: Graceful shutdown (Docker, systemd, kill)
    - SIGINT: Ctrl+C in terminal
    - atexit: Normal program exit

    Only registers once (idempotent).
    """
    global _SIGNAL_HANDLERS_REGISTERED

    if _SIGNAL_HANDLERS_REGISTERED:
        return

    # Register atexit handler for normal program exit
    atexit.register(_shutdown_all_loggers)

    # Register signal handlers (Unix/Linux/macOS only)
    if sys.platform != "win32":

        def _signal_handler(signum: int, frame: Any) -> None:
            """Handle shutdown signals gracefully."""
            _shutdown_all_loggers()
            # Re-raise signal to allow default handler to run
            signal.signal(signum, signal.SIG_DFL)
            signal.raise_signal(signum)

        # SIGTERM: Graceful shutdown request
        signal.signal(signal.SIGTERM, _signal_handler)

        # SIGINT: Ctrl+C
        signal.signal(signal.SIGINT, _signal_handler)

    _SIGNAL_HANDLERS_REGISTERED = True


def _get_or_create_state(name: str, config: LogConfig) -> _LoggerState:
    with _REGISTRY_LOCK:
        existing = _LOGGER_REGISTRY.get(name)
        if existing is not None:
            existing.ensure_compatible(config)
            return existing

        state = _LoggerState(name, config)
        _LOGGER_REGISTRY[name] = state
        return state


def _resolve_output_path(config: LogConfig) -> Path:
    template = config.output_file
    if "{date}" in template:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        template = template.format(date=today)
    return Path(template).expanduser().resolve()


class _AsyncWriterRunner:
    def __init__(self, writer: AsyncLogWriter) -> None:
        self._writer = writer
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._started = False
        self._start_lock = threading.Lock()

    def start(self) -> None:
        with self._start_lock:
            if self._started:
                return
            self._thread.start()
            asyncio.run_coroutine_threadsafe(self._writer.start(), self._loop).result()
            self._started = True

    def submit(self, entry: dict[str, Any]) -> None:
        if not self._started:
            raise RuntimeError("Async writer not started")
        asyncio.run_coroutine_threadsafe(self._writer.write_log(entry), self._loop).result()

    def flush(self) -> None:
        if not self._started:
            return
        asyncio.run_coroutine_threadsafe(self._writer.flush(), self._loop).result()

    def drain_pending(self) -> list[dict[str, Any]]:
        return self._writer.drain_pending()

    def stop(self, *, timeout: float = 30.0) -> None:
        """
        Stop the async writer with graceful shutdown.

        Args:
            timeout: Maximum time to wait for flush completion (seconds).
        """
        if not self._started:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._writer.stop(timeout=timeout), self._loop).result(
                timeout=timeout + 1.0
            )
        except Exception:
            # Force stop if graceful shutdown fails
            pass
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2.0)
            if self._thread.is_alive():
                # Thread didn't stop - log warning but continue
                pass
            self._loop.close()
            self._started = False

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()


class _LoggerState:
    def __init__(self, name: str, config: LogConfig) -> None:
        self.name = name
        self.config = config
        self.console_handler = ConsoleLogHandler()

        fallback = self.console_handler.write_batch if config.fallback_to_console else None
        self.file_path = _resolve_output_path(config)
        self.file_handler = FileLogHandler(self.file_path, fallback=fallback, config=config)

        # Initialize RabbitMQ handler if enabled
        self.rabbitmq_handler: Any | None = None
        if config.rabbitmq.enabled:
            try:
                from .handlers.rabbitmq import RabbitMQLogHandler

                self.rabbitmq_handler = RabbitMQLogHandler(
                    host=config.rabbitmq.host,
                    port=config.rabbitmq.port,
                    vhost=config.rabbitmq.vhost,
                    username=config.rabbitmq.username,
                    password=config.rabbitmq.password,
                    exchange=config.rabbitmq.exchange,
                    exchange_type=config.rabbitmq.exchange_type,
                    durable=config.rabbitmq.durable,
                    fallback_to_console=config.fallback_to_console,
                )
            except Exception as exc:
                print(
                    f"WARNING: Failed to initialize RabbitMQ handler: {exc}. "
                    f"RabbitMQ logging disabled.",
                    file=sys.stderr,
                )

        async def _write_batch(entries: Iterable[dict[str, Any]]) -> None:
            batch = list(entries)
            if not batch:
                return

            # Write to file handler
            try:
                await asyncio.to_thread(self.file_handler.write_batch, batch)
            except Exception:
                await asyncio.to_thread(self.console_handler.write_batch, batch)

            # Write to RabbitMQ handler if enabled
            if self.rabbitmq_handler is not None:
                try:
                    await asyncio.to_thread(self.rabbitmq_handler.write_batch, batch)
                except Exception:
                    # Failure logged by RabbitMQ handler itself
                    pass

        self._writer = AsyncLogWriter(
            max_queue_size=config.async_queue_size,
            flush_interval=config.async_flush_interval,
            batch_size=config.batch_size,
            write_batch=_write_batch,
        )
        self._runner = _AsyncWriterRunner(self._writer)
        self._lock = threading.Lock()
        self._started = False

    def ensure_compatible(self, config: LogConfig) -> None:
        if config.model_dump() != self.config.model_dump():
            raise ValueError(f"Logger '{self.name}' already configured with different settings.")

    def ensure_started(self) -> None:
        with self._lock:
            if self._started:
                return
            self._runner.start()
            self._started = True

    def set_log_level(self, level: LogLevel) -> None:
        """
        Change the minimum log level at runtime (thread-safe).

        Args:
            level: New minimum log level
        """
        with self._lock:
            self.config.log_level = level

    def emit(self, event: dict[str, Any]) -> None:
        self.ensure_started()
        self._runner.submit(dict(event))

    def flush(self) -> None:
        if not self._started:
            return
        self._runner.flush()

    def shutdown(self) -> None:
        pending_entries: list[dict[str, Any]] = []
        with self._lock:
            if not self._started:
                pending_entries = self._runner.drain_pending()
            else:
                self._runner.stop()
                self._started = False
                pending_entries = self._runner.drain_pending()

        if pending_entries:
            try:
                self.file_handler.write_batch(pending_entries)
            except Exception:
                self.console_handler.write_batch(pending_entries)
            if self.rabbitmq_handler is not None:
                try:
                    self.rabbitmq_handler.write_batch(pending_entries)
                except Exception:
                    pass

        self.file_handler.flush()
        self.file_handler.close()
        if self.rabbitmq_handler is not None:
            try:
                self.rabbitmq_handler.close()
            except Exception:
                pass


class StructuredLogger:
    """Adapter that enforces structured logging semantics for this project."""

    __slots__ = ("_logger", "_state")

    def __init__(self, logger: Any, state: _LoggerState) -> None:
        self._logger = logger
        self._state = state

    def bind(self, **new_values: Any) -> StructuredLogger:
        return StructuredLogger(self._logger.bind(**new_values), self._state)

    def new(self, **new_values: Any) -> StructuredLogger:
        return StructuredLogger(self._logger.new(**new_values), self._state)

    def debug(self, message: str, *, category: LogCategory | str, **kwargs: Any) -> Any:
        return self._log("debug", message, category=category, **kwargs)

    def info(self, message: str, *, category: LogCategory | str, **kwargs: Any) -> Any:
        return self._log("info", message, category=category, **kwargs)

    def warning(self, message: str, *, category: LogCategory | str, **kwargs: Any) -> Any:
        return self._log("warning", message, category=category, **kwargs)

    def warn(self, message: str, *, category: LogCategory | str, **kwargs: Any) -> Any:
        return self.warning(message, category=category, **kwargs)

    def error(self, message: str, *, category: LogCategory | str, **kwargs: Any) -> Any:
        return self._log("error", message, category=category, **kwargs)

    def exception(self, message: str, *, category: LogCategory | str, **kwargs: Any) -> Any:
        kwargs.setdefault("exc_info", True)
        return self._log("exception", message, category=category, **kwargs)

    def flush(self) -> None:
        self._state.flush()

    def shutdown(self) -> None:
        self._state.shutdown()

    def set_log_level(self, level: LogLevel) -> None:
        """
        Change the minimum log level at runtime.

        Args:
            level: New minimum log level (DEBUG, INFO, WARN, ERROR)
        """
        self._state.set_log_level(level)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._logger, item)

    def _log(
        self, method_name: str, message: str, *, category: LogCategory | str, **kwargs: Any
    ) -> Any:
        if category is None:
            raise ValueError("category is required for structured logging")

        log_level = _METHOD_TO_LEVEL.get(method_name)
        if log_level is None:
            raise ValueError(f"Unsupported log method '{method_name}'")

        if _LEVEL_TO_NUM[log_level] < _LEVEL_TO_NUM[self._state.config.log_level]:
            return None

        if "category" in kwargs:
            raise ValueError("'category' must be provided as named argument, not inside kwargs")

        category_value = category.value if isinstance(category, LogCategory) else str(category)

        payload = dict(kwargs)
        payload["category"] = category_value
        payload[_LOGGER_NAME_FIELD] = self._state.name

        return getattr(self._logger, method_name)(message, **payload)


@contextmanager
def log_duration(
    logger: StructuredLogger,
    operation: str,
    *,
    level: str = "info",
    category: LogCategory | str = LogCategory.PERFORMANCE,
    **kwargs: Any,
) -> Any:
    """
    Context manager for automatically logging operation duration.

    Usage:
        with log_duration(logger, "database_query", user_id=123):
            # ... operation ...
            pass

    Args:
        logger: StructuredLogger instance to use
        operation: Human-readable operation name
        level: Log level (debug, info, warning, error)
        category: Log category (defaults to Performance)
        **kwargs: Additional fields to include in the log entry
    """
    start_time = time.perf_counter()
    try:
        yield
        duration_ms = (time.perf_counter() - start_time) * 1000
        log_method = getattr(logger, level)
        log_method(
            f"Operation completed: {operation}",
            category=category,
            duration_ms=round(duration_ms, 2),
            operation_result="success",
            **kwargs,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"Operation failed: {operation}",
            category=category,
            duration_ms=round(duration_ms, 2),
            operation_result="error",
            error_type=type(exc).__name__,
            error_message=str(exc),
            **kwargs,
        )
        raise


def log_timing(
    operation: str | None = None,
    *,
    logger_name: str = "rabbitmq-mcp",
    level: str = "info",
    category: LogCategory | str = LogCategory.PERFORMANCE,
    **log_kwargs: Any,
) -> Callable[[F], F]:
    """
    Decorator for automatically logging function execution duration.

    Usage:
        @log_timing
        async def slow_operation():
            await asyncio.sleep(0.1)

        @log_timing(operation="custom_name", level="debug")
        def fast_operation():
            pass

    Args:
        operation: Operation name (defaults to function name)
        logger_name: Logger name to use
        level: Log level (debug, info, warning, error)
        category: Log category (defaults to Performance)
        **log_kwargs: Additional fields to include in log entries
    """

    def decorator(func: F) -> F:
        op_name = operation if operation is not None else func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(logger_name)
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                log_method = getattr(logger, level)
                log_method(
                    f"Operation completed: {op_name}",
                    category=category,
                    duration_ms=round(duration_ms, 2),
                    operation_result="success",
                    **log_kwargs,
                )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"Operation failed: {op_name}",
                    category=category,
                    duration_ms=round(duration_ms, 2),
                    operation_result="error",
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    **log_kwargs,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger(logger_name)
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                log_method = getattr(logger, level)
                log_method(
                    f"Operation completed: {op_name}",
                    category=category,
                    duration_ms=round(duration_ms, 2),
                    operation_result="success",
                    **log_kwargs,
                )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"Operation failed: {op_name}",
                    category=category,
                    duration_ms=round(duration_ms, 2),
                    operation_result="error",
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    **log_kwargs,
                )
                raise

        # Return async wrapper if function is coroutine, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        else:
            return sync_wrapper  # type: ignore[return-value]

    return decorator


atexit.register(_shutdown_all_loggers)
