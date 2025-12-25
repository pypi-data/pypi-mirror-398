"""
Search Intent Analyzer
Analyzes user search intent for a given keyword using Perplexity API.

Exit codes:
    0: Success
    1: Usage error (no keyword provided)
    2: API key missing/invalid (can fallback to Claude Code)
    3: API request error (network, timeout, auth, rate limit)
    4: File write error (permissions, disk space)
    5: Unexpected error (bug or unhandled case)

Error codes (for debugging):
    USAGE_NO_KEYWORD: No keyword argument provided
    USAGE_EMPTY_KEYWORD: Keyword is empty or whitespace only

    CONFIG_API_KEY_MISSING: PERPLEXITY_API_KEY not set in .env
    CONFIG_API_KEY_PLACEHOLDER: API key is still placeholder value (pplx-xxx...)
    CONFIG_API_KEY_INVALID_FORMAT: API key doesn't start with 'pplx-'
    CONFIG_DOTENV_MISSING: python-dotenv package not installed
    CONFIG_ENV_PARSE_ERROR: .env file has syntax errors

    API_TIMEOUT: Request timed out (>60s)
    API_CONNECTION_ERROR: General network failure
    API_DNS_ERROR: Cannot resolve api.perplexity.ai
    API_SSL_ERROR: SSL/TLS certificate issue
    API_CONNECTION_REFUSED: Server refused connection

    API_AUTH_401: Invalid API key
    API_FORBIDDEN_403: Access denied / key revoked
    API_RATE_LIMIT_429: Rate limit exceeded
    API_SERVER_500: Perplexity internal error
    API_GATEWAY_502: Perplexity gateway error
    API_UNAVAILABLE_503: Perplexity under maintenance
    API_GATEWAY_TIMEOUT_504: Gateway timeout

    API_JSON_PARSE_ERROR: Response is not valid JSON
    API_RESPONSE_NO_CHOICES: Missing 'choices' in response
    API_RESPONSE_EMPTY_CHOICES: Empty 'choices' array
    API_RESPONSE_NO_MESSAGE: Missing 'message' in choice
    API_RESPONSE_NO_CONTENT: Missing 'content' in message

    FILE_PERMISSION_ERROR: Cannot write to output file
    FILE_DISK_FULL: No disk space left
    FILE_READONLY_FS: File system is read-only
    FILE_WRITE_ERROR: General file write failure
"""
import json
import sys
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUTS_DIR, get_env_status, get_output_dir_status
from perplexity_client import (
    APIConnectionError,
    APIKeyMissingError,
    APIRequestError,
    APIResponseParseError,
    APITimeoutError,
    format_output_with_citations,
    query_perplexity,
)


def analyze_search_intent(keyword: str) -> str:
    """
    Analyze search intent for a keyword.

    Args:
        keyword: The main keyword to analyze

    Returns:
        Formatted analysis string with citations

    Raises:
        APIKeyMissingError: When API key is not configured
        APIConnectionError: When network connection fails
        APITimeoutError: When request times out
        APIRequestError: When API returns an error
        APIResponseParseError: When response is malformed
        OSError: When file write fails
    """
    system = """You are an expert SEO analyst specializing in search intent analysis.
Provide actionable, data-driven insights based on current search trends and SERP analysis."""

    prompt = f"""Analyze the search intent for the keyword: "{keyword}"

Provide a comprehensive analysis including:

## 1. Primary Search Intent
- Type: (informational / navigational / transactional / commercial investigation)
- Confidence level and reasoning

## 2. Secondary Intents
- Any related or secondary intents users might have

## 3. User Profile & Pain Points
- Who is searching for this?
- What problems are they trying to solve?
- What stage of the buyer journey are they in?

## 4. Top Questions Users Ask
List the top 5-7 questions users commonly ask about this topic

## 5. Related Keywords & Topics
- Semantically related keywords
- Topics that should be covered for comprehensive content

## 6. Content Format Recommendations
- Best content format (guide, listicle, comparison, tutorial, etc.)
- Recommended word count range
- Key elements to include

## 7. SERP Features to Target
- Featured snippets opportunity
- People Also Ask boxes
- Other SERP features

Be specific, actionable, and base your analysis on current search trends."""

    result = query_perplexity(prompt, system)
    output = format_output_with_citations(result)

    # Save to outputs directory
    output_file = OUTPUTS_DIR / "search-intent.md"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Search Intent Analysis: {keyword}\n\n")
            f.write(output)
    except PermissionError as e:
        raise OSError(
            f"[FILE_PERMISSION_ERROR] Cannot write to '{output_file}'.\n"
            f"Permission denied. Check directory write permissions.\n"
            f"Directory: {OUTPUTS_DIR}\n"
            f"Original error: {e}"
        ) from e
    except OSError as e:
        # More specific error messages based on error type
        if e.errno == 28:  # ENOSPC - No space left on device
            raise OSError(
                f"[FILE_DISK_FULL] Cannot write to '{output_file}'.\n"
                f"No disk space left. Free up space and try again.\n"
                f"Original error: {e}"
            ) from e
        elif e.errno == 30:  # EROFS - Read-only file system
            raise OSError(
                f"[FILE_READONLY_FS] Cannot write to '{output_file}'.\n"
                f"File system is read-only.\n"
                f"Original error: {e}"
            ) from e
        else:
            raise OSError(
                f"[FILE_WRITE_ERROR] Failed to write output file '{output_file}'.\n"
                f"Error type: {type(e).__name__} (errno={e.errno})\n"
                f"Check directory permissions and disk space.\n"
                f"Original error: {e}"
            ) from e

    print(f"\n✓ Analysis saved to: {output_file}")
    return output


def print_error(error_code: str, message: str, details: dict = None):
    """
    Print formatted error to stderr with structured details.

    Format:
        [ERROR_CODE]
        Error: <message>
          key: value
          key: value
    """
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[{error_code}]", file=sys.stderr)
    print(f"Error: {message}", file=sys.stderr)
    if details:
        print("-" * 40, file=sys.stderr)
        for key, value in details.items():
            if value is not None:
                # Format key nicely (convert underscores to spaces)
                formatted_key = key.replace("_", " ")
                print(f"  {formatted_key}: {value}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)


def _get_suggestion_for_status_code(status_code: int) -> str:
    """Return a suggestion based on HTTP status code."""
    suggestions = {
        400: "Check if the keyword contains invalid characters",
        401: "Verify your API key is correct in the .env file",
        403: "Your API key may be revoked. Generate a new one at https://perplexity.ai/settings/api",
        429: "Wait 1-2 minutes before retrying. Consider upgrading your API plan for higher limits.",
        500: "Perplexity is having issues. Try again in a few minutes.",
        502: "Perplexity gateway error. Usually resolves within minutes.",
        503: "Perplexity is under maintenance. Check https://status.perplexity.ai",
        504: "Request took too long. Try a shorter keyword or try again later."
    }
    return suggestions.get(status_code, "Check the error details above and try again")


if __name__ == "__main__":
    # === USAGE VALIDATION ===
    if len(sys.argv) < 2:
        print_error(
            "USAGE_NO_KEYWORD",
            "No keyword provided",
            {
                "usage": "python search-intent-analyzer.py <keyword>",
                "example": "python search-intent-analyzer.py 'best running shoes'",
                "hint": "Wrap multi-word keywords in quotes"
            }
        )
        sys.exit(1)

    keyword = " ".join(sys.argv[1:])

    # Validate keyword is not empty/whitespace
    if not keyword.strip():
        print_error(
            "USAGE_EMPTY_KEYWORD",
            "Keyword is empty or whitespace only",
            {
                "received": repr(keyword),
                "usage": "python search-intent-analyzer.py <keyword>",
                "hint": "Provide a meaningful search keyword"
            }
        )
        sys.exit(1)

    # Warn about very short keywords
    if len(keyword.strip()) < 3:
        print(f"Warning: Very short keyword '{keyword}' may yield broad results.", file=sys.stderr)

    print(f"Analyzing search intent for: {keyword}\n")
    print("=" * 50)

    # Print diagnostic info for debugging
    env_status = get_env_status()
    output_status = get_output_dir_status()

    try:
        print(analyze_search_intent(keyword))

    except APIKeyMissingError as e:
        # Provide specific guidance based on the error code
        error_code = e.error_code
        details = {
            "env_path": e.env_path,
        }

        # Add context-specific suggestions
        if error_code == "CONFIG_API_KEY_MISSING":
            details["problem"] = "PERPLEXITY_API_KEY not found in environment"
            details["fix_step_1"] = f"Open: {e.env_path}"
            details["fix_step_2"] = "Add line: PERPLEXITY_API_KEY=pplx-your-key-here"
            details["get_key_at"] = "https://perplexity.ai/settings/api"
        elif error_code == "CONFIG_API_KEY_PLACEHOLDER":
            details["problem"] = "API key is still the placeholder value"
            details["fix"] = f"Replace 'pplx-xxx...' with your real API key in {e.env_path}"
            details["get_key_at"] = "https://perplexity.ai/settings/api"
        elif error_code == "CONFIG_API_KEY_INVALID_FORMAT":
            details["problem"] = "API key format is incorrect"
            details["expected_format"] = "pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            details["fix"] = "Ensure your API key starts with 'pplx-'"
        elif error_code == "CONFIG_DOTENV_MISSING":
            details["problem"] = "python-dotenv package not installed"
            details["fix"] = "Run: pip install python-dotenv"
        elif error_code == "CONFIG_ENV_PARSE_ERROR":
            details["problem"] = ".env file has syntax errors"
            details["fix"] = "Check .env format: KEY=value (no quotes, no spaces around =)"
        else:
            details["suggestion"] = e.suggestion

        # Add env status if there's an error
        if env_status.get("error"):
            details["env_load_error"] = env_status.get("error")

        print_error(error_code, str(e), details)
        sys.exit(2)

    except APITimeoutError as e:
        timeout_secs = e.context.get("timeout_seconds", 60)
        print_error(
            e.error_code,
            str(e),
            {
                "timeout_seconds": timeout_secs,
                "url": e.context.get("url"),
                "possible_causes": "Slow network, Perplexity API overloaded, long-running query",
                "try_1": "Wait 30 seconds and run the command again",
                "try_2": "Check https://status.perplexity.ai for API status",
                "try_3": "Try a shorter/simpler keyword"
            }
        )
        sys.exit(3)

    except APIConnectionError as e:
        error_code = e.error_code
        details = {
            "url": e.context.get("url"),
        }

        # Add specific guidance based on connection error type
        if error_code == "API_DNS_ERROR":
            details["problem"] = "Cannot resolve api.perplexity.ai hostname"
            details["check_1"] = "Verify internet connection: ping google.com"
            details["check_2"] = "Check DNS settings (try 8.8.8.8 or 1.1.1.1)"
            details["check_3"] = "Disable VPN if active"
        elif error_code == "API_SSL_ERROR":
            details["problem"] = "SSL/TLS certificate verification failed"
            details["check_1"] = "Ensure system date/time is correct"
            details["check_2"] = "Update CA certificates: sudo update-ca-certificates"
            details["check_3"] = "Check if proxy/firewall is intercepting HTTPS"
        elif error_code == "API_CONNECTION_REFUSED":
            details["problem"] = "Perplexity API server refused connection"
            details["likely_cause"] = "API server is down or blocking connections"
            details["check"] = "Visit https://status.perplexity.ai"
        else:
            details["problem"] = "Network connection failed"
            details["check_1"] = "Verify internet connection"
            details["check_2"] = "Check firewall/proxy settings"
            details["check_3"] = "Try again in a few minutes"

        if e.context.get("original_error"):
            details["technical_detail"] = str(e.context.get("original_error"))[:200]

        print_error(error_code, str(e), details)
        sys.exit(3)

    except APIRequestError as e:
        status = e.status_code
        details = {
            "status_code": status,
            "url": e.request_url,
        }

        # Add status-specific actionable guidance
        if status == 400:
            details["problem"] = "Bad request - invalid payload sent to API"
            details["likely_cause"] = "Keyword contains unsupported characters"
            details["fix"] = "Try a simpler keyword without special characters"
        elif status == 401:
            details["problem"] = "API key is invalid or expired"
            details["fix_1"] = "Verify your API key at https://perplexity.ai/settings/api"
            details["fix_2"] = "Update PERPLEXITY_API_KEY in your .env file"
            details["fix_3"] = "Regenerate a new API key if needed"
        elif status == 403:
            details["problem"] = "Access denied - API key may be revoked or lack permissions"
            details["fix_1"] = "Check if your API key is still active"
            details["fix_2"] = "Verify your Perplexity account is in good standing"
            details["fix_3"] = "Generate a new API key at https://perplexity.ai/settings/api"
        elif status == 429:
            details["problem"] = "Rate limit exceeded - too many requests"
            details["fix_1"] = "Wait 1-2 minutes before retrying"
            details["fix_2"] = "Consider upgrading your API plan for higher limits"
            details["current_limit"] = "Check your plan limits at https://perplexity.ai/settings/api"
        elif status == 500:
            details["problem"] = "Perplexity internal server error"
            details["cause"] = "Issue on Perplexity's side, not your fault"
            details["fix"] = "Wait a few minutes and try again"
            details["status_page"] = "https://status.perplexity.ai"
        elif status == 502:
            details["problem"] = "Perplexity gateway error"
            details["cause"] = "Temporary infrastructure issue"
            details["fix"] = "Usually resolves within a few minutes - try again"
        elif status == 503:
            details["problem"] = "Perplexity service unavailable"
            details["cause"] = "API may be under maintenance"
            details["check"] = "https://status.perplexity.ai"
            details["fix"] = "Wait and try again later"
        elif status == 504:
            details["problem"] = "Gateway timeout - request took too long"
            details["cause"] = "Query was too complex or API is overloaded"
            details["fix_1"] = "Try a shorter/simpler keyword"
            details["fix_2"] = "Wait a few minutes and try again"
        else:
            details["problem"] = f"Unexpected HTTP error ({status})"
            details["suggestion"] = _get_suggestion_for_status_code(status)

        # Add response preview for debugging (if available)
        if e.response_body:
            details["response_preview"] = e.response_body[:150]

        print_error(e.error_code, str(e), details)
        sys.exit(3)

    except APIResponseParseError as e:
        error_code = e.error_code
        details = {}

        # Add specific guidance based on parse error type
        if error_code == "API_JSON_PARSE_ERROR":
            details["problem"] = "API returned non-JSON response"
            details["likely_cause"] = "Perplexity API returned HTML error page or malformed data"
            details["fix"] = "This is usually a temporary API issue - try again in a few minutes"
        elif error_code == "API_RESPONSE_NO_CHOICES":
            details["problem"] = "Response missing 'choices' field"
            details["likely_cause"] = "API response format changed or query was rejected"
            details["fix"] = "Try rephrasing your keyword or report to SEOKit maintainers"
        elif error_code == "API_RESPONSE_EMPTY_CHOICES":
            details["problem"] = "API returned empty results"
            details["likely_cause"] = "Model couldn't generate a response for this query"
            details["fix"] = "Try a different or more specific keyword"
        elif error_code == "API_RESPONSE_NO_MESSAGE":
            details["problem"] = "Response structure is invalid (missing message)"
            details["likely_cause"] = "API version mismatch or temporary API issue"
            details["fix"] = "Try again - report if issue persists"
        elif error_code == "API_RESPONSE_NO_CONTENT":
            details["problem"] = "Response has no content"
            details["likely_cause"] = "Model returned empty content"
            details["fix"] = "Try a different keyword"
        else:
            details["problem"] = "Failed to parse API response"
            details["fix"] = "This may be a temporary API issue - try again"

        # Add parse error details if available
        if e.context.get("parse_error"):
            details["parse_error"] = e.context.get("parse_error")

        # Add response preview for debugging
        if e.raw_response:
            preview = e.raw_response[:150]
            if len(e.raw_response) > 150:
                preview += "..."
            details["response_preview"] = preview

        print_error(error_code, str(e), details)
        sys.exit(3)

    except OSError as e:
        error_str = str(e)
        details = {
            "output_dir": str(OUTPUTS_DIR),
        }

        # Parse the error message for specific error codes
        if "[FILE_PERMISSION_ERROR]" in error_str:
            details["problem"] = "Cannot write to output file - permission denied"
            details["fix_1"] = f"Check write permissions: ls -la {OUTPUTS_DIR.parent}"
            details["fix_2"] = f"Try: chmod 755 {OUTPUTS_DIR}"
            details["fix_3"] = "Run from a directory where you have write access"
        elif "[FILE_DISK_FULL]" in error_str:
            details["problem"] = "No disk space left"
            details["fix_1"] = "Free up disk space: df -h"
            details["fix_2"] = "Delete unnecessary files or move to a different drive"
        elif "[FILE_READONLY_FS]" in error_str:
            details["problem"] = "File system is read-only"
            details["fix_1"] = "Check if disk is mounted read-only"
            details["fix_2"] = "Remount with write permissions or use a different location"
        elif "[FILE_WRITE_ERROR]" in error_str:
            details["problem"] = "General file write failure"
            details["check_1"] = "Verify the output directory exists"
            details["check_2"] = "Check if disk is read-only"
            details["check_3"] = "Verify file system is not corrupted"
        else:
            # Generic OSError handling
            details["problem"] = "File system error occurred"
            if hasattr(e, 'errno') and e.errno:
                details["errno"] = e.errno
                # Common errno explanations
                errno_map = {
                    2: "File or directory not found",
                    13: "Permission denied",
                    17: "File already exists",
                    21: "Is a directory (expected file)",
                    22: "Invalid argument",
                    28: "No space left on device",
                    30: "Read-only file system",
                }
                details["errno_meaning"] = errno_map.get(e.errno, "Unknown error")

        # Add output status if there's an error
        if output_status.get("error"):
            details["output_status_error"] = output_status.get("error")

        print_error("FILE_ERROR", str(e), details)
        sys.exit(4)

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Operation cancelled by user (Ctrl+C).", file=sys.stderr)
        print("No files were modified.", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        error_type = type(e).__name__
        error_module = type(e).__module__

        print_error(
            f"UNEXPECTED_{error_type.upper()}",
            str(e),
            {
                "error_type": error_type,
                "module": error_module,
                "keyword": keyword,
                "python_version": sys.version.split()[0],
                "traceback": "See below"
            }
        )
        # Print full traceback for debugging
        print("\n--- Full Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("--- End Traceback ---\n", file=sys.stderr)

        print("This is an unexpected error. Please report this issue:", file=sys.stderr)
        print("  https://github.com/your-repo/seokit/issues", file=sys.stderr)
        print("\nInclude the error details and traceback above.", file=sys.stderr)
        sys.exit(5)
