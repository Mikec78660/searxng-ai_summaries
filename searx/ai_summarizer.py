# SPDX-License-Identifier: AGPL-3.0-or-later
"""AI-powered summarization module for SearXNG search results.

This module provides functionality to generate AI summaries of search results
using OpenAI-compatible API endpoints.
"""

from __future__ import annotations

import json
import typing as t
from datetime import datetime
from urllib.parse import urlparse
import time

import httpx

from searx import logger

if t.TYPE_CHECKING:
    from searx.result_types import EngineResults

logger = logger.getChild('ai_summarizer')

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that summarizes search results.
Your task is to provide a concise, accurate summary of the provided search results.
Focus on the most relevant information and present it in a clear, readable format.
If the results contain conflicting information, mention this briefly.
Keep the summary factual and based on the provided results."""

DEFAULT_SUMMARY_PROMPT = """Search Query: {query}

Search Results:
{results}

Please provide a concise, well-structured summary of these search results that directly answers the query.

IMPORTANT: Your response must be:
- Between 50 and 300 words
- Complete sentences (never cut off mid-sentence)
- Well-structured with clear beginning and end

Format your response using Markdown:
- Use **bold** for emphasis on key points
- Use bullet points (-) for lists
- Use numbered lists (1., 2., etc.) for steps or ranked items
- Add paragraph breaks between different topics
- Use proper formatting to make it easy to read

Focus on the most relevant and reliable information."""

DEFAULT_TIMEOUT = 15.0
DEFAULT_TIMEOUT_PER_RESULT = 5.0
MAX_CONTENT_LENGTH = 4000


class SummarizerError(Exception):
    """Base exception for summarizer errors."""
    pass


class APIError(SummarizerError):
    """Exception raised when the API returns an error."""
    pass


class TimeoutError(SummarizerError):
    """Exception raised when the request times out."""
    pass


def sanitize_url(url: str) -> str:
    """Sanitize URL to handle invalid IDNA hostnames gracefully.

    Args:
        url: The URL to sanitize

    Returns:
        The original URL if valid, or '[Invalid URL]' if the URL
        has invalid characters that would cause IDNA encoding errors.
    """
    if not url:
        return url

    try:
        parsed = urlparse(url)
        if parsed.netloc:
            # Test if hostname is valid IDNA - this will raise UnicodeError
            # for invalid characters like '›' (U+203A) or other special chars
            parsed.netloc.encode('idna')
    except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError):
        logger.debug(f"Skipping URL with invalid hostname: {url}")
        return '[Invalid URL]'
    except Exception:
        # Catch any other parsing errors
        return '[Invalid URL]'

    return url


def format_results_for_prompt(
    results: EngineResults,
    query: str,
    max_results: int = 10
) -> str:
    """Format search results into a prompt suitable for AI summarization.

    Args:
        results: The search results to format
        query: The original search query
        max_results: Maximum number of results to include in the prompt

    Returns:
        A formatted string containing the search results
    """
    lines = [
        f"Search Query: {query}",
        "",
        "Search Results:",
        "",
    ]

    result_count = 0
    for result in results:
        if result_count >= max_results:
            break

        # Extract title and content from result
        title = getattr(result, 'title', '') or getattr(result, 'name', '')
        content = getattr(result, 'content', '') or getattr(result, 'description', '')
        url = getattr(result, 'url', '') or getattr(result, 'link', '')

        if not title and not content:
            continue

        result_count += 1
        lines.append(f"{result_count}. {title}")

        if content:
            # Truncate content if too long
            if len(content) > MAX_CONTENT_LENGTH // max_results:
                content = content[: MAX_CONTENT_LENGTH // max_results] + "..."
            lines.append(f"   Content: {content}")

        if url:
            # Sanitize URL to handle invalid IDNA hostnames
            safe_url = sanitize_url(url)
            lines.append(f"   URL: {safe_url}")

        lines.append("")

    if result_count == 0:
        lines.append("No results found.")

    return "\n".join(lines)


async def fetch_available_models(
    endpoint: str,
    api_key: str | None = None,
    timeout: float = 10,
) -> list[str]:
    """Fetch available models from the OpenAI-compatible API endpoint.

    Args:
        endpoint: The base URL of the API endpoint (e.g., "https://api.openai.com/v1")
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds (default: 10)

    Returns:
        List of model IDs, or empty list on error
    """
    url = f"{endpoint.rstrip('/')}/v1/models"
    headers: dict[str, str] = {}

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            models = data.get("data", [])
            model_ids = [model.get("id", "") for model in models if model.get("id")]
            logger.debug(f"Fetched {len(model_ids)} models from {endpoint}")

            return model_ids

    except Exception as e:
        logger.warning(f"Error fetching models from {endpoint}: {e}")
        return []


def generate_summary_sync(
    results: list[dict],
    query: str,
    endpoint: str,
    model: str,
    api_key: str | None = None,
    system_prompt: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> dict[str, t.Any]:
    """Generate AI summary synchronously (blocking call).

    Args:
        results: List of search result dicts with 'title', 'content', 'url' keys
        query: The original search query
        endpoint: The base URL of the API endpoint
        model: The model ID to use for summarization
        api_key: Optional API key for authentication
        system_prompt: Optional custom system prompt
        timeout: Request timeout in seconds
        max_tokens: Maximum tokens in the response
        temperature: Temperature for generation (0.0 to 1.0)

    Returns:
        A dictionary with success, summary, error, model, timestamp, usage, stats
    """
    timestamp = datetime.utcnow().isoformat()

    # Ensure endpoint has /v1 suffix
    endpoint = endpoint.rstrip('/')
    if not endpoint.endswith('/v1'):
        endpoint = f"{endpoint}/v1"
    api_url = f"{endpoint}/chat/completions"

    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Format results into prompt text
    lines = [f"Search Query: {query}", "", "Search Results:", ""]
    for i, result in enumerate(results, 1):
        title = result.get('title', '')
        content = result.get('content', '')
        url = result.get('url', '')

        if not title and not content:
            continue

        lines.append(f"{i}. {title}")
        if content:
            # Truncate content if too long
            max_content = MAX_CONTENT_LENGTH // len(results) if results else MAX_CONTENT_LENGTH
            if len(content) > max_content:
                content = content[:max_content] + "..."
            lines.append(f"   Content: {content}")
        if url:
            # Sanitize URL to handle invalid IDNA hostnames
            safe_url = sanitize_url(url)
            lines.append(f"   URL: {safe_url}")
        lines.append("")

    if len(lines) <= 4:  # Only header lines, no results
        lines.append("No results found.")

    formatted_results = "\n".join(lines)

    # Build the user prompt
    user_prompt = DEFAULT_SUMMARY_PROMPT.format(
        query=query,
        results=formatted_results
    )

    # Use default system prompt if none provided
    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    start_time = time.time()

    try:
        # Use sync client instead of async - create explicit timeout object
        timeout_obj = httpx.Timeout(timeout, connect=10.0)
        with httpx.Client(timeout=timeout_obj) as client:
            response = client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Calculate response time
            response_time = round(time.time() - start_time, 2)

            # Extract summary from response
            choices = data.get("choices", [])
            if not choices:
                logger.warning("No choices in API response")
                return {
                    "success": False,
                    "summary": None,
                    "error": "No completion returned from API",
                    "model": model,
                    "timestamp": timestamp,
                    "usage": None,
                    "stats": None,
                }

            message = choices[0].get("message", {})
            summary = message.get("content", "").strip()

            # Extract usage stats
            usage = data.get("usage", {})
            stats = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "model": model,
                "response_time": response_time,
            }

            logger.debug(f"Generated summary using model {model}")

            return {
                "success": True,
                "summary": summary,
                "error": None,
                "model": model,
                "timestamp": timestamp,
                "usage": usage,
                "stats": stats,
            }

    except httpx.TimeoutException:
        logger.warning("Timeout generating summary")
        return {
            "success": False,
            "summary": None,
            "error": f"Request timed out after {timeout}s",
            "model": model,
            "timestamp": timestamp,
            "usage": None,
            "stats": None,
        }

    except httpx.HTTPStatusError as e:
        error_msg = f"API returned error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
        except Exception:
            pass
        logger.warning(error_msg)
        return {
            "success": False,
            "summary": None,
            "error": error_msg,
            "model": model,
            "timestamp": timestamp,
            "usage": None,
            "stats": None,
        }

    except httpx.RequestError as e:
        logger.warning(f"Request error generating summary: {e}")
        return {
            "success": False,
            "summary": None,
            "error": f"Request failed: {e}",
            "model": model,
            "timestamp": timestamp,
            "usage": None,
            "stats": None,
        }

    except Exception as e:
        # Catch any unexpected errors (e.g., from URL processing, etc.)
        logger.error(f"Unexpected error generating summary: {e}")
        return {
            "success": False,
            "summary": None,
            "error": f"Unexpected error: {e}",
            "model": model,
            "timestamp": timestamp,
            "usage": None,
            "stats": None,
        }


async def generate_summary(
    results: EngineResults,
    query: str,
    endpoint: str,
    model: str,
    api_key: str | None = None,
    system_prompt: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> dict[str, t.Any]:
    """Generate an AI summary of search results.

    Args:
        results: The search results to summarize
        query: The original search query
        endpoint: The base URL of the API endpoint (e.g., "https://api.openai.com/v1")
        model: The model ID to use for summarization
        api_key: Optional API key for authentication
        system_prompt: Optional custom system prompt (uses default if not provided)
        timeout: Request timeout in seconds
        max_tokens: Maximum tokens in the response
        temperature: Temperature for generation (0.0 to 1.0)

    Returns:
        A dictionary containing:
        - success: Boolean indicating success
        - summary: The generated summary (if successful)
        - error: Error message (if failed)
        - model: The model used
        - timestamp: ISO format timestamp
        - usage: Token usage information (if available)

    Raises:
        APIError: If the API returns an error response
        TimeoutError: If the request times out
    """
    # Ensure endpoint has /v1 suffix for OpenAI-compatible APIs
    endpoint = endpoint.rstrip('/')
    if not endpoint.endswith('/v1'):
        endpoint = f"{endpoint}/v1"
    url = f"{endpoint}/chat/completions"

    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Format results for the prompt
    formatted_results = format_results_for_prompt(results, query)

    # Build the user prompt
    user_prompt = DEFAULT_SUMMARY_PROMPT.format(
        query=query,
        results=formatted_results
    )

    # Use default system prompt if none provided
    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    timestamp = datetime.utcnow().isoformat()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract summary from response
            choices = data.get("choices", [])
            if not choices:
                logger.warning("No choices in API response")
                return {
                    "success": False,
                    "summary": None,
                    "error": "No completion returned from API",
                    "model": model,
                    "timestamp": timestamp,
                    "usage": None,
                }

            message = choices[0].get("message", {})
            summary = message.get("content", "").strip()

            logger.debug(f"Generated summary using model {model}")

            return {
                "success": True,
                "summary": summary,
                "error": None,
                "model": model,
                "timestamp": timestamp,
                "usage": data.get("usage"),
            }

    except httpx.TimeoutException as e:
        logger.warning(f"Timeout generating summary: {e}")
        raise TimeoutError(f"Request timed out after {timeout}s") from e

    except httpx.HTTPStatusError as e:
        error_msg = f"API returned error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
        except Exception:
            pass
        logger.warning(error_msg)
        raise APIError(error_msg) from e

    except httpx.RequestError as e:
        logger.warning(f"Request error generating summary: {e}")
        raise APIError(f"Request failed: {e}") from e


async def stream_generate_summary(
    results: EngineResults,
    query: str,
    endpoint: str,
    model: str,
    api_key: str | None = None,
    system_prompt: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> t.AsyncGenerator[str, None]:
    """Stream an AI summary of search results.

    Args:
        results: The search results to summarize
        query: The original search query
        endpoint: The base URL of the API endpoint (e.g., "https://api.openai.com/v1")
        model: The model ID to use for summarization
        api_key: Optional API key for authentication
        system_prompt: Optional custom system prompt (uses default if not provided)
        timeout: Request timeout in seconds
        max_tokens: Maximum tokens in the response
        temperature: Temperature for generation (0.0 to 1.0)

    Yields:
        Chunks of the generated summary as they arrive from the API

    Raises:
        APIError: If the API returns an error response
        TimeoutError: If the request times out
    """
    # Ensure endpoint has /v1 suffix for OpenAI-compatible APIs
    endpoint = endpoint.rstrip('/')
    if not endpoint.endswith('/v1'):
        endpoint = f"{endpoint}/v1"
    url = f"{endpoint}/chat/completions"

    headers: dict[str, str] = {
        "Content-Type": "application/json",
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Format results for the prompt
    formatted_results = format_results_for_prompt(results, query)

    # Build the user prompt
    user_prompt = DEFAULT_SUMMARY_PROMPT.format(
        query=query,
        results=formatted_results
    )

    # Use default system prompt if none provided
    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,  # Enable streaming
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    # OpenAI streaming format: data: {"choices": [{"delta": {"content": "text"}}]}
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix

                        if data == "[DONE]":
                            break

                        try:
                            chunk_data = json.loads(data)
                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming chunk: {data}")
                            continue

    except httpx.TimeoutException as e:
        logger.warning(f"Timeout generating summary: {e}")
        raise TimeoutError(f"Request timed out after {timeout}s") from e

    except httpx.HTTPStatusError as e:
        error_msg = f"API returned error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
        except Exception:
            pass
        logger.warning(error_msg)
        raise APIError(error_msg) from e

    except httpx.RequestError as e:
        logger.warning(f"Request error generating summary: {e}")
        raise APIError(f"Request failed: {e}") from e


def should_generate_summary(
    preferences: dict[str, t.Any] | None,
    results_count: int = 0,
) -> bool:
    """Check if an AI summary should be generated based on user preferences.

    Args:
        preferences: User preferences dictionary containing AI summarization settings.
            Expected structure:
            {
                "ai_summarizer": {
                    "enabled": bool,
                    "min_results": int,
                    "endpoint": str,
                    "model": str
                }
            }
        results_count: Number of search results available

    Returns:
        True if a summary should be generated, False otherwise
    """
    if preferences is None:
        return False

    ai_config = preferences.get("ai_summarizer", {})

    # Check if AI summarization is enabled
    if not ai_config.get("enabled", False):
        return False

    # Check if we have enough results to summarize
    min_results = ai_config.get("min_results", 3)
    if results_count < min_results:
        return False

    # Check if endpoint and model are configured
    endpoint = ai_config.get("endpoint", "")
    model = ai_config.get("model", "")
    if not endpoint or not model:
        logger.debug("AI summarization enabled but endpoint or model not configured")
        return False

    return True
