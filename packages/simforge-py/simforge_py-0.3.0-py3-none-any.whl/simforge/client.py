"""Simforge client for provider-based API calls."""

import asyncio
import json
import logging
import threading
from typing import Any, Optional, TypedDict

import requests

from simforge.baml import run_function_with_baml

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_URL = "https://simforge.goharvest.ai"


class AllowedEnvVars(TypedDict, total=False):
    """Allowed environment variables for LLM providers.

    Only these keys are permitted when passing environment variables
    to the Simforge client for local BAML execution.

    Attributes:
        OPENAI_API_KEY: OpenAI API key for GPT models
    """

    OPENAI_API_KEY: str


class _CreateTraceResult(TypedDict):
    """Result from creating a trace."""

    traceId: str
    functionId: str
    versionId: str


class Simforge:
    """Client for making provider-based API calls via BAML."""

    def __init__(
        self,
        api_key: str,
        service_url: Optional[str] = None,
        env_vars: Optional[AllowedEnvVars] = None,
        execute_locally: bool = True,
    ):
        """Initialize the Simforge client.

        Args:
            api_key: The API key for Simforge API authentication
            service_url: The base URL for the Simforge API (default: https://simforge.goharvest.ai)
            env_vars: Environment variables for LLM provider API keys (only OPENAI_API_KEY is supported)
            execute_locally: Whether to execute BAML locally on the client (default: True)
        """
        self.api_key = api_key
        self.service_url = service_url or DEFAULT_SERVICE_URL
        self.env_vars = env_vars or {}
        self.execute_locally = execute_locally

    def _fetch_function_version(self, method_name: str) -> dict:
        """Fetch the function with its current version and BAML prompt from the server.

        Args:
            method_name: The name of the method to fetch

        Returns:
            Function version data including BAML prompt and providers

        Raises:
            ValueError: If function not found or has no prompt
        """
        url = f"{self.service_url}/api/sdk/functions/lookup"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"name": method_name}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()

            result = response.json()

            # Check if function was not found
            if result.get("id") is None:
                raise ValueError(
                    f'Function "{method_name}" not found. Create it at: {self.service_url}/functions'
                )

            # Check if function has no prompt
            if not result.get("prompt"):
                func_id = result.get("id")
                raise ValueError(
                    f'Function "{method_name}" has no prompt configured. '
                    f"Add one at: {self.service_url}/functions/{func_id}"
                )

            # Check for errors in the response
            if "error" in result:
                if "url" in result:
                    raise ValueError(
                        f"{result['error']} Configure it at: {self.service_url}{result['url']}"
                    )
                raise ValueError(result["error"])

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching function version: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            raise

    def call(self, method_name: str, **kwargs: Any) -> Any:
        """Call a method with the given named arguments via BAML execution.

        Args:
            method_name: The name of the method to call
            **kwargs: Named arguments to pass to the method

        Returns:
            The result of the BAML function execution

        Raises:
            ValueError: If no prompt is found or other API errors
        """
        # If executeLocally is true, fetch the BAML and execute it locally
        if self.execute_locally:
            try:
                function_version = self._fetch_function_version(method_name)
                execution_result = asyncio.run(
                    run_function_with_baml(
                        function_version["prompt"],
                        kwargs,
                        function_version["providers"],
                        self.env_vars,
                    )
                )

                # Create trace for the local execution
                # Serialize the result to JSON string
                if isinstance(execution_result.result, str):
                    # If it's a string, use as-is
                    result_str = execution_result.result
                elif hasattr(execution_result.result, "model_dump"):
                    # Pydantic v2 model - convert to dict first, then to JSON
                    result_dict = execution_result.result.model_dump()
                    result_str = json.dumps(result_dict)
                elif hasattr(execution_result.result, "dict"):
                    # Pydantic v1 model - convert to dict first, then to JSON
                    result_dict = execution_result.result.dict()
                    result_str = json.dumps(result_dict)
                elif isinstance(execution_result.result, (dict, list)):
                    # Plain dict or list - serialize to JSON
                    result_str = json.dumps(execution_result.result)
                else:
                    # Fallback to string representation
                    result_str = str(execution_result.result)

                # Create trace in background thread so user doesn't have to wait
                def create_trace_async():
                    try:
                        self._create_trace(
                            function_id=function_version["id"],
                            result=result_str,
                            inputs=kwargs if kwargs else None,
                            raw_collector=execution_result.raw_collector,
                        )
                    except Exception:
                        # Silently ignore trace creation failures
                        pass

                thread = threading.Thread(target=create_trace_async, daemon=True)
                thread.start()

                return execution_result.result
            except Exception as e:
                logger.error(f"Error during local execution: {e}")
                raise

        # Otherwise, fall back to server-side execution
        url = f"{self.service_url}/api/sdk/call"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "name": method_name,
            "inputs": kwargs,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=120,  # Longer timeout for BAML execution
            )
            response.raise_for_status()

            result = response.json()

            # Check for errors in the response
            if "error" in result:
                if "url" in result:
                    raise ValueError(
                        f"{result['error']} Configure it at: {self.service_url}{result['url']}"
                    )
                raise ValueError(result["error"])

            return result.get("result")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Simforge: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            raise

    def _create_trace(
        self,
        function_id: str,
        result: str,
        inputs: Optional[dict] = None,
        raw_collector: Optional[dict] = None,
        source: str = "python-sdk",
    ) -> _CreateTraceResult:
        """Create a trace from a local execution result.

        Internal method to record traces when executing BAML locally.

        Args:
            function_id: The ID of the function
            result: The execution result (as a string)
            inputs: The input arguments that were passed to the function
            raw_collector: Raw collector data from BAML execution (server will parse it)
            source: Source of the trace (e.g., "python-sdk", "typescript-sdk", "web-server")

        Returns:
            A CreateTraceResult containing traceId, functionId, and versionId

        Raises:
            ValueError: If the function has no prompt configured
            requests.exceptions.RequestException: If the API request fails
        """
        url = f"{self.service_url}/api/sdk/functions/{function_id}/traces"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload: dict = {
            "result": result,
            "source": source,
        }

        if inputs is not None:
            payload["inputs"] = inputs
        if raw_collector is not None:
            payload["rawCollector"] = raw_collector

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            result_data = response.json()

            # Check for errors in the response
            if "error" in result_data:
                if "url" in result_data:
                    raise ValueError(
                        f"{result_data['error']} Configure it at: {self.service_url}{result_data['url']}"
                    )
                raise ValueError(result_data["error"])

            return result_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating trace: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            raise

    def get_openai_tracing_processor(self):
        """Get a tracing processor for OpenAI Agents SDK integration.

        The processor implements the TracingProcessor interface from the OpenAI
        Agents SDK and can be registered to automatically capture traces and
        spans from agent execution.

        Example:
            ```python
            from simforge import Simforge
            from agents import set_trace_processors

            simforge = Simforge(api_key="your-api-key")
            processor = simforge.get_openai_tracing_processor()

            # Register the processor with OpenAI Agents SDK
            set_trace_processors([processor])
            ```

        Returns:
            A SimforgeOpenAITracingProcessor instance configured for this client

        Raises:
            ImportError: If openai-agents is not installed

        See:
            https://openai.github.io/openai-agents-python/ref/tracing/
        """
        # Import here to avoid requiring openai-agents for basic SDK usage
        from simforge.tracing import SimforgeOpenAITracingProcessor

        return SimforgeOpenAITracingProcessor(
            api_key=self.api_key,
            service_url=self.service_url,
        )
