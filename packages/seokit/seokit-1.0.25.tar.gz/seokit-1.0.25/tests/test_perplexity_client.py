"""Tests for Perplexity API client edge cases."""
from unittest.mock import patch

import pytest
import requests
import responses

from seokit.config import PERPLEXITY_API_URL
from seokit.core.perplexity_client import format_output_with_citations, query_perplexity


class TestQueryPerplexitySuccess:
    """Test successful query scenarios."""

    def test_success_returns_content_and_citations(self, mock_perplexity_api, mock_perplexity_success):
        """Verify content and citations returned on success."""
        result = query_perplexity("test prompt")

        assert result["content"] == "This is a test response from Perplexity API."
        assert result["citations"] == [
            "https://example.com/source1",
            "https://example.com/source2"
        ]

    def test_success_with_system_prompt(self, mock_perplexity_api, mock_perplexity_success):
        """Verify system prompt is included in request."""
        result = query_perplexity("test prompt", system_prompt="Be helpful")

        assert result["content"] == "This is a test response from Perplexity API."
        # Verify request was made with system message
        assert len(mock_perplexity_api.calls) == 1
        request_body = mock_perplexity_api.calls[0].request.body
        assert b"system" in request_body

    def test_success_with_custom_max_tokens(self, mock_perplexity_api):
        """Verify custom max_tokens is passed."""
        query_perplexity("test prompt", max_tokens=2048)

        request_body = mock_perplexity_api.calls[0].request.body
        assert b"2048" in request_body


class TestQueryPerplexityErrors:
    """Test error handling scenarios."""

    def test_timeout_error_handling(self, mock_api_key):
        """Verify timeout error returns proper message."""
        with patch("seokit.core.perplexity_client.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()

            result = query_perplexity("test prompt")

            assert "ERROR" in result["content"]
            assert "timed out" in result["content"]
            assert result["citations"] == []

    def test_401_unauthorized(self, mock_api_key):
        """Verify 401 Unauthorized is handled."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                PERPLEXITY_API_URL,
                json={"error": "Unauthorized"},
                status=401,
            )

            result = query_perplexity("test prompt")

            assert "ERROR" in result["content"]
            assert "401" in result["content"]
            assert result["citations"] == []

    def test_429_rate_limited(self, mock_api_key):
        """Verify 429 Rate Limit is handled."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                PERPLEXITY_API_URL,
                json={"error": "Too Many Requests"},
                status=429,
            )

            result = query_perplexity("test prompt")

            assert "ERROR" in result["content"]
            assert "429" in result["content"]
            assert result["citations"] == []

    def test_500_server_error(self, mock_api_key):
        """Verify 500 Server Error is handled."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                PERPLEXITY_API_URL,
                json={"error": "Internal Server Error"},
                status=500,
            )

            result = query_perplexity("test prompt")

            assert "ERROR" in result["content"]
            assert "500" in result["content"]
            assert result["citations"] == []

    def test_malformed_json_response(self, mock_api_key):
        """Verify malformed JSON response is handled."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                PERPLEXITY_API_URL,
                body="not valid json{{{",
                status=200,
            )

            result = query_perplexity("test prompt")

            assert "ERROR" in result["content"]
            assert result["citations"] == []

    def test_empty_response(self, mock_api_key):
        """Verify empty response is handled."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                PERPLEXITY_API_URL,
                json={},
                status=200,
            )

            result = query_perplexity("test prompt")

            # Empty response will cause KeyError - should be caught
            assert "ERROR" in result["content"]
            assert result["citations"] == []

    def test_network_connection_error(self, mock_api_key):
        """Verify network/connection error is handled."""
        with patch("seokit.core.perplexity_client.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")

            result = query_perplexity("test prompt")

            assert "ERROR" in result["content"]
            assert result["citations"] == []

    def test_missing_api_key_error(self, monkeypatch):
        """Verify missing API key returns error."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "")
        with patch("seokit.core.perplexity_client.PERPLEXITY_API_KEY", ""):
            with patch("seokit.core.perplexity_client.validate_config", return_value=False):
                result = query_perplexity("test prompt")

                assert "ERROR" in result["content"]
                assert "not configured" in result["content"]
                assert result["citations"] == []


class TestFormatOutputWithCitations:
    """Test format_output_with_citations function."""

    def test_format_with_citations(self):
        """Verify formatting with citations includes Sources section."""
        result = {
            "content": "Test content here.",
            "citations": [
                "https://example.com/source1",
                "https://example.com/source2"
            ]
        }

        output = format_output_with_citations(result)

        assert "Test content here." in output
        assert "## Sources" in output
        assert "- https://example.com/source1" in output
        assert "- https://example.com/source2" in output

    def test_format_without_citations(self):
        """Verify formatting without citations omits Sources section."""
        result = {
            "content": "Test content without sources.",
            "citations": []
        }

        output = format_output_with_citations(result)

        assert output == "Test content without sources."
        assert "## Sources" not in output

    def test_format_preserves_content_exactly(self):
        """Verify content is preserved exactly as provided."""
        multiline_content = "Line 1\nLine 2\n\nLine 4 after blank"
        result = {
            "content": multiline_content,
            "citations": []
        }

        output = format_output_with_citations(result)

        assert output == multiline_content


class TestQueryPerplexityEdgeCases:
    """Test additional edge cases."""

    def test_response_without_citations_field(self, mock_api_key):
        """Verify response without citations field returns empty list."""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                PERPLEXITY_API_URL,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": "Response without citations"
                            }
                        }
                    ]
                },
                status=200,
            )

            result = query_perplexity("test prompt")

            assert result["content"] == "Response without citations"
            assert result["citations"] == []

    def test_empty_prompt(self, mock_perplexity_api):
        """Verify empty prompt is handled."""
        result = query_perplexity("")

        # Should still make request
        assert len(mock_perplexity_api.calls) == 1
        assert result["content"] == "This is a test response from Perplexity API."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
