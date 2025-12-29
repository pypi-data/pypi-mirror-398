"""
Tool Observer Module for Pipecat Tool Execution Monitoring.

This module provides a decorator-based approach to observe, monitor, and track
tool executions in pipecat-based applications. It captures execution context,
handles timeouts, manages callbacks, and detects issues in tool results.

Key Components:
    - ToolExecutionContext: Data class holding execution state and metrics
    - ToolObserverRegistry: Singleton registry for tracking active executions
    - observe_tool: Decorator for instrumenting tool functions

Example:
    @observe_tool(tool_name="my_tool", timeout_seconds=5.0)
    async def my_tool_handler(params: FunctionCallParams) -> dict:
        return {"status": "ok"}
"""

import asyncio
import contextlib
import functools
import inspect
import json
import time
import traceback
from collections import OrderedDict
from collections.abc import Callable
from typing import Any, TypeVar, cast

from connexity.utils.logging_config import get_logger

try:
    from pipecat.services.llm_service import FunctionCallParams
except ImportError:
    FunctionCallParams = None

# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])

# Module logger - consumers can configure this logger's level and handlers
logger = get_logger(__name__)

# Issue detection patterns for result analysis
_ISSUE_PATTERNS: frozenset[str] = frozenset({"error", "exception", "failed", "failure"})
_ISSUE_DICT_KEYS: frozenset[str] = frozenset(
    {"error", "exception", "failure", "failed"}
)


class ToolExecutionContext:
    """
    Encapsulates the complete state and metrics of a single tool execution.

    This class captures all relevant information about a tool call including
    timing metrics, results, errors, and timeout status. It uses __slots__
    for memory efficiency when handling many concurrent executions.

    Attributes:
        tool_name: Name of the tool being executed.
        tool_call_id: Unique identifier for this specific tool invocation.
        arguments: Dictionary of arguments passed to the tool.
        start_time: Unix timestamp when execution began.
        end_time: Unix timestamp when execution completed.
        duration_ms: Total execution time in milliseconds.
        result: The return value from the tool (if captured).
        issue: Exception instance if an error occurred.
        issue_traceback: Formatted traceback string for debugging.
        success: Whether the execution completed without issues.
        timeout_enabled: Whether timeout monitoring is active.
        timeout_seconds: Configured timeout duration.
        timeout_triggered: Whether execution was terminated due to timeout.
        callback_called: Whether the result callback was invoked.
    """

    __slots__ = (
        "tool_name",
        "tool_call_id",
        "arguments",
        "start_time",
        "end_time",
        "duration_ms",
        "result",
        "issue",
        "issue_traceback",
        "success",
        "timeout_enabled",
        "timeout_seconds",
        "timeout_triggered",
        "callback_called",
    )

    def __init__(self) -> None:
        """Initialize a new execution context with default values."""
        self.tool_name: str | None = None
        self.tool_call_id: str | None = None
        self.arguments: dict[str, Any] | None = None
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.duration_ms: float | None = None
        self.result: Any = None
        self.issue: Exception | None = None
        self.issue_traceback: str | None = None
        self.success: bool = True
        self.timeout_enabled: bool = False
        self.timeout_seconds: float | None = None
        self.timeout_triggered: bool = False
        self.callback_called: bool = False

    def to_dict(self) -> dict[str, Any]:
        """
        Convert context to a dictionary for serialization or logging.

        Returns:
            Dictionary containing all execution context fields with
            exception objects converted to string representations.
        """
        return {
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
            "arguments": self.arguments,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "issue": str(self.issue) if self.issue else None,
            "issue_type": type(self.issue).__name__ if self.issue else None,
            "issue_traceback": self.issue_traceback,
        }


class ToolObserverRegistry:
    """
    Thread-safe singleton registry for tracking tool execution contexts.

    Maintains an ordered collection of execution contexts indexed by tool_call_id,
    with automatic cleanup of stale entries to prevent memory leaks during
    long-running sessions.

    The registry uses an asyncio lock for thread safety in concurrent environments
    and implements automatic eviction of entries older than max_age_seconds.

    Attributes:
        _instance: Singleton instance reference.
        _executions: OrderedDict mapping tool_call_id to (context, timestamp).
        _lock: Asyncio lock for thread-safe access.
        _max_age: Maximum age in seconds before entries are eligible for cleanup.
    """

    _instance: "ToolObserverRegistry | None" = None

    def __init__(self, max_age_seconds: float = 300.0) -> None:
        """
        Initialize the registry with configurable entry lifetime.

        Args:
            max_age_seconds: Maximum time to retain execution contexts.
                Defaults to 300 seconds (5 minutes).
        """
        self._executions: OrderedDict[str, tuple[ToolExecutionContext, float]] = (
            OrderedDict()
        )
        self._lock = asyncio.Lock()
        self._max_age = max_age_seconds

    @classmethod
    def get_instance(cls) -> "ToolObserverRegistry":
        """
        Retrieve or create the singleton registry instance.

        Returns:
            The global ToolObserverRegistry instance.
        """
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("ToolObserverRegistry singleton instance created")
        return cls._instance

    async def register_execution(self, context: ToolExecutionContext) -> None:
        """
        Register a new tool execution context in the registry.

        Automatically triggers cleanup when the registry exceeds 100 entries
        to prevent unbounded memory growth.

        Args:
            context: The execution context to register. Must have a valid
                tool_call_id; contexts without IDs are silently ignored.
        """
        if not context.tool_call_id:
            logger.debug("Skipping registration: context has no tool_call_id")
            return

        async with self._lock:
            self._executions[context.tool_call_id] = (context, time.time())
            logger.debug(
                "Registered execution: tool=%s, call_id=%s",
                context.tool_name,
                context.tool_call_id,
            )
            if len(self._executions) > 100:
                await self._cleanup_old_executions()

    async def get_execution(self, tool_call_id: str) -> ToolExecutionContext | None:
        """
        Retrieve an execution context by its tool call ID.

        Args:
            tool_call_id: The unique identifier for the tool invocation.

        Returns:
            The ToolExecutionContext if found, None otherwise.
        """
        async with self._lock:
            entry = self._executions.get(tool_call_id)
            return entry[0] if entry else None

    async def clear_execution(self, tool_call_id: str) -> None:
        """
        Remove an execution context from the registry.

        Args:
            tool_call_id: The unique identifier for the tool invocation to remove.
        """
        async with self._lock:
            if self._executions.pop(tool_call_id, None):
                logger.debug("Cleared execution: call_id=%s", tool_call_id)

    async def _cleanup_old_executions(self) -> None:
        """
        Remove execution contexts that have exceeded the maximum age.

        This method is called automatically during registration when the
        registry exceeds the size threshold. It removes all entries older
        than _max_age seconds.
        """
        now = time.time()
        expired = [
            tool_call_id
            for tool_call_id, (_, created_at) in self._executions.items()
            if (now - created_at) > self._max_age
        ]

        for tool_call_id in expired:
            self._executions.pop(tool_call_id, None)

        if expired:
            logger.debug("Cleaned up %d expired execution contexts", len(expired))

    def register_execution_sync(self, context: ToolExecutionContext) -> None:
        """
        Synchronous wrapper for registering executions from sync contexts.

        Attempts to schedule the async registration on the running event loop.
        Falls back to running in a new loop if no loop is running.

        Args:
            context: The execution context to register.
        """
        if not context.tool_call_id:
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.register_execution(context))
            else:
                loop.run_until_complete(self.register_execution(context))
        except RuntimeError as e:
            logger.debug("Could not register execution synchronously: %s", e)


def _extract_tool_name(
    tool_name: str | None,
    args: tuple[Any, ...],
    func: Callable[..., Any],
) -> str:
    """
    Determine the tool name from available sources.

    Prioritizes explicitly provided name, then attempts to extract from
    schema, finally falls back to function name.

    Args:
        tool_name: Explicitly provided tool name (highest priority).
        args: Positional arguments passed to the tool function.
        func: The decorated tool function.

    Returns:
        The resolved tool name string.
    """
    if tool_name:
        return tool_name
    if args and hasattr(args[0], "schema"):
        return getattr(args[0].schema, "name", func.__name__)
    return func.__name__


def _extract_params(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> "FunctionCallParams | None":
    """
    Extract FunctionCallParams from function arguments.

    Searches both positional and keyword arguments for a FunctionCallParams
    instance, which contains the tool_call_id and result_callback.

    Args:
        args: Positional arguments to search.
        kwargs: Keyword arguments to search.

    Returns:
        The FunctionCallParams instance if found, None otherwise.
    """
    if FunctionCallParams is None:
        return None

    for arg in args:
        if isinstance(arg, FunctionCallParams):
            return arg

    for value in kwargs.values():
        if isinstance(value, FunctionCallParams):
            return value

    return None


def _detect_issue_in_result(result: Any) -> bool:
    """
    Analyze a tool result for indicators of failure or errors.

    Checks for common error patterns in the result structure including
    explicit error keys in dictionaries and error-related substrings.

    Args:
        result: The tool execution result to analyze.

    Returns:
        True if the result appears to contain an error, False otherwise.
    """
    if result is None:
        return False

    try:
        if isinstance(result, dict):
            # Fast path: check for explicit error keys
            if _ISSUE_DICT_KEYS & result.keys():
                return True
            if result.get("success") is False:
                return True
            result_str = json.dumps(result).lower()
        elif isinstance(result, str):
            result_str = result.lower()
        else:
            result_str = str(result).lower()

        return any(pattern in result_str for pattern in _ISSUE_PATTERNS)

    except (TypeError, ValueError) as e:
        logger.debug("Could not analyze result for issues: %s", e)
        return False


def _wrap_callback(
    original_callback: Callable[[Any], Any],
    context: ToolExecutionContext,
    include_result: bool,
) -> Callable[[Any], Any]:
    """
    Create a wrapper around the result callback to capture execution state.

    The wrapper intercepts callback invocations to track whether the callback
    was called and to capture the result for issue detection.

    Args:
        original_callback: The original result_callback from FunctionCallParams.
        context: The execution context to update on callback invocation.
        include_result: Whether to capture the result in the context.

    Returns:
        An async wrapper function that delegates to the original callback.
    """

    async def wrapped_callback(result: Any) -> Any:
        context.callback_called = True

        if include_result and context.result is None:
            context.result = result
            if result is None:
                context.success = False
                context.issue = Exception("Tool returned None (null)")
                logger.warning("Tool %s returned None result", context.tool_name)
            elif _detect_issue_in_result(result):
                context.success = False
                context.issue = Exception(f"Issue detected in result: {result}")
                logger.warning(
                    "Issue detected in tool %s result: %s",
                    context.tool_name,
                    result,
                )

        return await original_callback(result)

    return wrapped_callback


async def _execute_with_timeout(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    context: ToolExecutionContext,
    original_callback: Callable[[Any], Any] | None,
) -> Any:
    """
    Execute an async function with timeout enforcement.

    Uses asyncio.wait_for for proper task cancellation on timeout.
    Handles both timeout and cancellation scenarios, notifying the
    callback with appropriate error payloads.

    Args:
        func: The async tool function to execute.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        context: Execution context for tracking state.
        original_callback: Optional callback for result notification.

    Returns:
        The result of the function execution.

    Raises:
        asyncio.CancelledError: If the task was cancelled externally.
        TimeoutError: If execution exceeded the timeout threshold.
    """
    try:
        result = await asyncio.wait_for(
            func(*args, **kwargs), timeout=context.timeout_seconds
        )
        return result

    except asyncio.CancelledError:
        logger.info(
            "Tool %s execution cancelled (call_id=%s)",
            context.tool_name,
            context.tool_call_id,
        )
        if original_callback and not context.callback_called:
            context.success = False
            context.issue = Exception("Tool execution was cancelled")
            cancel_payload = {"success": False, "issue": "Tool execution was cancelled"}
            try:
                await original_callback(cancel_payload)
                context.callback_called = True
            except Exception as e:
                logger.debug("Failed to invoke callback on cancellation: %s", e)
        raise

    except TimeoutError:
        context.timeout_triggered = True
        context.success = False
        context.issue = TimeoutError(
            f"Tool execution timeout after {context.timeout_seconds}s"
        )
        logger.warning(
            "Tool %s timed out after %.1fs (call_id=%s)",
            context.tool_name,
            context.timeout_seconds,
            context.tool_call_id,
        )

        if original_callback and not context.callback_called:
            timeout_payload = {
                "success": False,
                "issue": f"Tool execution timeout after {context.timeout_seconds} seconds",
            }
            try:
                await original_callback(timeout_payload)
                context.callback_called = True
            except Exception as e:
                logger.debug("Failed to invoke callback on timeout: %s", e)

        raise


def _process_result(
    context: ToolExecutionContext,
    result: Any,
    include_result: bool,
) -> None:
    """
    Process and analyze the tool execution result.

    Captures the result in the context if configured and performs
    issue detection on the returned value.

    Args:
        context: The execution context to update.
        result: The raw result from the tool function.
        include_result: Whether to store the result in the context.
    """
    if include_result and context.result is None:
        context.result = result

        if result is None:
            context.success = False
            context.issue = Exception("Tool returned None (null)")
            logger.warning("Tool %s returned None result", context.tool_name)
        elif _detect_issue_in_result(result):
            context.success = False
            context.issue = Exception(f"Issue detected in result: {result}")
            logger.warning("Issue detected in tool %s result", context.tool_name)


async def _handle_missing_callback(
    context: ToolExecutionContext,
    original_callback: Callable[[Any], Any] | None,
) -> None:
    """
    Ensure the result callback is invoked even if the tool didn't call it.

    This safety mechanism ensures the calling system receives a response
    by invoking the callback with the captured result or an error payload.

    Args:
        context: The execution context containing result and state.
        original_callback: The result callback to potentially invoke.
    """
    if not (original_callback and not context.callback_called):
        return

    try:
        if context.result is not None:
            await original_callback(context.result)
        else:
            issue_payload = {
                "success": False,
                "issue": "Tool returned None (null) and did not call result_callback",
            }
            await original_callback(issue_payload)
        context.callback_called = True
    except Exception as e:
        logger.error(
            "Failed to invoke missing callback for tool %s: %s",
            context.tool_name,
            e,
        )

    # Mark as failure since callback should have been called by the tool
    if context.success:
        context.success = False
        if context.result is None:
            context.issue = Exception(
                "Tool returned None (null) and did not call result_callback"
            )
        else:
            context.issue = Exception(
                "Tool has result_callback available but did not call it"
            )
        logger.warning(
            "Tool %s did not invoke result_callback (call_id=%s)",
            context.tool_name,
            context.tool_call_id,
        )


def _handle_missing_callback_sync(
    context: ToolExecutionContext,
    original_callback: Callable[[Any], Any] | None,
) -> None:
    """
    Synchronous version of _handle_missing_callback for sync tool functions.

    Schedules the callback invocation on the event loop from a synchronous
    context, handling both running and non-running loop scenarios.

    Args:
        context: The execution context containing result and state.
        original_callback: The result callback to potentially invoke.
    """
    if not (
        original_callback
        and callable(original_callback)
        and not context.callback_called
    ):
        return

    async def send_result_via_callback() -> None:
        try:
            if context.result is not None:
                await original_callback(context.result)
            else:
                issue_payload = {
                    "success": False,
                    "issue": "Tool returned None (null) and did not call result_callback",
                }
                await original_callback(issue_payload)
            context.callback_called = True
        except Exception as e:
            logger.error(
                "Failed to send result via callback for tool %s: %s",
                context.tool_name,
                e,
            )

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(send_result_via_callback())
        else:
            loop.run_until_complete(send_result_via_callback())
    except RuntimeError as e:
        logger.debug("Could not schedule callback invocation: %s", e)

    # Mark as failure since callback should have been called by the tool
    if context.success:
        context.success = False
        if context.result is None:
            context.issue = Exception(
                "Tool returned None (null) and did not call result_callback"
            )
        else:
            context.issue = Exception(
                "Tool has result_callback available but did not call it"
            )
        logger.warning("Sync tool %s did not invoke result_callback", context.tool_name)


def observe_tool(
    tool_name: str | None = None,
    include_result: bool = True,
    include_traceback: bool = True,
    enable_timeout: bool = True,
    timeout_seconds: float = 10.0,
) -> Callable[[F], F]:
    """
    Decorator for observing and monitoring tool function executions.

    Wraps both async and sync tool functions to provide comprehensive
    monitoring including execution timing, result capture, error tracking,
    and timeout enforcement. Integrates with pipecat's FunctionCallParams
    for callback management.

    Args:
        tool_name: Optional explicit name for the tool. If not provided,
            attempts to extract from schema or uses the function name.
        include_result: Whether to capture and analyze the return value.
            Defaults to True.
        include_traceback: Whether to capture full tracebacks on exceptions.
            Defaults to True.
        enable_timeout: Whether to enforce execution timeouts.
            Defaults to True.
        timeout_seconds: Maximum execution time before timeout.
            Defaults to 10.0 seconds.

    Returns:
        A decorator function that wraps the target tool function.

    Example:
        @observe_tool(tool_name="weather_lookup", timeout_seconds=5.0)
        async def get_weather(params: FunctionCallParams) -> dict:
            # Tool implementation
            return {"temp": 72, "condition": "sunny"}
    """
    # Return passthrough decorator if pipecat is not available
    if FunctionCallParams is None:
        logger.debug("FunctionCallParams not available; observe_tool is a no-op")

        def passthrough_decorator(func: F) -> F:
            return func

        return passthrough_decorator

    def decorator(func: F) -> F:
        registry = ToolObserverRegistry.get_instance()

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            context = ToolExecutionContext()
            context.start_time = time.time()
            context.tool_name = _extract_tool_name(tool_name, args, func)

            params = _extract_params(args, kwargs)
            original_callback: Callable[[Any], Any] | None = None

            if enable_timeout:
                context.timeout_enabled = True
                context.timeout_seconds = timeout_seconds

            if params:
                context.tool_call_id = getattr(params, "tool_call_id", None)
                if hasattr(params, "arguments") and isinstance(params.arguments, dict):
                    context.arguments = params.arguments.copy()

                if context.tool_call_id:
                    await registry.register_execution(context)

                original_callback = getattr(params, "result_callback", None)
                if original_callback and callable(original_callback):
                    params.result_callback = _wrap_callback(
                        original_callback, context, include_result
                    )

            logger.debug(
                "Starting tool execution: %s (call_id=%s)",
                context.tool_name,
                context.tool_call_id,
            )

            try:
                if context.timeout_enabled and original_callback:
                    result = await _execute_with_timeout(
                        func, args, kwargs, context, original_callback
                    )
                else:
                    result = await func(*args, **kwargs)

                _process_result(context, result, include_result)
                return result

            except asyncio.CancelledError:
                context.success = False
                if not context.issue:
                    context.issue = Exception("Tool execution was cancelled")

                if params and original_callback and not context.callback_called:
                    cancel_payload = {
                        "success": False,
                        "issue": "Tool execution was cancelled",
                    }
                    try:
                        await original_callback(cancel_payload)
                        context.callback_called = True
                    except Exception as e:
                        logger.debug("Failed to notify callback on cancellation: %s", e)

                raise

            except TimeoutError:
                # Already handled in _execute_with_timeout
                raise

            except Exception as e:
                context.success = False
                context.issue = e

                if include_traceback:
                    context.issue_traceback = traceback.format_exc()

                logger.error(
                    "Tool %s failed with %s: %s (call_id=%s)",
                    context.tool_name,
                    type(e).__name__,
                    e,
                    context.tool_call_id,
                )

                if params and original_callback and not context.callback_called:
                    issue_payload = {
                        "success": False,
                        "issue": str(e),
                        "issue_type": type(e).__name__,
                    }
                    try:
                        await original_callback(issue_payload)
                        context.callback_called = True
                    except Exception as cb_error:
                        logger.debug(
                            "Failed to notify callback on exception: %s", cb_error
                        )

                raise

            finally:
                context.end_time = time.time()
                context.duration_ms = (context.end_time - context.start_time) * 1000

                await _handle_missing_callback(context, original_callback)

                if context.success:
                    logger.info(
                        "Tool %s completed successfully in %.1fms (call_id=%s)",
                        context.tool_name,
                        context.duration_ms,
                        context.tool_call_id,
                    )
                else:
                    logger.debug(
                        "Tool %s execution context: %s",
                        context.tool_name,
                        context.to_dict(),
                    )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            context = ToolExecutionContext()
            context.start_time = time.time()
            context.tool_name = _extract_tool_name(tool_name, args, func)

            params = _extract_params(args, kwargs)

            if enable_timeout:
                context.timeout_enabled = True
                context.timeout_seconds = timeout_seconds

            if params:
                context.tool_call_id = getattr(params, "tool_call_id", None)
                if hasattr(params, "arguments") and isinstance(params.arguments, dict):
                    context.arguments = params.arguments.copy()

                if context.tool_call_id:
                    registry.register_execution_sync(context)

            original_callback: Callable[[Any], Any] | None = None
            if params:
                original_callback = getattr(params, "result_callback", None)

            logger.debug(
                "Starting sync tool execution: %s (call_id=%s)",
                context.tool_name,
                context.tool_call_id,
            )

            timeout_task: asyncio.Task[None] | None = None
            if (
                context.timeout_enabled
                and params
                and original_callback
                and callable(original_callback)
            ):

                async def timeout_handler() -> None:
                    await asyncio.sleep(context.timeout_seconds)  # type: ignore[arg-type]
                    if context.end_time is None:
                        context.timeout_triggered = True
                        context.success = False
                        context.issue = TimeoutError(
                            f"Tool execution timeout after {context.timeout_seconds}s"
                        )
                        timeout_payload = {
                            "success": False,
                            "issue": f"Tool execution timeout after {context.timeout_seconds} seconds",
                        }
                        await original_callback(timeout_payload)  # type: ignore[misc]
                        context.callback_called = True
                        logger.warning(
                            "Sync tool %s timed out after %.1fs",
                            context.tool_name,
                            context.timeout_seconds,
                        )

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        timeout_task = asyncio.create_task(timeout_handler())
                    else:
                        timeout_task = loop.create_task(timeout_handler())
                except RuntimeError as e:
                    logger.debug("Could not create timeout task: %s", e)

            try:
                result = func(*args, **kwargs)
                _process_result(context, result, include_result)
                return result

            except Exception as e:
                context.success = False
                context.issue = e

                if include_traceback:
                    context.issue_traceback = traceback.format_exc()

                logger.error(
                    "Sync tool %s failed with %s: %s",
                    context.tool_name,
                    type(e).__name__,
                    e,
                )

                raise

            finally:
                context.end_time = time.time()
                context.duration_ms = (context.end_time - context.start_time) * 1000

                _handle_missing_callback_sync(context, original_callback)

                if timeout_task and not timeout_task.done():
                    with contextlib.suppress(Exception):
                        timeout_task.cancel()

                if context.success:
                    logger.info(
                        "Sync tool %s completed successfully in %.1fms",
                        context.tool_name,
                        context.duration_ms,
                    )

        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
