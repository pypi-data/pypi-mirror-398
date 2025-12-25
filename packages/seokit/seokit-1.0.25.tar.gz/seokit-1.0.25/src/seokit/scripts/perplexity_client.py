"""
Perplexity API Client
Provides web-search enabled queries via Perplexity's sonar models.

Error Codes:
    API_KEY_MISSING: API key not configured in .env
    API_KEY_PLACEHOLDER: API key is placeholder value
    API_KEY_INVALID_FORMAT: API key format is incorrect
    API_TIMEOUT: Request timed out
    API_CONNECTION_ERROR: Network connection failed
    API_SSL_ERROR: SSL/TLS certificate error
    API_DNS_ERROR: DNS resolution failed
    API_AUTH_401: Invalid API key
    API_FORBIDDEN_403: Access forbidden
    API_RATE_LIMIT_429: Rate limit exceeded
    API_SERVER_500: Server error
    API_GATEWAY_502: Gateway error
    API_UNAVAILABLE_503: Service unavailable
    API_RESPONSE_PARSE_ERROR: JSON parse failed
    API_RESPONSE_STRUCTURE_ERROR: Response missing expected fields
"""
import json
import sys
from pathlib import Path

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import PERPLEXITY_API_KEY, PERPLEXITY_API_URL, PERPLEXITY_MODEL, validate_config


class PerplexityError(Exception):
    """Base exception for Perplexity API errors."""
    def __init__(self, message: str, error_code: str = "PERPLEXITY_ERROR", context: dict = None):
        self.error_code = error_code
        self.context = context or {}
        super().__init__(message)

    def __str__(self):
        base = f"[{self.error_code}] {super().__str__()}"
        if self.context:
            # Filter out None values and format
            ctx = {k: v for k, v in self.context.items() if v is not None}
            if ctx:
                details = ", ".join(f"{k}={v}" for k, v in ctx.items())
                base += f"\n  Context: {details}"
        return base


class APIKeyMissingError(PerplexityError):
    """Raised when API key is not configured."""
    def __init__(self, config_result: dict):
        self.env_path = config_result.get("env_path", "")
        self.suggestion = config_result.get("suggestion", "")
        self.diagnostics = config_result.get("diagnostics", {})
        super().__init__(
            config_result.get("error_message", "API key not configured"),
            error_code=config_result.get("error_code", "API_KEY_MISSING"),
            context={
                "env_path": self.env_path,
                "suggestion": self.suggestion
            }
        )


class APIRequestError(PerplexityError):
    """Raised when API request fails."""
    def __init__(self, message: str, error_code: str = "API_REQUEST_ERROR",
                 status_code: int = None, response_body: str = None,
                 request_url: str = None):
        self.status_code = status_code
        self.response_body = response_body
        self.request_url = request_url
        super().__init__(
            message,
            error_code=error_code,
            context={
                "status_code": status_code,
                "url": request_url,
                "response_preview": response_body[:200] if response_body else None
            }
        )


class APITimeoutError(PerplexityError):
    """Raised when API request times out."""
    def __init__(self, message: str, timeout_seconds: int = None, request_url: str = None):
        super().__init__(
            message,
            error_code="API_TIMEOUT",
            context={
                "timeout_seconds": timeout_seconds,
                "url": request_url
            }
        )


class APIConnectionError(PerplexityError):
    """Raised when connection to API fails."""
    def __init__(self, message: str, error_code: str = "API_CONNECTION_ERROR",
                 original_error: str = None, request_url: str = None):
        super().__init__(
            message,
            error_code=error_code,
            context={
                "original_error": original_error,
                "url": request_url
            }
        )


class APIResponseParseError(PerplexityError):
    """Raised when API response cannot be parsed."""
    def __init__(self, message: str, raw_response: str = None,
                 parse_error: str = None, error_code: str = "API_RESPONSE_PARSE_ERROR"):
        self.raw_response = raw_response
        super().__init__(
            message,
            error_code=error_code,
            context={
                "parse_error": parse_error,
                "response_preview": raw_response[:300] if raw_response else None
            }
        )


def query_perplexity(prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> dict:
    """
    Query Perplexity API with web search capability.

    Args:
        prompt: User query/prompt
        system_prompt: Optional system instructions
        max_tokens: Maximum response tokens (default 4096)

    Returns:
        dict with 'content' and 'citations' keys

    Raises:
        APIKeyMissingError: When API key is not configured
        APITimeoutError: When request times out
        APIRequestError: When API returns an error
        APIResponseParseError: When response cannot be parsed
    """
    config_result = validate_config()
    if not config_result.get("valid"):
        raise APIKeyMissingError(config_result)

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60)
    except requests.exceptions.Timeout as e:
        raise APITimeoutError(
            "Request timed out after 60 seconds. The Perplexity API may be slow or unreachable.",
            timeout_seconds=60,
            request_url=PERPLEXITY_API_URL
        ) from e
    except requests.exceptions.SSLError as e:
        raise APIConnectionError(
            "SSL/TLS certificate verification failed. This could indicate a network security issue.",
            error_code="API_SSL_ERROR",
            original_error=str(e),
            request_url=PERPLEXITY_API_URL
        ) from e
    except requests.exceptions.ConnectionError as e:
        # Try to identify specific connection issues
        error_str = str(e).lower()
        if "name or service not known" in error_str or "getaddrinfo failed" in error_str:
            raise APIConnectionError(
                "DNS resolution failed. Cannot resolve api.perplexity.ai. Check your internet connection.",
                error_code="API_DNS_ERROR",
                original_error=str(e),
                request_url=PERPLEXITY_API_URL
            ) from e
        elif "connection refused" in error_str:
            raise APIConnectionError(
                "Connection refused. The Perplexity API server may be down.",
                error_code="API_CONNECTION_REFUSED",
                original_error=str(e),
                request_url=PERPLEXITY_API_URL
            ) from e
        else:
            raise APIConnectionError(
                "Network connection failed. Check your internet connection.",
                error_code="API_CONNECTION_ERROR",
                original_error=str(e),
                request_url=PERPLEXITY_API_URL
            ) from e
    except requests.exceptions.RequestException as e:
        raise APIRequestError(
            f"HTTP request failed: {type(e).__name__}",
            error_code="API_REQUEST_FAILED",
            request_url=PERPLEXITY_API_URL
        ) from e

    # Handle HTTP errors with specific error codes
    if response.status_code != 200:
        error_map = {
            400: ("API_BAD_REQUEST_400", "Bad request. Check the request payload format."),
            401: ("API_AUTH_401", "Invalid API key. Check PERPLEXITY_API_KEY in your .env file."),
            403: ("API_FORBIDDEN_403", "Access forbidden. Your API key may lack permissions or be revoked."),
            404: ("API_NOT_FOUND_404", "API endpoint not found. The API may have changed."),
            422: ("API_VALIDATION_422", "Request validation failed. Check prompt format."),
            429: ("API_RATE_LIMIT_429", "Rate limit exceeded. Wait a few minutes before retrying."),
            500: ("API_SERVER_500", "Perplexity server error. Try again later."),
            502: ("API_GATEWAY_502", "Perplexity gateway error. The service may be temporarily unavailable."),
            503: ("API_UNAVAILABLE_503", "Perplexity service unavailable. The service is likely under maintenance."),
            504: ("API_GATEWAY_TIMEOUT_504", "Gateway timeout. The API server took too long to respond."),
        }
        error_code, error_msg = error_map.get(
            response.status_code,
            (f"API_HTTP_{response.status_code}", "Unexpected HTTP error")
        )
        raise APIRequestError(
            f"{error_msg} (HTTP {response.status_code})",
            error_code=error_code,
            status_code=response.status_code,
            response_body=response.text[:500] if response.text else None,
            request_url=PERPLEXITY_API_URL
        )

    # Parse response
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise APIResponseParseError(
            "Failed to parse API response as JSON",
            raw_response=response.text[:500] if response.text else None,
            parse_error=str(e),
            error_code="API_JSON_PARSE_ERROR"
        ) from e

    # Validate response structure with specific error messages
    if "choices" not in data:
        raise APIResponseParseError(
            "API response missing 'choices' field. The API response format may have changed.",
            raw_response=json.dumps(data)[:500],
            error_code="API_RESPONSE_NO_CHOICES"
        )

    if not data["choices"]:
        raise APIResponseParseError(
            "API response has empty 'choices' array. The model may not have generated a response.",
            raw_response=json.dumps(data)[:500],
            error_code="API_RESPONSE_EMPTY_CHOICES"
        )

    first_choice = data["choices"][0]
    if "message" not in first_choice:
        raise APIResponseParseError(
            "API response choice missing 'message' field.",
            raw_response=json.dumps(first_choice)[:500],
            error_code="API_RESPONSE_NO_MESSAGE"
        )

    if "content" not in first_choice["message"]:
        raise APIResponseParseError(
            "API response message missing 'content' field.",
            raw_response=json.dumps(first_choice["message"])[:500],
            error_code="API_RESPONSE_NO_CONTENT"
        )

    return {
        "content": data["choices"][0]["message"]["content"],
        "citations": data.get("citations", [])
    }


def format_output_with_citations(result: dict) -> str:
    """Format result with citations appended."""
    output = result["content"]
    if result["citations"]:
        output += "\n\n## Sources\n"
        for url in result["citations"]:
            output += f"- {url}\n"
    return output
