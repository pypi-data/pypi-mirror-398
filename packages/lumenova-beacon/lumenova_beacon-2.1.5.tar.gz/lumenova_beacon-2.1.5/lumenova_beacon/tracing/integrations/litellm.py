"""OTLP-based LiteLLM integration using standard OpenTelemetry spans.

This module provides a callback handler that traces LiteLLM operations
using standard OpenTelemetry spans, making it portable to any OTLP backend.

Usage:
    from lumenova_beacon import BeaconClient
    from lumenova_beacon import BeaconLiteLLMLogger
    import litellm

    # Initialize BeaconClient with OTLP (sets up TracerProvider)
    client = BeaconClient()

    # Register OTEL-based logger
    litellm.callbacks = [BeaconLiteLLMLogger()]

    # All LiteLLM calls now traced via standard OTEL spans
    response = litellm.completion(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        metadata={
            "generation_name": "greeting",
            "session_id": "user-123",
            "tags": ["prod"]
        }
    )

Environment Variables:
    BEACON_ENDPOINT - Beacon API endpoint (for OTLP export)
    BEACON_API_KEY - Beacon API key (for OTLP export)
    BEACON_SESSION_ID - Default session ID (optional)
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind

try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:
    raise ImportError(
        "litellm is required for LiteLLM OTLP integration. "
        "Install it with: pip install litellm"
    )

logger = logging.getLogger(__name__)


class BeaconLiteLLMLogger(CustomLogger):
    """OTEL-based logger for tracing LiteLLM operations.

    Spans are exported via the configured TracerProvider/SpanExporter, making
    this integration portable to any OTLP-compatible backend.

    This logger captures:
    - Input messages and parameters
    - Response content
    - Token usage
    - Request timing
    - Errors and exceptions
    - Custom metadata (generation names, trace IDs, tags, etc.)

    Example:
        >>> from lumenova_beacon import BeaconClient
        >>> from lumenova_beacon import BeaconLiteLLMLogger
        >>> import litellm
        >>>
        >>> # Initialize BeaconClient with OTLP (sets up TracerProvider)
        >>> client = BeaconClient()
        >>>
        >>> # All calls automatically traced via OTEL
        >>> response = litellm.completion(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
    """

    # Semantic convention attribute names (GenAI conventions)
    # See: https://opentelemetry.io/docs/specs/semconv/gen-ai/
    ATTR_LLM_SYSTEM = "gen_ai.system"
    ATTR_LLM_MODEL = "gen_ai.request.model"
    ATTR_LLM_PROMPT = "gen_ai.prompt"
    ATTR_LLM_COMPLETION = "gen_ai.completion"
    ATTR_LLM_TEMPERATURE = "gen_ai.request.temperature"
    ATTR_LLM_MAX_TOKENS = "gen_ai.request.max_tokens"
    ATTR_LLM_TOP_P = "gen_ai.request.top_p"
    ATTR_LLM_TOP_K = "gen_ai.request.top_k"
    ATTR_LLM_FREQUENCY_PENALTY = "gen_ai.request.frequency_penalty"
    ATTR_LLM_PRESENCE_PENALTY = "gen_ai.request.presence_penalty"
    ATTR_LLM_PROMPT_TOKENS = "gen_ai.usage.prompt_tokens"
    ATTR_LLM_COMPLETION_TOKENS = "gen_ai.usage.completion_tokens"
    ATTR_LLM_TOTAL_TOKENS = "gen_ai.usage.total_tokens"

    # TTFT (Time-to-First-Token) attributes
    ATTR_TTFT_MS = "gen_ai.response.time_to_first_token_ms"
    ATTR_STREAMING = "gen_ai.request.streaming"

    # Beacon-specific attributes
    ATTR_BEACON_SESSION_ID = "beacon.session_id"
    ATTR_BEACON_SPAN_TYPE = "beacon.span_type"

    def __init__(self, tracer_name: str = "lumenova_beacon.litellm"):
        """Initialize the OTEL-based LiteLLM logger.

        Args:
            tracer_name: Name for the OpenTelemetry tracer
        """
        super().__init__()
        self._tracer = trace.get_tracer(tracer_name)

        # TTFT tracking for streaming calls
        self._first_chunk_times: dict[str, float] = {}  # call_id -> first chunk timestamp
        self._start_perf_times: dict[str, float] = {}  # call_id -> high-precision start time

        logger.debug(f"Initialized BeaconLiteLLMLogger with tracer: {tracer_name}")

    def _extract_metadata(self, kwargs: dict) -> dict:
        """Extract Beacon-compatible metadata from LiteLLM kwargs.

        Args:
            kwargs: LiteLLM kwargs dictionary

        Returns:
            Dictionary with extracted metadata fields
        """
        litellm_params = kwargs.get("litellm_params", {})
        metadata = litellm_params.get("metadata", {})

        return {
            "generation_name": metadata.get("generation_name"),
            "trace_id": metadata.get("trace_id"),
            "session_id": metadata.get("session_id"),
            "user_id": metadata.get("user_id") or metadata.get("trace_user_id"),
            "tags": metadata.get("tags", []),
            "custom": {
                k: v for k, v in metadata.items()
                if k not in ["generation_name", "trace_id", "session_id",
                             "user_id", "trace_user_id", "tags"]
            }
        }

    def _extract_messages(self, kwargs: dict) -> list[dict]:
        """Extract messages in a clean format.

        Args:
            kwargs: LiteLLM kwargs dictionary

        Returns:
            List of message dictionaries
        """
        messages = kwargs.get("messages", [])

        clean_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                clean_messages.append(msg)
            else:
                clean_messages.append({
                    "role": getattr(msg, "role", "unknown"),
                    "content": getattr(msg, "content", str(msg))
                })

        return clean_messages

    def _extract_response_content(self, response_obj: Any) -> dict:
        """Extract response content in a clean format.

        Args:
            response_obj: LiteLLM response object

        Returns:
            Dictionary with response content
        """
        try:
            if hasattr(response_obj, "choices") and response_obj.choices:
                choice = response_obj.choices[0]

                if hasattr(choice, "message"):
                    message = choice.message
                    result = {
                        "role": "assistant",
                        "content": getattr(message, "content", None)
                    }

                    # Include tool calls if present
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        result["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": getattr(tc, "type", "function"),
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]

                    # Include function call if present (legacy format)
                    if hasattr(message, "function_call") and message.function_call:
                        result["function_call"] = {
                            "name": message.function_call.name,
                            "arguments": message.function_call.arguments
                        }

                    return result

                elif hasattr(choice, "text"):
                    return {"text": choice.text}

            # Fallback for embedding or other response types
            if hasattr(response_obj, "data"):
                return {"data": "embedding_response"}

        except Exception as e:
            logger.debug(f"Error extracting response content: {e}")

        return {"content": str(response_obj)[:500]}

    def _set_span_attributes(
        self,
        span,
        kwargs: dict,
        response_obj: Any,
        metadata: dict,
        is_error: bool = False
    ) -> None:
        """Set all attributes on the OTEL span.

        Args:
            span: OpenTelemetry span
            kwargs: LiteLLM kwargs dictionary
            response_obj: LiteLLM response object
            metadata: Extracted metadata dictionary
            is_error: Whether this is an error span
        """
        # Model info
        model = kwargs.get("model", "unknown")
        span.set_attribute(self.ATTR_LLM_SYSTEM, "litellm")
        span.set_attribute(self.ATTR_LLM_MODEL, model)
        span.set_attribute(self.ATTR_BEACON_SPAN_TYPE, "generation")

        # Input (messages)
        messages = self._extract_messages(kwargs)
        span.set_attribute(self.ATTR_LLM_PROMPT, json.dumps(messages, default=str))

        # Model parameters
        param_mapping = {
            "temperature": self.ATTR_LLM_TEMPERATURE,
            "max_tokens": self.ATTR_LLM_MAX_TOKENS,
            "top_p": self.ATTR_LLM_TOP_P,
            "top_k": self.ATTR_LLM_TOP_K,
            "frequency_penalty": self.ATTR_LLM_FREQUENCY_PENALTY,
            "presence_penalty": self.ATTR_LLM_PRESENCE_PENALTY,
        }

        for param_name, attr_name in param_mapping.items():
            if param_name in kwargs and kwargs[param_name] is not None:
                span.set_attribute(attr_name, kwargs[param_name])

        # Output and usage (only for successful calls)
        if not is_error and response_obj:
            # Response content
            output = self._extract_response_content(response_obj)
            span.set_attribute(self.ATTR_LLM_COMPLETION, json.dumps(output, default=str))

            # Token usage
            if hasattr(response_obj, "usage") and response_obj.usage:
                usage = response_obj.usage
                span.set_attribute(
                    self.ATTR_LLM_PROMPT_TOKENS,
                    getattr(usage, "prompt_tokens", 0)
                )
                span.set_attribute(
                    self.ATTR_LLM_COMPLETION_TOKENS,
                    getattr(usage, "completion_tokens", 0)
                )
                span.set_attribute(
                    self.ATTR_LLM_TOTAL_TOKENS,
                    getattr(usage, "total_tokens", 0)
                )

        # Beacon-specific metadata
        if metadata.get("session_id"):
            span.set_attribute(self.ATTR_BEACON_SESSION_ID, metadata["session_id"])

        # Custom metadata
        for key, value in metadata.get("custom", {}).items():
            if isinstance(value, (str, int, float, bool)):
                attr_value = value
            else:
                attr_value = json.dumps(value, default=str)
            span.set_attribute(f"beacon.metadata.{key}", attr_value)

    def _get_call_id(self, kwargs: dict) -> str:
        """Get a unique call identifier for TTFT tracking.

        Args:
            kwargs: LiteLLM kwargs dictionary

        Returns:
            Unique call identifier string
        """
        # Prefer litellm_call_id if available, otherwise use id(kwargs)
        call_id = kwargs.get("litellm_call_id")
        if call_id is not None:
            return str(call_id)
        return str(id(kwargs))

    def log_pre_api_call(
        self,
        model: str,
        messages: list,
        kwargs: dict,
    ) -> None:
        """Record high-precision start time before the API call.

        This is called before the LLM API request and is used to
        calculate accurate TTFT for streaming calls.

        Args:
            model: The model name
            messages: The input messages
            kwargs: LiteLLM call parameters
        """
        try:
            call_id = self._get_call_id(kwargs)
            self._start_perf_times[call_id] = time.perf_counter()
        except Exception as e:
            logger.debug(f"Error in log_pre_api_call: {e}")

    def log_stream_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Log streaming chunk event for TTFT calculation.

        This is called for each streaming chunk. We record the first chunk
        time to calculate time-to-first-token.

        Args:
            kwargs: LiteLLM call parameters
            response_obj: The streaming response chunk
            start_time: Chunk start datetime
            end_time: Chunk end datetime
        """
        try:
            call_id = self._get_call_id(kwargs)

            # Only record the first chunk time
            if call_id not in self._first_chunk_times:
                self._first_chunk_times[call_id] = time.perf_counter()

        except Exception as e:
            logger.debug(f"Error in log_stream_event: {e}")

    async def async_log_stream_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Async version of log_stream_event.

        Args:
            kwargs: LiteLLM call parameters
            response_obj: The streaming response chunk
            start_time: Chunk start datetime
            end_time: Chunk end datetime
        """
        self.log_stream_event(kwargs, response_obj, start_time, end_time)

    def log_success_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Log successful LiteLLM completion using OTEL span.

        Args:
            kwargs: LiteLLM call parameters
            response_obj: LiteLLM response object
            start_time: Request start datetime
            end_time: Request end datetime
        """
        try:
            metadata = self._extract_metadata(kwargs)
            span_name = metadata.get("generation_name") or f"{kwargs.get('model', 'litellm')}.completion"
            call_id = self._get_call_id(kwargs)

            # Create span with explicit timing
            with self._tracer.start_as_current_span(
                span_name,
                kind=SpanKind.CLIENT,
                start_time=self._to_nanoseconds(start_time),
            ) as span:
                self._set_span_attributes(span, kwargs, response_obj, metadata)
                span.set_status(Status(StatusCode.OK))

                # Calculate and set TTFT for streaming calls
                is_streaming = kwargs.get("stream", False)
                first_chunk_time = self._first_chunk_times.pop(call_id, None)
                start_perf_time = self._start_perf_times.pop(call_id, None)

                if is_streaming and first_chunk_time is not None and start_perf_time is not None:
                    # Calculate TTFT in milliseconds
                    ttft_ms = (first_chunk_time - start_perf_time) * 1000
                    span.set_attribute(self.ATTR_TTFT_MS, ttft_ms)
                    span.set_attribute(self.ATTR_STREAMING, True)
                elif is_streaming:
                    # Mark as streaming even if TTFT couldn't be calculated
                    span.set_attribute(self.ATTR_STREAMING, True)

            logger.debug(f"Logged LiteLLM call via OTEL: {span_name}")

        except Exception as e:
            logger.error(f"Error logging success event to OTEL: {e}", exc_info=True)

    def log_failure_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Log failed LiteLLM completion using OTEL span.

        Args:
            kwargs: LiteLLM call parameters
            response_obj: LiteLLM response object (or exception)
            start_time: Request start datetime
            end_time: Request end datetime
        """
        try:
            metadata = self._extract_metadata(kwargs)
            span_name = metadata.get("generation_name") or f"{kwargs.get('model', 'litellm')}.completion"
            call_id = self._get_call_id(kwargs)

            # Clean up TTFT tracking state
            self._first_chunk_times.pop(call_id, None)
            self._start_perf_times.pop(call_id, None)

            with self._tracer.start_as_current_span(
                span_name,
                kind=SpanKind.CLIENT,
                start_time=self._to_nanoseconds(start_time),
            ) as span:
                self._set_span_attributes(span, kwargs, response_obj, metadata, is_error=True)

                # Record exception
                exception = kwargs.get("exception")
                if exception:
                    span.record_exception(exception)
                    span.set_status(Status(StatusCode.ERROR, str(exception)))
                else:
                    error_msg = str(response_obj)[:500] if response_obj else "Unknown error"
                    span.set_status(Status(StatusCode.ERROR, error_msg))

            logger.debug(f"Logged failed LiteLLM call via OTEL: {span_name}")

        except Exception as e:
            logger.error(f"Error logging failure event to OTEL: {e}", exc_info=True)

    async def async_log_success_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Async version of log_success_event.

        OpenTelemetry operations are thread-safe, so we delegate to sync version.

        Args:
            kwargs: LiteLLM call parameters
            response_obj: LiteLLM response object
            start_time: Request start datetime
            end_time: Request end datetime
        """
        self.log_success_event(kwargs, response_obj, start_time, end_time)

    async def async_log_failure_event(
        self,
        kwargs: dict,
        response_obj: Any,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Async version of log_failure_event.

        OpenTelemetry operations are thread-safe, so we delegate to sync version.

        Args:
            kwargs: LiteLLM call parameters
            response_obj: LiteLLM response object (or exception)
            start_time: Request start datetime
            end_time: Request end datetime
        """
        self.log_failure_event(kwargs, response_obj, start_time, end_time)

    @staticmethod
    def _to_nanoseconds(dt: datetime) -> int:
        """Convert datetime to nanoseconds since epoch.

        Args:
            dt: Datetime object (can be naive or timezone-aware)

        Returns:
            Nanoseconds since Unix epoch
        """
        # timestamp() correctly handles both naive (as local) and aware datetimes
        return int(dt.timestamp() * 1e9)
