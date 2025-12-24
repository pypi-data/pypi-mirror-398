"""
Client Wrapper

Proxy-based wrapper that intercepts client method calls
to capture telemetry and evaluate policies.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

from .constants import SDK_LANGUAGE, SDK_VERSION
from .normalizer import normalize_data
from .providers import detect_provider, detect_event_type, get_api_type
from .types import (
    OximyConfig,
    OximyEvent,
    OximyState,
    PolicyViolation,
    RequestContext,
    StreamingInfo,
)
from .utils import generate_event_id, get_timestamp, is_async_iterable
from .policy import PolicyManager
from .policy.evaluator import extract_target_content
from .types import OximyPolicyError


def buffer_stream(
    stream: AsyncIterator[Any],
) -> tuple[AsyncIterator[Any], asyncio.Future, dict[str, float | None]]:
    """Creates a buffered stream that collects items as they're consumed."""
    items: list[Any] = []
    first_chunk_time: dict[str, float | None] = {"value": None}
    future: asyncio.Future[dict[str, Any]] = asyncio.Future()

    async def buffered() -> AsyncIterator[Any]:
        error: Exception | None = None
        try:
            async for chunk in stream:
                # Record time of first chunk
                if first_chunk_time["value"] is None:
                    first_chunk_time["value"] = time.time() * 1000  # milliseconds

                items.append(chunk)
                yield chunk
            
            # Stream completed successfully
            if not future.done():
                future.set_result({
                    "items": items,
                    "completed": True,
                    "error": None,
                })
        except Exception as e:
            error = e
            if not future.done():
                future.set_result({
                    "items": items,
                    "completed": False,
                    "error": error,
                })
            raise

    return buffered(), future, first_chunk_time


def extract_oximy_context(args: tuple[Any, ...], kwargs: dict[str, Any]) -> RequestContext | None:
    """Extracts Oximy context from the second argument or kwargs."""
    # Check kwargs first
    if "oximy" in kwargs:
        context = kwargs["oximy"]
        if isinstance(context, dict):
            return context  # type: ignore
        return None

    # Check second positional argument
    if len(args) >= 2:
        second_arg = args[1]
        if isinstance(second_arg, dict) and "oximy" in second_arg:
            return second_arg["oximy"]  # type: ignore

    return None


def create_policy_error(violation: PolicyViolation) -> OximyPolicyError:
    """Creates a policy error."""
    return OximyPolicyError(violation)


def merge_stream_chunks(chunks: list[Any]) -> Any:
    """Merges streaming chunks into a single response object for normalization."""
    if not chunks:
        return None

    # Try to merge OpenAI-style streaming chunks
    merged: dict[str, Any] = {}
    content = ""
    finish_reason: str | None = None
    usage: Any = None

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        # Copy top-level fields from first chunk
        if not merged:
            for key, value in chunk.items():
                if key not in ("choices", "delta"):
                    merged[key] = value

        # Extract usage (usually in last chunk)
        if "usage" in chunk:
            usage = chunk["usage"]

        # Extract content from choices
        if "choices" in chunk and isinstance(chunk["choices"], list):
            for choice in chunk["choices"]:
                if isinstance(choice, dict):
                    delta = choice.get("delta", {})
                    if isinstance(delta, dict):
                        delta_content = delta.get("content")
                        if isinstance(delta_content, str):
                            content += delta_content

                    if "finish_reason" in choice and isinstance(choice["finish_reason"], str):
                        finish_reason = choice["finish_reason"]

    # Build merged response
    merged["choices"] = [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
            },
            "finish_reason": finish_reason,
        }
    ]

    if usage:
        merged["usage"] = usage

    return merged


class WrappedClient:
    """Proxy wrapper that intercepts method calls for telemetry."""

    def __init__(
        self,
        client: Any,
        send_event: Callable[[OximyEvent], None],
        config: OximyConfig,
        state: OximyState,
        debug: Callable[..., None],
        policy_manager: PolicyManager | None = None,
        path: list[str] | None = None,
    ):
        self._client = client
        self._send_event = send_event
        self._config = config
        self._state = state
        self._debug = debug
        self._policy_manager = policy_manager
        self._path = path or []

    def __getattr__(self, name: str) -> Any:
        """Intercepts attribute access to wrap methods and nested objects."""
        try:
            attr = getattr(self._client, name)
        except AttributeError:
            raise AttributeError(f"'{type(self._client).__name__}' object has no attribute '{name}'")

        # Check if it's a bound method (has __self__ and __func__)
        is_bound_method = hasattr(attr, "__self__") and hasattr(attr, "__func__")
        
        # Check if it's callable (function, method, or callable mock)
        is_callable = callable(attr) and not isinstance(attr, type)
        is_mock = type(attr).__name__ in ("MagicMock", "Mock", "AsyncMock")
        
        # For mocks: determine if it's an object or method
        # Heuristic: AsyncMock is always a method
        # MagicMock: if it has _mock_children (attributes set on it), it's an object
        # Otherwise, if callable and return_value/side_effect is set, it's a method
        if is_mock:
            mock_type = type(attr).__name__
            
            if mock_type == "AsyncMock":
                # AsyncMock is always a method
                if is_callable:
                    return self._wrap_method(attr, name)
            
            if mock_type in ("MagicMock", "Mock"):
                # Check if it has children (attributes explicitly set)
                # _mock_children is a dict of attributes that were set
                has_children = hasattr(attr, "_mock_children") and attr._mock_children
                
                # If it has children, it's an object
                if has_children:
                    return WrappedClient(
                        attr,
                        self._send_event,
                        self._config,
                        self._state,
                        self._debug,
                        self._policy_manager,
                        self._path + [name],
                    )
                
                # If it's callable and has return_value or side_effect, it's a method
                if is_callable and (hasattr(attr, "return_value") or hasattr(attr, "side_effect")):
                    return self._wrap_method(attr, name)
                
                # Default for MagicMock: if callable, treat as method; otherwise as object
                if is_callable:
                    return self._wrap_method(attr, name)
                else:
                    return WrappedClient(
                        attr,
                        self._send_event,
                        self._config,
                        self._state,
                        self._debug,
                        self._policy_manager,
                        self._path + [name],
                    )
        
        # Priority: If it's callable, treat as method
        if is_callable:
            if is_bound_method:
                return self._wrap_method(attr, name)
            # Non-mock callable: definitely a method
            return self._wrap_method(attr, name)

        # Not callable: treat as object if it's a mock or has attributes
        if is_mock or (hasattr(attr, "__dict__") and not is_bound_method):
            return WrappedClient(
                attr,
                self._send_event,
                self._config,
                self._state,
                self._debug,
                self._policy_manager,
                self._path + [name],
            )

        # If it's an object (but not a string, list, etc.), create a nested wrapper
        if isinstance(attr, object) and not isinstance(attr, (str, int, float, bool, list, tuple, type(None), type)):
            return WrappedClient(
                attr,
                self._send_event,
                self._config,
                self._state,
                self._debug,
                self._policy_manager,
                self._path + [name],
            )

        # Return value as-is for primitives, arrays, etc.
        return attr

    def _wrap_method(self, method: Callable[..., Any], name: str) -> Callable[..., Any]:
        """Wraps a method to capture telemetry and evaluate policies."""
        method_path = ".".join(self._path + [name])
        provider = detect_provider(self._client)

        async def wrapped_async(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time() * 1000  # milliseconds
            timestamp = get_timestamp()
            event_id = generate_event_id()
            request_input = args[0] if args else {}
            oximy_context = extract_oximy_context(args, kwargs)

            # Detect event type from method path
            event_type = detect_event_type(method_path)  # type: ignore
            api_type = get_api_type(method_path)

            self._debug("Intercepted call:", method_path, event_id)

            # Collect all policy violations
            all_violations: list[PolicyViolation] = []

            # =========================================================================
            # INPUT POLICY EVALUATION
            # =========================================================================
            if self._policy_manager and self._policy_manager.is_enabled():
                try:
                    input_result = await self._policy_manager.evaluate_input(request_input)

                    if input_result.violations:
                        all_violations.extend(input_result.violations)

                        # Fire violation callback for each
                        for violation in input_result.violations:
                            if self._config.on_policy_violation:
                                self._config.on_policy_violation(violation)

                    # If blocked, throw error
                    if not input_result.allowed and input_result.blocked:
                        self._debug("Request blocked by policy:", input_result.blocked.get("rule_name"))
                        raise create_policy_error(
                            PolicyViolation(
                                rule_id=input_result.blocked.get("rule_id", ""),
                                rule_name=input_result.blocked.get("rule_name", ""),
                                action="block",
                                severity="high",
                                message=input_result.blocked.get("message"),
                            )
                        )

                    # If modified (redacted), use modified request
                    if input_result.modified_request:
                        request_input = input_result.modified_request
                        args = (request_input,) + args[1:]

                except OximyPolicyError:
                    raise
                except Exception as err:
                    # Fail-open for other errors
                    self._debug("Policy evaluation error:", err)

            # =========================================================================
            # STREAMING USAGE OPTIMIZATION
            # =========================================================================
            if isinstance(request_input, dict) and api_type in ("chat.completions", "completions"):
                if request_input.get("stream") is True:
                    # Merge with existing stream_options if present
                    existing_stream_options = request_input.get("stream_options", {})
                    if not isinstance(existing_stream_options, dict):
                        existing_stream_options = {}
                    request_input["stream_options"] = {
                        **existing_stream_options,
                        "include_usage": True,
                    }
                    # Update args
                    args = (request_input,) + args[1:]

            response: Any = None
            error: Exception | None = None
            streaming_info: StreamingInfo | None = None

            try:
                # Execute original method
                if asyncio.iscoroutinefunction(method):
                    response = await method(*args, **kwargs)
                else:
                    response = method(*args, **kwargs)

                # Handle streaming responses
                if is_async_iterable(response):
                    stream, collected_future, first_chunk_time = buffer_stream(response)

                    # Send telemetry after stream completes (fire and forget)
                    async def send_stream_telemetry() -> None:
                        try:
                            result = await collected_future
                            end_time = time.time() * 1000

                            # Build streaming info
                            streaming_info = StreamingInfo(
                                enabled=True,
                                chunk_count=len(result["items"]),
                                completed=result["completed"],
                                interrupted_reason="error" if result.get("error") else None,
                            )

                            # Merge all chunks for normalization
                            merged_response = merge_stream_chunks(result["items"])
                            normalized = normalize_data(request_input, merged_response, provider, event_type)  # type: ignore

                            # Evaluate output policies (async, non-blocking for streaming)
                            if self._policy_manager and self._policy_manager.is_enabled():
                                try:
                                    output_result = await self._policy_manager.evaluate_output(merged_response)
                                    if output_result.violations:
                                        all_violations.extend(output_result.violations)
                                        for violation in output_result.violations:
                                            if self._config.on_policy_violation:
                                                self._config.on_policy_violation(violation)
                                except Exception:
                                    # Fail-open
                                    pass

                            ttft_ms = None
                            if first_chunk_time["value"]:
                                ttft_ms = int(first_chunk_time["value"] - start_time)

                            event: OximyEvent = {
                                "id": event_id,
                                "timestamp": timestamp,
                                "source": {
                                    "sdk_version": SDK_VERSION,
                                    "sdk_language": SDK_LANGUAGE,
                                    "provider": provider,  # type: ignore
                                    "api_type": api_type,
                                    "event_type": event_type,  # type: ignore
                                },
                                "raw": {
                                    "request": request_input,
                                    "response": result["items"],
                                },
                                "normalized": normalized,
                                "timing": {
                                    "started_at": datetime.fromtimestamp(start_time / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
                                    "ended_at": datetime.fromtimestamp(end_time / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
                                    "duration_ms": int(end_time - start_time),
                                    "ttft_ms": ttft_ms,
                                },
                                "outcome": {
                                    "success": not result.get("error"),
                                    "finish_reason": normalized.get("output", {}).get("finish_reason") if normalized else None,
                                    "error": {
                                        "type": result["error"].__class__.__name__,
                                        "message": str(result["error"]),
                                    } if result.get("error") else None,
                                },
                                "streaming": streaming_info,
                            }

                            # Add context
                            if oximy_context:
                                event["context"] = {
                                    "user_id": oximy_context.get("user_id"),
                                    "session_id": oximy_context.get("session_id"),
                                    "trace_id": oximy_context.get("trace_id"),
                                    "parent_event_id": oximy_context.get("parent_event_id"),
                                    "span_name": oximy_context.get("span_name"),
                                    "tags": oximy_context.get("tags"),
                                    "metadata": {
                                        **(self._config.metadata or {}),
                                        **(oximy_context.get("metadata") or {}),
                                    },
                                }
                            elif self._config.metadata:
                                event["context"] = {"metadata": self._config.metadata}

                            # Add global context
                            if self._config.environment and event.get("context"):
                                event["context"]["metadata"] = {
                                    **event["context"].get("metadata", {}),
                                    "environment": self._config.environment,
                                    "service": self._config.service,
                                    "version": self._config.version,
                                }

                            # Add policy info if there were violations
                            if all_violations:
                                event["policy"] = {
                                    "version": self._state.policy.version if self._state.policy else 0,
                                    "mode": self._state.settings.policy_mode if self._state.settings else "shadow",  # type: ignore
                                    "violations": [
                                        {
                                            "rule_id": v.rule_id,
                                            "rule_name": v.rule_name,
                                            "action": v.action,
                                            "severity": v.severity,
                                            "matched": v.matched,
                                            "message": v.message,
                                        }
                                        for v in all_violations
                                    ],
                                }

                            self._send_event(event)
                        except Exception:
                            # Fail-open: ignore telemetry collection errors
                            pass

                    asyncio.create_task(send_stream_telemetry())

                    return stream

                # =========================================================================
                # OUTPUT POLICY EVALUATION (Non-streaming)
                # =========================================================================
                if self._policy_manager and self._policy_manager.is_enabled():
                    try:
                        output_result = await self._policy_manager.evaluate_output(response)

                        if output_result.violations:
                            all_violations.extend(output_result.violations)

                            for violation in output_result.violations:
                                if self._config.on_policy_violation:
                                    self._config.on_policy_violation(violation)

                        # If blocked, throw error
                        if not output_result.allowed and output_result.blocked:
                            self._debug("Response blocked by policy:", output_result.blocked.get("rule_name"))
                            raise create_policy_error(
                                PolicyViolation(
                                    rule_id=output_result.blocked.get("rule_id", ""),
                                    rule_name=output_result.blocked.get("rule_name", ""),
                                    action="block",
                                    severity="high",
                                    message=output_result.blocked.get("message"),
                                )
                            )

                        # If modified, use modified response
                        if output_result.modified_response:
                            response = output_result.modified_response

                    except OximyPolicyError:
                        raise
                    except Exception as err:
                        self._debug("Output policy evaluation error:", err)

                # Non-streaming response
                end_time = time.time() * 1000
                normalized = normalize_data(request_input, response, provider, event_type)  # type: ignore

                event: OximyEvent = {
                    "id": event_id,
                    "timestamp": timestamp,
                    "source": {
                        "sdk_version": SDK_VERSION,
                        "sdk_language": SDK_LANGUAGE,
                        "provider": provider,  # type: ignore
                        "api_type": api_type,
                        "event_type": event_type,  # type: ignore
                    },
                    "raw": {
                        "request": request_input,
                        "response": response,
                    },
                    "normalized": normalized,
                    "timing": {
                        "started_at": datetime.fromtimestamp(start_time / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "ended_at": datetime.fromtimestamp(end_time / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "duration_ms": int(end_time - start_time),
                    },
                    "outcome": {
                        "success": True,
                        "finish_reason": normalized.get("output", {}).get("finish_reason") if normalized else None,
                    },
                }

                # Add context
                if oximy_context:
                    event["context"] = {
                        "user_id": oximy_context.get("user_id"),
                        "session_id": oximy_context.get("session_id"),
                        "trace_id": oximy_context.get("trace_id"),
                        "parent_event_id": oximy_context.get("parent_event_id"),
                        "span_name": oximy_context.get("span_name"),
                        "tags": oximy_context.get("tags"),
                        "metadata": {
                            **(self._config.metadata or {}),
                            **(oximy_context.get("metadata") or {}),
                        },
                    }
                elif self._config.metadata:
                    event["context"] = {"metadata": self._config.metadata}

                # Add global context
                if self._config.environment and event.get("context"):
                    event["context"]["metadata"] = {
                        **event["context"].get("metadata", {}),
                        "environment": self._config.environment,
                        "service": self._config.service,
                        "version": self._config.version,
                    }

                # Add policy info if there were violations
                if all_violations:
                    event["policy"] = {
                        "version": self._state.policy.version if self._state.policy else 0,
                        "mode": self._state.settings.policy_mode if self._state.settings else "shadow",  # type: ignore
                        "violations": [
                            {
                                "rule_id": v.rule_id,
                                "rule_name": v.rule_name,
                                "action": v.action,
                                "severity": v.severity,
                                "matched": v.matched,
                                "message": v.message,
                            }
                            for v in all_violations
                        ],
                    }

                self._send_event(event)

                return response

            except Exception as err:
                error = err
                end_time = time.time() * 1000

                event: OximyEvent = {
                    "id": event_id,
                    "timestamp": timestamp,
                    "source": {
                        "sdk_version": SDK_VERSION,
                        "sdk_language": SDK_LANGUAGE,
                        "provider": provider,  # type: ignore
                        "api_type": api_type,
                        "event_type": event_type,  # type: ignore
                    },
                    "raw": {
                        "request": request_input,
                        "response": None,
                    },
                    "timing": {
                        "started_at": datetime.fromtimestamp(start_time / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "ended_at": datetime.fromtimestamp(end_time / 1000, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "duration_ms": int(end_time - start_time),
                    },
                    "outcome": {
                        "success": False,
                        "error": {
                            "type": error.__class__.__name__,
                            "message": str(error),
                            "code": getattr(error, "code", None),
                            "statusCode": getattr(error, "status", None),
                        },
                    },
                }

                # Add context
                if oximy_context:
                    event["context"] = {
                        "user_id": oximy_context.get("user_id"),
                        "session_id": oximy_context.get("session_id"),
                        "trace_id": oximy_context.get("trace_id"),
                        "parent_event_id": oximy_context.get("parent_event_id"),
                        "span_name": oximy_context.get("span_name"),
                        "tags": oximy_context.get("tags"),
                        "metadata": {
                            **(self._config.metadata or {}),
                            **(oximy_context.get("metadata") or {}),
                        },
                    }
                elif self._config.metadata:
                    event["context"] = {"metadata": self._config.metadata}

                # Add policy info if there were violations
                if all_violations:
                    event["policy"] = {
                        "version": self._state.policy.version if self._state.policy else 0,
                        "mode": self._state.settings.policy_mode if self._state.settings else "shadow",  # type: ignore
                        "violations": [
                            {
                                "rule_id": v.rule_id,
                                "rule_name": v.rule_name,
                                "action": v.action,
                                "severity": v.severity,
                                "matched": v.matched,
                                "message": v.message,
                            }
                            for v in all_violations
                        ],
                    }

                self._send_event(event)

                # Re-throw original error
                raise error

        # Handle both sync and async methods
        if asyncio.iscoroutinefunction(method):
            return wrapped_async
        else:
            # For sync methods, create a sync wrapper
            # Note: Policy evaluation is async, so we need to run it in an event loop
            def wrapped_sync(*args: Any, **kwargs: Any) -> Any:
                # Try to get existing event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an async context - run in a thread with a new event loop
                    import concurrent.futures
                    def run_in_new_loop():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(wrapped_async(*args, **kwargs))
                        finally:
                            new_loop.close()
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_new_loop)
                        return future.result()
                except RuntimeError:
                    # No event loop running - use existing loop or create one
                    try:
                        loop = asyncio.get_event_loop()
                        return loop.run_until_complete(wrapped_async(*args, **kwargs))
                    except RuntimeError:
                        # No event loop exists - create one and run
                        return asyncio.run(wrapped_async(*args, **kwargs))

            return wrapped_sync


def wrap_client(
    client: Any,
    send_event: Callable[[OximyEvent], None],
    config: OximyConfig,
    state: OximyState,
    debug: Callable[..., None],
    policy_manager: PolicyManager | None = None,
) -> Any:
    """Wraps an AI client with Oximy telemetry and policy evaluation."""
    return WrappedClient(client, send_event, config, state, debug, policy_manager)
