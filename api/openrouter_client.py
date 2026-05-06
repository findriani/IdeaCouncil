"""
OpenRouter API client with async support.
"""

import httpx
import asyncio
from typing import Dict, List, Any, Optional
from utils.logger import logger
from api.rate_limiter import RateLimiter

class OpenRouterError(Exception):
    """Base exception for OpenRouter errors."""
    pass

class InsufficientCreditsError(OpenRouterError):
    """Raised when API credits are insufficient."""
    pass

class ModelNotAvailableError(OpenRouterError):
    """Raised when requested model is not available."""
    pass

class RateLimitError(OpenRouterError):
    """Raised when rate limit is exceeded."""
    pass

class OpenRouterClient:
    """Async client for OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 60,
        max_retries: int = 3,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limiter: Optional rate limiter instance
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = rate_limiter or RateLimiter()

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/llm-council",
            "X-Title": "LLM Council Research Brainstorming"
        }

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a chat completion request.

        Args:
            model: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional API parameters

        Returns:
            API response dictionary

        Raises:
            OpenRouterError: On API errors
        """
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        # Use granular timeouts: quick connect, long read (models can take minutes)
        http_timeout = httpx.Timeout(
            connect=30.0,
            read=float(self.timeout),
            write=30.0,
            pool=60.0
        )
        async with httpx.AsyncClient(timeout=http_timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    async with self.rate_limiter:
                        response = await client.post(
                            url,
                            headers=self.headers,
                            json=payload
                        )

                    # Handle different error codes
                    if response.status_code == 402:
                        raise InsufficientCreditsError(
                            "Insufficient credits in OpenRouter account"
                        )
                    elif response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.warning(
                                f"Rate limit hit, waiting {wait_time}s before retry"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise RateLimitError("Rate limit exceeded")
                    elif response.status_code == 404:
                        raise ModelNotAvailableError(
                            f"Model not available: {model}"
                        )
                    elif response.status_code >= 400:
                        error_data = response.json() if response.text else {}
                        raise OpenRouterError(
                            f"API error {response.status_code}: {error_data}"
                        )

                    response.raise_for_status()
                    return response.json()

                except httpx.TimeoutException as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Timeout ({type(e).__name__}) for {model} "
                            f"(attempt {attempt+1}/{self.max_retries}), retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise OpenRouterError(
                            f"Request timed out after {self.max_retries} attempts for {model}"
                        )

                except httpx.RequestError as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"Network error ({type(e).__name__}: {e!r}) for {model} "
                            f"(attempt {attempt+1}/{self.max_retries}), retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise OpenRouterError(f"Request failed for {model}: {e}")

        raise OpenRouterError("Max retries exceeded")

    async def batch_completions(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Make multiple completion requests concurrently.

        Args:
            requests: List of request configurations, each with:
                - model: Model identifier
                - messages: Message list
                - temperature: Temperature
                - max_tokens: Max tokens
                - Other optional parameters

        Returns:
            List of response dictionaries

        Raises:
            OpenRouterError: On API errors
        """
        tasks = []

        for req in requests:
            task = self.chat_completion(
                model=req["model"],
                messages=req["messages"],
                temperature=req.get("temperature", 0.7),
                max_tokens=req.get("max_tokens", 2000),
                **{k: v for k, v in req.items()
                   if k not in ["model", "messages", "temperature", "max_tokens"]}
            )
            tasks.append(task)

        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Request {i} failed: {result}")
                # Re-raise first exception encountered
                if isinstance(result, OpenRouterError):
                    raise result
                else:
                    raise OpenRouterError(f"Request failed: {result}")
            processed_results.append(result)

        return processed_results

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Fetch list of available models from OpenRouter.

        Returns:
            List of model information dictionaries
        """
        url = f"{self.base_url}/models"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])

        except Exception as e:
            logger.error(f"Failed to fetch available models: {e}")
            return []

    def extract_usage(self, response: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token usage from API response.

        Args:
            response: API response dictionary

        Returns:
            Dictionary with input_tokens, output_tokens
        """
        usage = response.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }

    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extract message content from API response.

        Args:
            response: API response dictionary

        Returns:
            Message content string
        """
        try:
            message = response["choices"][0]["message"]
            content = message.get("content")

            if content:
                return content

            # Reasoning models (e.g. Kimi K2.5, GLM-5, QwQ) put their output
            # in `reasoning` or `reasoning_details` with content: null
            reasoning = message.get("reasoning")
            if reasoning:
                logger.info("content is null — using 'reasoning' field (reasoning model)")
                return reasoning

            details = message.get("reasoning_details", [])
            if details:
                text = " ".join(
                    d.get("text", "") for d in details if isinstance(d, dict)
                ).strip()
                if text:
                    logger.info("content is null — using 'reasoning_details' field (reasoning model)")
                    return text

            logger.warning(f"No extractable content in message: {message}")
            return ""

        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract content from response: {e}")
            return ""
