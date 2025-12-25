"""BAML execution utilities for the Simforge Python SDK.

This module provides functions to execute BAML prompts dynamically on the client side.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)

# Allowed environment variable keys for LLM providers
ALLOWED_ENV_KEYS = ["OPENAI_API_KEY"]


class ProviderDefinition:
    """Provider definition from the server."""

    def __init__(self, provider: str, api_key_env: str, models: List[Dict[str, str]]):
        self.provider = provider
        self.api_key_env = api_key_env
        self.models = models


def filter_env_vars(env_vars: Dict[str, str]) -> Dict[str, str]:
    """Filter environment variables to only include allowed keys.

    This prevents accidentally passing sensitive environment variables to the BAML runtime.

    Args:
        env_vars: Environment variables dictionary

    Returns:
        Filtered dictionary with only allowed keys
    """
    filtered = {}
    for key in ALLOWED_ENV_KEYS:
        if key in env_vars:
            filtered[key] = env_vars[key]
    return filtered


def parse_baml_class_to_pydantic(
    baml_source: str, class_name: str
) -> Optional[Type[BaseModel]]:
    """Parse a BAML class definition and create a Pydantic model.

    Args:
        baml_source: The BAML source code
        class_name: The name of the class to parse

    Returns:
        A dynamically created Pydantic model, or None if parsing fails
    """
    # Find the class definition
    class_pattern = rf"class\s+{re.escape(class_name)}\s*\{{([^}}]+)\}}"
    class_match = re.search(class_pattern, baml_source, re.DOTALL)

    if not class_match:
        return None

    class_body = class_match.group(1)

    # Parse fields: field_name type? @description("...")
    field_pattern = r"(\w+)\s+(string|int|float|bool)(\?)?"
    fields = {}

    for match in re.finditer(field_pattern, class_body):
        field_name = match.group(1)
        field_type_str = match.group(2)
        is_optional = match.group(3) == "?"

        # Map BAML types to Python types
        type_map = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool,
        }

        field_type = type_map.get(field_type_str, str)

        if is_optional:
            fields[field_name] = (Optional[field_type], None)
        else:
            fields[field_name] = (field_type, ...)

    if not fields:
        return None

    # Create Pydantic model dynamically
    try:
        return create_model(class_name, **fields)
    except Exception as e:
        logger.warning(f"Failed to create Pydantic model for {class_name}: {e}")
        return None


def extract_function_name(baml_source: str) -> Optional[str]:
    """Extract the first function name from BAML source code.

    Args:
        baml_source: BAML source code

    Returns:
        Function name or None if not found
    """
    import re

    match = re.search(r"function\s+(\w+)\s*\(", baml_source)
    return match.group(1) if match else None


def coerce_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce input values from strings to their appropriate types.

    Args:
        inputs: Input dictionary

    Returns:
        Coerced input dictionary
    """
    coerced = {}

    for key, value in inputs.items():
        if isinstance(value, str):
            # Try to parse as JSON (handles numbers, booleans, arrays, objects)
            try:
                coerced[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Keep as string if not valid JSON
                coerced[key] = value
        else:
            coerced[key] = value

    return coerced


def format_provider(provider: str) -> str:
    """Convert provider name to PascalCase.

    Args:
        provider: Provider name (e.g., "openai")

    Returns:
        Formatted provider name (e.g., "OpenAI")
    """
    provider_map = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google",
    }
    return provider_map.get(provider, provider.capitalize())


def format_model(model: str) -> str:
    """Convert a model name to a valid BAML identifier part.

    Args:
        model: Model name (e.g., "gpt-5-mini")

    Returns:
        Formatted model name (e.g., "GPT5_mini")
    """
    return (
        model.replace("gpt-", "GPT")  # gpt- prefix -> GPT
        .replace(".", "_")  # dots -> underscore
        .replace("-", "_")  # hyphens -> underscore
    )


def get_client_name(provider: str, model: str) -> str:
    """Generate the BAML client name from provider and model.

    Args:
        provider: Provider name
        model: Model name

    Returns:
        BAML client name (e.g., "OpenAI_GPT4_1_mini")
    """
    return f"{format_provider(provider)}_{format_model(model)}"


def generate_client_definitions(providers: List[ProviderDefinition]) -> str:
    """Generate BAML client definition strings.

    BamlRuntime requires clients to be defined in source for parsing.

    Args:
        providers: List of provider definitions

    Returns:
        BAML client definitions as a string
    """
    definitions = []

    for provider_def in providers:
        for model in provider_def.models:
            client_name = get_client_name(provider_def.provider, model["model"])
            definitions.append(
                f"""client<llm> {client_name} {{
  provider {provider_def.provider}
  options {{
    model "{model["model"]}"
    api_key env.{provider_def.api_key_env}
  }}
}}"""
            )

    return "\n\n".join(definitions)


def with_default_clients(baml_source: str, providers: List[ProviderDefinition]) -> str:
    """Prepend the default client definitions to a BAML source if it doesn't already define them.

    Args:
        baml_source: BAML source code
        providers: List of provider definitions

    Returns:
        BAML source with client definitions
    """
    if "client<llm> OpenAI_" in baml_source:
        return baml_source

    default_clients = generate_client_definitions(providers)
    return f"{default_clients}\n\n{baml_source}"


async def run_function_with_baml(
    baml_source: str,
    inputs: Dict[str, Any],
    providers: List[Dict[str, Any]],
    env_vars: Dict[str, str],
) -> Any:
    """Run the BAML function with the given inputs using the BAML runtime directly.

    Note: This requires the baml-py package to be installed.

    Args:
        baml_source: The BAML source code containing the function
        inputs: Named arguments to pass to the function
        providers: Available provider definitions
        env_vars: Environment variables for API keys (only OPENAI_API_KEY is allowed)

    Returns:
        The result of the BAML function execution

    Raises:
        ImportError: If baml-py is not installed
        ValueError: If no function found in BAML source
        RuntimeError: If BAML function execution failed
    """
    try:
        from baml_py import BamlRuntime
    except ImportError:
        raise ImportError(
            "baml-py is required for local execution. Install it with: pip install baml-py"
        )

    # Extract function name from the BAML source
    function_name = extract_function_name(baml_source)
    if not function_name:
        raise ValueError("No function found in BAML source")

    # Convert provider dicts to ProviderDefinition objects
    provider_objs = [
        ProviderDefinition(p["provider"], p["apiKeyEnv"], p["models"])
        for p in providers
    ]

    # Add default client definitions (runtime needs them for parsing)
    full_source = with_default_clients(baml_source, provider_objs)

    # Filter env vars to only allowed keys
    filtered_env_vars = filter_env_vars(env_vars)

    # Create runtime from source with env vars
    runtime = BamlRuntime.from_files(
        "/tmp/baml_runtime", {"source.baml": full_source}, filtered_env_vars
    )

    # Create context manager
    ctx = runtime.create_context_manager()

    # Coerce inputs from strings to proper types
    args = coerce_inputs(inputs)

    # Call the function with all required arguments
    # Signature: call_function(function_name, args, ctx, tb, cb, collectors, env_vars, tags)
    result = await runtime.call_function(
        function_name,
        args,
        ctx,
        None,  # tb (TypeBuilder)
        None,  # cb (ClientRegistry)
        [],  # collectors
        filtered_env_vars,
        {},  # tags
    )

    if not result.is_ok():
        raise RuntimeError("BAML function execution failed")

    # Extract the parsed result from the internal representation
    internal_json = result.unstable_internal_repr()

    try:
        internal_data = json.loads(internal_json)
        if "Success" in internal_data and "content" in internal_data["Success"]:
            # The content is the raw LLM response (JSON string)
            content = internal_data["Success"]["content"]
            # Parse it to get the actual data as a dict
            result_dict = json.loads(content)

            # Try to extract the return type from the function definition
            # Pattern: function FunctionName(...) -> ReturnType {
            return_type_match = re.search(
                rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*->\s*(\w+)",
                baml_source,
            )

            if return_type_match:
                return_type_name = return_type_match.group(1)

                # Try to create a Pydantic model from the BAML class definition
                pydantic_model = parse_baml_class_to_pydantic(
                    baml_source, return_type_name
                )

                if pydantic_model:
                    # Return a Pydantic model instance
                    try:
                        return pydantic_model(**result_dict)
                    except Exception as e:
                        logger.warning(
                            f"Failed to instantiate Pydantic model: {e}, returning dict"
                        )
                        return result_dict

            # If we couldn't create a Pydantic model, return the dict
            return result_dict
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Failed to parse BAML result: {e}")

    # If we couldn't extract the content, raise an error
    raise RuntimeError("Unexpected BAML result format")
