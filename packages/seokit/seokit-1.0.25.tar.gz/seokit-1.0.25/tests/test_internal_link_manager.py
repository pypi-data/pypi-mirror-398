"""Tests for internal-link-manager.py"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "seokit" / "scripts"))

from importlib import import_module

# Import the module
internal_link_manager = import_module("internal-link-manager")

normalize_text = internal_link_manager.normalize_text
count_words = internal_link_manager.count_words
is_in_heading = internal_link_manager.is_in_heading
is_in_code_block = internal_link_manager.is_in_code_block
is_already_linked = internal_link_manager.is_already_linked
extract_keyword_from_title = internal_link_manager.extract_keyword_from_title
find_keyword_matches = internal_link_manager.find_keyword_matches
get_section_type = internal_link_manager.get_section_type


class TestNormalizeText:
    def test_basic_lowercase(self):
        assert normalize_text("Hello World") == "hello world"

    def test_vietnamese_text(self):
        result = normalize_text("Xin Chào Việt Nam")
        assert result == "xin chào việt nam"

    def test_whitespace_strip(self):
        assert normalize_text("  hello  ") == "hello"

    def test_empty_string(self):
        assert normalize_text("") == ""


class TestCountWords:
    def test_basic_count(self):
        assert count_words("hello world test") == 3

    def test_multiple_spaces(self):
        assert count_words("hello   world") == 2

    def test_empty_string(self):
        assert count_words("") == 0

    def test_vietnamese_words(self):
        assert count_words("Xin chào Việt Nam") == 4


class TestIsInHeading:
    def test_h1_heading(self):
        content = "# This is heading\nSome text"
        assert is_in_heading(content, 5) is True

    def test_h2_heading(self):
        content = "## Heading two\nContent here"
        assert is_in_heading(content, 8) is True

    def test_not_in_heading(self):
        content = "# Heading\nThis is body text"
        assert is_in_heading(content, 15) is False

    def test_h6_heading(self):
        content = "###### Deep heading\nText"
        assert is_in_heading(content, 10) is True


class TestIsInCodeBlock:
    def test_inside_code_block(self):
        content = "Text\n```python\ncode here\n```\nMore text"
        assert is_in_code_block(content, 20) is True

    def test_outside_code_block(self):
        content = "Text\n```python\ncode\n```\nMore text"
        assert is_in_code_block(content, 30) is False

    def test_before_code_block(self):
        content = "Before\n```\ncode\n```"
        assert is_in_code_block(content, 3) is False


class TestIsAlreadyLinked:
    def test_inside_link_text(self):
        content = "Check [this link](https://example.com) here"
        assert is_already_linked(content, 7, 4) is True

    def test_outside_link(self):
        content = "Check [link](url) and this text"
        assert is_already_linked(content, 25, 4) is False

    def test_plain_text(self):
        content = "Just plain text without links"
        assert is_already_linked(content, 5, 5) is False


class TestExtractKeywordFromTitle:
    def test_remove_site_suffix(self):
        # "Best" is removed as common prefix, keeping core keyword
        result = extract_keyword_from_title("Best Running Shoes | Nike Store")
        assert result == "Running Shoes"

    def test_remove_dash_suffix(self):
        result = extract_keyword_from_title("How to Cook - Recipe Blog")
        assert result == "How to Cook"

    def test_simple_title(self):
        result = extract_keyword_from_title("Simple Title")
        assert result == "Simple Title"

    def test_vietnamese_title(self):
        result = extract_keyword_from_title("Hướng dẫn nấu phở | Blog Ẩm Thực")
        assert result == "nấu phở"


class TestFindKeywordMatches:
    def test_exact_match(self):
        content = "The running shoes are great for running"
        matches = find_keyword_matches(content, "running")
        assert len(matches) == 2

    def test_case_insensitive(self):
        content = "The Running shoes are RUNNING fast"
        matches = find_keyword_matches(content, "running")
        assert len(matches) == 2

    def test_no_match(self):
        content = "Hello world"
        matches = find_keyword_matches(content, "python")
        assert len(matches) == 0

    def test_word_boundary(self):
        # Should not match "running" in "runningshoes"
        content = "I love runningshoes"
        matches = find_keyword_matches(content, "running")
        assert len(matches) == 0


class TestGetSectionType:
    def test_body_default(self):
        content = "## Introduction\nSome text\n## Main Content\nBody text here"
        pos = content.find("Body text")
        assert get_section_type(content, pos) == "body"

    def test_faq_section(self):
        content = "## FAQ\nQuestion and answer here"
        pos = content.find("Question")
        assert get_section_type(content, pos) == "faq"

    def test_conclusion_section(self):
        content = "## Body\nText\n## Kết luận\nFinal thoughts"
        pos = content.find("Final")
        assert get_section_type(content, pos) == "conclusion"


class TestApplyLinksIntegration:
    def test_apply_links_basic(self, tmp_path):
        # Create test YAML
        links_file = tmp_path / ".seokit-links.yaml"
        links_file.write_text("""entries:
  - url: https://example.com/shoes
    title: Best Running Shoes
    keyword: running shoes
""")

        # Create test article
        article = tmp_path / "article.md"
        article.write_text("""# My Article

This is about running shoes and how to choose them.

## Body

The best running shoes are important for athletes.
""")

        # Mock cwd to tmp_path
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = internal_link_manager.apply_links(str(article))

        assert result["links_inserted"] >= 1

        # Verify link was inserted
        content = article.read_text()
        assert "[running shoes]" in content or "[Running shoes]" in content


class TestSyncSitemapUnit:
    @patch("requests.get")
    def test_fetch_sitemap_urls(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = b"""<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/page1</loc></url>
  <url><loc>https://example.com/page2</loc></url>
</urlset>"""
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        urls = internal_link_manager.fetch_sitemap_urls("https://example.com/sitemap.xml")
        assert len(urls) == 2
        assert "https://example.com/page1" in urls
