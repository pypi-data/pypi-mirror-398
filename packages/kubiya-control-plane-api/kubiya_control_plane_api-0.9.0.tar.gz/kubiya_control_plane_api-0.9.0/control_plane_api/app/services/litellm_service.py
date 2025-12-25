"""
LiteLLM Service

This service provides a wrapper around LiteLLM for agent execution.
"""

import os
from typing import Dict, List, Optional, Any
import litellm
from litellm import completion, get_valid_models
import logging
import httpx

from control_plane_api.app.config import settings

logger = logging.getLogger(__name__)


class LiteLLMService:
    """Service for interacting with LiteLLM"""

    def __init__(self):
        """Initialize LiteLLM service with configuration"""
        # Set LiteLLM configuration
        if settings.litellm_api_key:
            os.environ["LITELLM_API_KEY"] = settings.litellm_api_key
        litellm.api_base = settings.litellm_api_base
        litellm.drop_params = True  # Drop unsupported params instead of failing

        # Configure timeout
        litellm.request_timeout = settings.litellm_timeout

        logger.info(f"LiteLLM Service initialized with base URL: {settings.litellm_api_base}")

    async def fetch_available_models(self, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch available models from the LiteLLM proxy server.

        This method tries multiple approaches:
        1. HTTP API call to /model/info endpoint (includes mode field)
        2. Fallback to /v1/models endpoint with mode detection
        3. Fallback to using LiteLLM SDK's get_valid_models() if available

        Args:
            base_url: Optional override for the LiteLLM base URL

        Returns:
            List of model objects with mode field from the LiteLLM server

        Raises:
            Exception if all methods fail
        """
        # Use provided base_url or fall back to settings
        api_base = base_url or settings.litellm_api_base

        # Try Method 1: /model/info endpoint (includes mode)
        try:
            model_info_url = f"{api_base.rstrip('/')}/model/info"
            logger.info(f"Fetching models from LiteLLM /model/info endpoint: {model_info_url}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if settings.litellm_api_key:
                    headers["Authorization"] = f"Bearer {settings.litellm_api_key}"

                response = await client.get(model_info_url, headers=headers)
                response.raise_for_status()

                data = response.json()

                # Parse model_info response
                models = []
                for model_data in data.get("data", []):
                    models.append({
                        "id": model_data.get("model_name"),
                        "object": "model",
                        "created": 0,
                        "owned_by": model_data.get("litellm_provider", "unknown"),
                        "mode": model_data.get("mode", "completion")  # Include mode from LiteLLM
                    })

                logger.info(f"Successfully fetched {len(models)} models from LiteLLM /model/info with mode information")
                return models

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"/model/info endpoint failed: {e.response.status_code}. "
                f"Trying fallback to /v1/models..."
            )

        except Exception as e:
            logger.warning(f"/model/info request failed: {str(e)}. Trying fallback to /v1/models...")

        # Try Method 2: /v1/models endpoint (detect mode from model name)
        try:
            models_url = f"{api_base.rstrip('/')}/v1/models"
            logger.info(f"Fetching models from LiteLLM server: {models_url}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if settings.litellm_api_key:
                    headers["Authorization"] = f"Bearer {settings.litellm_api_key}"

                response = await client.get(models_url, headers=headers)
                response.raise_for_status()

                data = response.json()

                # LiteLLM returns models in OpenAI format: {"data": [...], "object": "list"}
                raw_models = data.get("data", [])

                # Add mode detection from model name
                models = []
                for model in raw_models:
                    model_id = model.get("id", "")
                    model_lower = model_id.lower()

                    # Detect mode from model name - expanded detection for embedding models
                    # Check for embedding keywords (including common embedding model patterns)
                    embedding_keywords = [
                        "embedding", "embed", "embeddings",
                        "ada-002", "text-embedding",
                        "bge-", "gte-", "e5-",  # Common embedding model prefixes
                        "voyage-", "cohere-embed",  # Provider-specific embedding models
                        "-embed-", "_embed_", "/embed",  # Pattern matching
                    ]

                    if any(keyword in model_lower for keyword in embedding_keywords):
                        mode = "embedding"
                    elif any(keyword in model_lower for keyword in ["gpt", "claude", "llama", "mistral", "gemini", "deepseek", "qwen"]):
                        mode = "chat"
                    else:
                        mode = "completion"

                    model["mode"] = mode
                    models.append(model)

                logger.info(f"Successfully fetched {len(models)} models from LiteLLM server via /v1/models with mode detection")
                return models

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"HTTP endpoint failed: {e.response.status_code}. "
                f"Trying SDK fallback method..."
            )

        except Exception as e:
            logger.warning(f"HTTP request failed: {str(e)}. Trying SDK fallback method...")

        # Try Method 3: Use LiteLLM Python SDK (synchronous, needs to be run in executor)
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            def _get_models_sync():
                """Synchronous function to get models using LiteLLM SDK"""
                try:
                    # Set environment for LiteLLM
                    if settings.litellm_api_key:
                        os.environ["LITELLM_API_KEY"] = settings.litellm_api_key

                    # Use get_valid_models with provider endpoint check
                    model_names = get_valid_models(check_provider_endpoint=True)

                    # Convert model strings to OpenAI-like format with mode detection
                    models = []
                    for model_name in model_names:
                        model_lower = model_name.lower()

                        # Detect mode from model name - expanded detection for embedding models
                        # Check for embedding keywords (including common embedding model patterns)
                        embedding_keywords = [
                            "embedding", "embed", "embeddings",
                            "ada-002", "text-embedding",
                            "bge-", "gte-", "e5-",  # Common embedding model prefixes
                            "voyage-", "cohere-embed",  # Provider-specific embedding models
                            "-embed-", "_embed_", "/embed",  # Pattern matching
                        ]

                        if any(keyword in model_lower for keyword in embedding_keywords):
                            mode = "embedding"
                        elif any(keyword in model_lower for keyword in ["gpt", "claude", "llama", "mistral", "gemini", "deepseek", "qwen"]):
                            mode = "chat"
                        else:
                            mode = "completion"

                        models.append({
                            "id": model_name,
                            "object": "model",
                            "created": 0,
                            "owned_by": "litellm",
                            "mode": mode
                        })

                    return models
                except Exception as e:
                    logger.error(f"LiteLLM SDK get_valid_models failed: {str(e)}")
                    return []

            # Run synchronous function in thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                models = await loop.run_in_executor(executor, _get_models_sync)

            if models:
                logger.info(f"Successfully fetched {len(models)} models using LiteLLM SDK with mode detection")
                return models

        except Exception as e:
            logger.error(f"LiteLLM SDK method failed: {str(e)}")

        # If all methods failed, raise exception
        raise Exception(
            f"Failed to fetch models from LiteLLM server. "
            f"Tried HTTP endpoint and SDK method. "
            f"Please ensure LiteLLM proxy is running at {api_base}"
        )

    def validate_model(self, model_id: str) -> bool:
        """
        Validate if a model ID is supported by the LiteLLM server.

        Args:
            model_id: The model identifier to validate

        Returns:
            True if the model is valid, False otherwise
        """
        try:
            # For now, we'll accept any model ID that follows the provider/model format
            # More sophisticated validation can be added later by checking against
            # the models list from the server
            return bool(model_id and "/" in model_id)
        except Exception as e:
            logger.error(f"Error validating model {model_id}: {str(e)}")
            return False


    def execute_agent(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute an agent with LiteLLM

        Args:
            prompt: The user prompt
            model: Model identifier (defaults to configured default)
            system_prompt: System prompt for the agent
            temperature: Temperature for response generation
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            **kwargs: Additional parameters to pass to LiteLLM

        Returns:
            Dict containing the response and metadata
        """
        try:
            # Use default model if not specified
            if not model:
                model = settings.litellm_default_model

            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Prepare completion parameters
            # For custom proxies, use openai/ prefix to force OpenAI-compatible mode
            # This tells LiteLLM to use the base_url as an OpenAI-compatible endpoint
            completion_params = {
                "model": f"openai/{model}",  # Use openai/ prefix for custom proxy
                "messages": messages,
                "temperature": temperature,
                "api_key": settings.litellm_api_key or "dummy-key",  # Fallback for when key is not set
                "base_url": settings.litellm_api_base,
            }

            if max_tokens:
                completion_params["max_tokens"] = max_tokens
            if top_p:
                completion_params["top_p"] = top_p

            # Add any additional kwargs
            completion_params.update(kwargs)

            logger.info(f"Executing agent with model: {model} (using openai/{model})")

            # Make the completion request
            response = completion(**completion_params)

            # Extract response content
            result = {
                "success": True,
                "response": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
            }

            logger.info(f"Agent execution successful. Tokens used: {result['usage']['total_tokens']}")
            return result

        except Exception as e:
            logger.error(f"Error executing agent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model": model or settings.litellm_default_model,
            }

    def execute_agent_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        """
        Execute an agent with streaming response

        Args:
            prompt: The user prompt
            model: Model identifier (defaults to configured default)
            system_prompt: System prompt for the agent
            temperature: Temperature for response generation
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            **kwargs: Additional parameters to pass to LiteLLM

        Yields:
            Response chunks as they arrive
        """
        try:
            # Use default model if not specified
            if not model:
                model = settings.litellm_default_model

            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Prepare completion parameters
            # For custom proxies, use openai/ prefix to force OpenAI-compatible mode
            # This tells LiteLLM to use the base_url as an OpenAI-compatible endpoint
            completion_params = {
                "model": f"openai/{model}",  # Use openai/ prefix for custom proxy
                "messages": messages,
                "temperature": temperature,
                "stream": True,
                "api_key": settings.litellm_api_key or "dummy-key",  # Fallback for when key is not set
                "base_url": settings.litellm_api_base,
            }

            if max_tokens:
                completion_params["max_tokens"] = max_tokens
            if top_p:
                completion_params["top_p"] = top_p

            # Add any additional kwargs
            completion_params.update(kwargs)

            logger.info(f"Executing agent (streaming) with model: {model} (using openai/{model})")

            # Make the streaming completion request
            response = completion(**completion_params)

            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error executing agent (streaming): {str(e)}")
            yield f"Error: {str(e)}"


# Singleton instance
litellm_service = LiteLLMService()
