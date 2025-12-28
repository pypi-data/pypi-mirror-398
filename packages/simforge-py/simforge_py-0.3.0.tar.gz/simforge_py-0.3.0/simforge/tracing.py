"""Tracing processor for OpenAI Agents SDK integration.

This module provides a tracing processor that implements the OpenAI Agents SDK
TracingProcessor interface to automatically capture and send traces to Simforge.

See: https://openai.github.io/openai-agents-python/ref/tracing/
"""

import json
import logging
import os
from typing import TYPE_CHECKING, Any

import requests

# Try to import openai-agents, but make it optional
try:
    from agents.tracing import TracingProcessor

    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    OPENAI_AGENTS_AVAILABLE = False
    # Create a dummy base class if openai-agents is not installed
    TracingProcessor = object  # type: ignore

if TYPE_CHECKING:
    from agents.tracing import Span, Trace

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_URL = "https://simforge.goharvest.ai"


class SimforgeOpenAITracingProcessor(TracingProcessor):
    """Tracing processor for OpenAI Agents SDK integration.

    Implements the TracingProcessor interface from the OpenAI Agents SDK to
    automatically capture traces and spans and send them to Simforge for
    monitoring and analysis.

    This processor receives notifications when traces and spans start and end,
    allowing it to collect, process, and export tracing data to Simforge.

    Example:
        ```python
        from simforge import Simforge
        from agents import set_trace_processors

        simforge = Simforge(api_key="your-api-key")
        processor = simforge.get_openai_tracing_processor()

        # Register the processor with OpenAI Agents SDK
        set_trace_processors([processor])
        ```

    Notes:
        - All methods are thread-safe
        - Methods do not block for long periods
        - Errors are handled gracefully to prevent disrupting agent execution
    """

    def __init__(
        self,
        api_key: str | None = None,
        service_url: str = DEFAULT_SERVICE_URL,
    ):
        """Initialize the tracing processor.

        Args:
            api_key: The API key for Simforge API authentication
            service_url: The base URL for the Simforge API

        Raises:
            ImportError: If openai-agents is not installed
        """
        if not OPENAI_AGENTS_AVAILABLE:
            raise ImportError(
                "openai-agents is required for tracing functionality. "
                "Install it with: pip install simforge-py[openai-tracing]"
            )

        self.api_key = api_key or os.getenv("SIMFORGE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SIMFORGE_API_KEY environment variable is not set and no API key was provided"
            )
        self.service_url = service_url
        self._active_traces: dict[str, Any] = {}
        self._active_spans: dict[str, Any] = {}

    def on_trace_start(self, trace: "Trace") -> None:
        """Called when a trace starts.

        Args:
            trace: The trace that has started
        """
        try:
            self._active_traces[trace.trace_id] = trace
            logger.debug(f"Trace started: {trace.trace_id} - {trace.name}")

            # Send the external trace to Simforge immediately
            self._send_external_trace(trace)
        except Exception as e:
            logger.error(f"Error in on_trace_start: {e}", exc_info=True)

    def on_trace_end(self, trace: "Trace") -> None:
        """Called when a trace ends.

        Args:
            trace: The trace that has ended
        """
        try:
            logger.debug(f"Trace ended: {trace.trace_id} - {trace.name}")

            # Send the external trace again to capture any updates
            self._send_external_trace(trace)

            # Clean up
            self._active_traces.pop(trace.trace_id, None)
        except Exception as e:
            logger.error(f"Error in on_trace_end: {e}", exc_info=True)

    def on_span_start(self, span: "Span") -> None:
        """Called when a span starts.

        Args:
            span: The span that has started
        """
        try:
            self._active_spans[span.span_id] = span
            logger.debug(
                f"Span started: {span.span_id} (trace: {span.trace_id}, type: {span.span_data.type})"
            )

            # Send the external span to Simforge immediately
            self._send_external_span(span)
        except Exception as e:
            logger.error(f"Error in on_span_start: {e}", exc_info=True)

    def on_span_end(self, span: "Span") -> None:
        """Called when a span ends.

        Args:
            span: The span that has ended
        """
        try:
            logger.debug(
                f"Span ended: {span.span_id} (trace: {span.trace_id}, type: {span.span_data.type})"
            )

            # Send the external span to Simforge again to capture updates
            self._send_external_span(span)

            # Clean up
            self._active_spans.pop(span.span_id, None)
        except Exception as e:
            logger.error(f"Error in on_span_end: {e}", exc_info=True)

    def shutdown(self) -> None:
        """Shutdown the processor and clean up resources.

        Called when the tracing system is shutting down. Should clean up
        any resources and ensure all pending data is flushed.
        """
        try:
            logger.info("Shutting down Simforge tracing processor")
            self.force_flush()
            self._active_traces.clear()
            self._active_spans.clear()
        except Exception as e:
            logger.error(f"Error in shutdown: {e}", exc_info=True)

    def force_flush(self) -> None:
        """Force flush any queued traces/spans to Simforge.

        Ensures all pending data is sent to the Simforge API immediately.
        Should not block for long periods.
        """
        try:
            logger.debug("Force flushing Simforge tracing processor")
            # No queued traces - all traces are sent immediately per LLM call
        except Exception as e:
            logger.error(f"Error in force_flush: {e}", exc_info=True)

    def _send_external_trace(self, trace: "Trace") -> None:
        """Send external trace to Simforge API.

        Args:
            trace: The trace to send
        """
        try:
            trace_data = {
                "type": "openai",
                "source": "python-sdk-openai-tracing",
                "rawTrace": trace.export(),
            }

            # Serialize to JSON to catch any serialization errors early
            try:
                json_str = json.dumps(trace_data)
                trace_data = json.loads(json_str)  # Re-parse to ensure it's clean
            except TypeError as e:
                logger.error(f"Failed to serialize raw trace data: {e}")
                logger.debug(f"Problematic trace_data: {trace_data}")
                return

            url = f"{self.service_url}/api/sdk/externalTraces"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            response = requests.post(
                url,
                json=trace_data,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            logger.debug(f"Successfully sent external trace to Simforge: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to send external trace to Simforge: {e}", exc_info=True)

    def _send_external_span(self, span: "Span") -> None:
        """Send external span to Simforge API.

        Args:
            span: The span to send
        """
        try:
            # Use span.export() for base serialization, then inject input/response
            # The SDK's toJSON/export hides _input and _response, so we add them manually
            serialized_span = span.export()

            # Inject the actual input and response data into span_data
            if "span_data" not in serialized_span:
                serialized_span["span_data"] = {}

            # Get input and response from span_data (they're private properties with underscores)
            span_input = getattr(span.span_data, "input", None) or []
            span_response = getattr(span.span_data, "response", None)

            # Serialize them - model_dump() handles Pydantic models, JSON handles the rest
            serialized_span["span_data"]["input"] = [
                item if isinstance(item, dict) else item.model_dump()
                for item in span_input
            ]
            serialized_span["span_data"]["response"] = (
                span_response.model_dump() if span_response else None
            )

            span_data = {
                "type": "openai",
                "source": "python-sdk-openai-tracing",
                "sourceTraceId": span.trace_id,
                "rawSpan": serialized_span,
            }

            # Serialize to JSON to catch any serialization errors early
            try:
                json_str = json.dumps(span_data)
                span_data = json.loads(json_str)  # Re-parse to ensure it's clean
            except TypeError as e:
                logger.error(f"Failed to serialize raw span data: {e}")
                logger.debug(f"Problematic span_data: {span_data}")
                return

            url = f"{self.service_url}/api/sdk/externalSpans"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            response = requests.post(
                url,
                json=span_data,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            logger.debug(f"Successfully sent external span to Simforge: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to send external span to Simforge: {e}", exc_info=True)

    def __enter__(self) -> "SimforgeOpenAITracingProcessor":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - flush pending traces."""
        self.shutdown()
