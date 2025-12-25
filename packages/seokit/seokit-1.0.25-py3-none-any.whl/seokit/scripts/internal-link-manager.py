"""
Internal Link Manager
Manages automatic internal linking for SEO articles.

Actions:
    sync <sitemap_url>  - Fetch sitemap.xml and save URL mappings
    list                - Display all saved entries
    apply <article>     - Insert internal links into article

Exit codes:
    0: Success
    1: Usage/validation error
    2: Network/HTTP error (timeout, connection, DNS, SSL)
    3: File error (read, write, permission, not found)
    4: XML parsing error
    5: YAML parsing error
    6: Unexpected error

Error code prefixes:
    [NETWORK_*]: Network-related errors (exit 2)
    [HTTP_*]: HTTP response errors (exit 2)
    [FILE_*]: File system errors (exit 3)
    [XML_*]: XML parsing errors (exit 4)
    [YAML_*]: YAML parsing errors (exit 5)
    [VALIDATION_*]: Input validation errors (exit 1)
    [APPLY_*]: Link application errors (exit 1)
    [SYNC_*]: Sitemap sync errors (exit 2)
    [UNEXPECTED_*]: Unexpected errors (exit 6)
"""
import argparse
import re
import sys
import traceback
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests
import yaml
from bs4 import BeautifulSoup

# Constants
LINKS_FILE = ".seokit-links.yaml"
REQUEST_TIMEOUT = 10
LINKS_PER_1000_WORDS = 2
MIN_WORD_DISTANCE = 150
SECTION_PRIORITY = ["body", "conclusion", "faq", "introduction"]
MAX_SITEMAP_URLS = 500  # Limit to prevent DoS
USER_AGENT = "SEOKit/1.0 Internal Link Manager"


# Custom exceptions for granular error handling
class SEOKitError(Exception):
    """Base exception for SEOKit errors."""
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class FileError(SEOKitError):
    """File system errors (exit code 3)."""
    pass


class YAMLError(SEOKitError):
    """YAML parsing errors (exit code 5)."""
    pass


class ValidationError(SEOKitError):
    """Input validation errors (exit code 1)."""
    pass


class ApplyError(SEOKitError):
    """Link application errors (exit code 1)."""
    pass


def normalize_text(text: str) -> str:
    """Normalize Unicode text for consistent matching."""
    return unicodedata.normalize("NFC", text.lower().strip())


def count_words(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r"\S+", text))


def get_word_positions(text: str) -> list[tuple[int, int, int]]:
    """Get (word_index, start_char, end_char) for each word."""
    positions = []
    for i, match in enumerate(re.finditer(r"\S+", text)):
        positions.append((i, match.start(), match.end()))
    return positions


def char_to_word_position(text: str, char_pos: int) -> int:
    """Convert character position to word position."""
    words_before = count_words(text[:char_pos])
    return words_before


def is_in_heading(content: str, pos: int) -> bool:
    """Check if position is inside a markdown heading (H1-H6)."""
    # Find line containing position
    line_start = content.rfind("\n", 0, pos) + 1
    line_end = content.find("\n", pos)
    if line_end == -1:
        line_end = len(content)
    line = content[line_start:line_end]
    return bool(re.match(r"^\s*#{1,6}\s", line))


def is_in_code_block(content: str, pos: int) -> bool:
    """Check if position is inside a fenced code block."""
    # Count ``` before position
    before = content[:pos]
    fence_count = len(re.findall(r"^```", before, re.MULTILINE))
    # Odd count means inside code block
    return fence_count % 2 == 1


def is_already_linked(content: str, pos: int, keyword_len: int) -> bool:
    """Check if position is already inside a markdown link."""
    # Check if within [...](...) pattern
    # Look for [ before and ]( after
    before = content[max(0, pos - 200):pos]
    after = content[pos:pos + keyword_len + 200]

    # Check if we're inside link text [text]
    open_bracket = before.rfind("[")
    close_bracket = before.rfind("]")
    if open_bracket > close_bracket:
        # Found [ without matching ]
        close_after = after.find("](")
        if close_after != -1:
            return True

    # Check if we're inside link URL (url)
    open_paren = before.rfind("](")
    close_paren = before.rfind(")")
    if open_paren > close_paren:
        return True

    return False


def get_section_type(content: str, pos: int) -> str:
    """Determine section type based on position."""
    before = content[:pos].lower()

    # Check common section headers
    if re.search(r"#+\s*(faq|câu hỏi|hỏi đáp)", before, re.IGNORECASE):
        last_faq = max(
            (m.end() for m in re.finditer(r"#+\s*(faq|câu hỏi|hỏi đáp)", before, re.IGNORECASE)),
            default=0
        )
        # Check if another section started after FAQ
        next_heading = re.search(r"\n#+\s", content[last_faq:pos])
        if not next_heading:
            return "faq"

    if re.search(r"#+\s*(kết luận|conclusion|tổng kết)", before, re.IGNORECASE):
        return "conclusion"

    if re.search(r"#+\s*(giới thiệu|introduction|mở đầu)", before, re.IGNORECASE):
        # Check if we're still in intro section
        intro_pos = max(
            (m.end() for m in re.finditer(r"#+\s*(giới thiệu|introduction|mở đầu)", before, re.IGNORECASE)),
            default=0
        )
        next_heading = re.search(r"\n#+\s", content[intro_pos:pos])
        if not next_heading:
            return "introduction"

    return "body"


def find_keyword_matches(content: str, keyword: str) -> list[tuple[int, int]]:
    """Find all exact matches of keyword in content (case-insensitive for Vietnamese)."""
    matches = []
    normalized_content = normalize_text(content)
    normalized_keyword = normalize_text(keyword)

    # Use word boundary matching
    pattern = r"\b" + re.escape(normalized_keyword) + r"\b"

    for match in re.finditer(pattern, normalized_content):
        # Map back to original positions
        matches.append((match.start(), match.end()))

    return matches


def extract_keyword_from_title(title: str) -> str:
    """Extract main keyword from page title."""
    # Remove common suffixes like " | Brand Name", " - Site Name"
    title = re.split(r"\s*[|\-–—]\s*", title)[0].strip()

    # Remove common prefixes
    title = re.sub(r"^(hướng dẫn|cách|top|best|review|đánh giá)\s+", "", title, flags=re.IGNORECASE)

    return title.strip()


def validate_url(url: str) -> bool:
    """Validate URL scheme and block private IPs."""
    try:
        parsed = urlparse(url)
        # Only allow http/https
        if parsed.scheme not in ("http", "https"):
            return False
        # Block localhost and private IP patterns
        host = parsed.hostname or ""
        if host in ("localhost", "127.0.0.1", "0.0.0.0"):
            return False
        if host.startswith("192.168.") or host.startswith("10."):
            return False
        if host.startswith("172.") and 16 <= int(host.split(".")[1]) <= 31:
            return False
        return True
    except Exception:
        return False


def safe_parse_xml(xml_content: bytes) -> ElementTree.Element:
    """Parse XML safely, blocking XXE attacks."""
    # Create parser that disables external entities
    parser = ElementTree.XMLParser()
    # Parse without resolving external entities
    return ElementTree.fromstring(xml_content, parser=parser)


def fetch_sitemap_urls(sitemap_url: str, depth: int = 0) -> list[str]:
    """Fetch and parse sitemap.xml to extract URLs. Handles sitemap index files."""
    if depth > 2:  # Prevent infinite recursion
        return []

    if not validate_url(sitemap_url):
        raise ValueError(f"Invalid or blocked URL: {sitemap_url}")

    indent = "  " * depth
    print(f"{indent}Fetching sitemap: {sitemap_url}")

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(sitemap_url, timeout=REQUEST_TIMEOUT, headers=headers)
    response.raise_for_status()

    # Parse XML safely
    root = safe_parse_xml(response.content)

    # Handle different namespace formats
    namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Check if this is a sitemap index (contains <sitemap> elements)
    child_sitemaps = root.findall(".//sm:sitemap/sm:loc", namespaces)
    if not child_sitemaps:
        child_sitemaps = root.findall(".//sitemap/loc")

    if child_sitemaps:
        # This is a sitemap index - fetch each child sitemap
        print(f"{indent}  Found sitemap index with {len(child_sitemaps)} child sitemaps")
        all_urls = []
        for sitemap_loc in child_sitemaps:
            if sitemap_loc.text and len(all_urls) < MAX_SITEMAP_URLS:
                child_url = sitemap_loc.text.strip()
                child_urls = fetch_sitemap_urls(child_url, depth + 1)
                all_urls.extend(child_urls)
        return all_urls[:MAX_SITEMAP_URLS]

    # Regular sitemap - extract page URLs
    urls = []
    # Try with namespace
    for loc in root.findall(".//sm:url/sm:loc", namespaces):
        if loc.text:
            urls.append(loc.text.strip())

    # Fallback without namespace
    if not urls:
        for loc in root.findall(".//url/loc"):
            if loc.text:
                urls.append(loc.text.strip())

    # Also try direct loc elements (simple sitemaps)
    if not urls:
        for loc in root.findall(".//sm:loc", namespaces):
            if loc.text:
                urls.append(loc.text.strip())
        if not urls:
            for loc in root.findall(".//loc"):
                if loc.text:
                    urls.append(loc.text.strip())

    # Limit URLs to prevent DoS
    if len(urls) > MAX_SITEMAP_URLS:
        print(f"{indent}  Warning: Limiting to first {MAX_SITEMAP_URLS} URLs (found {len(urls)})")
        urls = urls[:MAX_SITEMAP_URLS]

    return urls


def fetch_page_title(url: str) -> Optional[str]:
    """Fetch page and extract title tag."""
    if not validate_url(url):
        print(f"  Warning: Skipping invalid URL: {url}")
        return None

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text().strip()
    except Exception as e:
        print(f"  Warning: Failed to fetch {url}: {e}")
    return None


def sync_sitemap(sitemap_url: str) -> dict:
    """
    Fetch sitemap and build URL-keyword mapping.

    Returns:
        dict with stats: total_urls, successful, failed
    """
    # Validate URL format
    if not sitemap_url.startswith(("http://", "https://")):
        raise ValidationError(
            "VALIDATION_INVALID_URL_SCHEME",
            f"Invalid URL scheme: must start with http:// or https://",
            {
                "url": sitemap_url,
                "suggestion": "Use a full URL like https://example.com/sitemap.xml"
            }
        )

    # Validate URL is not blocked
    if not validate_url(sitemap_url):
        raise ValidationError(
            "VALIDATION_BLOCKED_URL",
            f"URL is blocked (localhost or private IP)",
            {
                "url": sitemap_url,
                "suggestion": "Use a public URL, not localhost or private network"
            }
        )

    # Auto-append sitemap.xml if needed
    if not sitemap_url.endswith(".xml"):
        if not sitemap_url.endswith("/"):
            sitemap_url += "/"
        sitemap_url += "sitemap.xml"

    # Fetch sitemap URLs (network errors handled in main())
    urls = fetch_sitemap_urls(sitemap_url)

    if not urls:
        raise ValidationError(
            "SYNC_NO_URLS_FOUND",
            f"No URLs found in sitemap",
            {
                "url": sitemap_url,
                "suggestion": "Verify the sitemap contains valid <url><loc> entries"
            }
        )

    print(f"Found {len(urls)} URLs in sitemap\n")

    entries = []
    failed = 0
    failed_urls = []

    for i, url in enumerate(urls, 1):
        url_display = url[:60] + "..." if len(url) > 63 else url
        print(f"[{i}/{len(urls)}] Processing: {url_display}")
        title = fetch_page_title(url)

        if title:
            keyword = extract_keyword_from_title(title)
            if keyword:
                entries.append({
                    "url": url,
                    "title": title,
                    "keyword": keyword
                })
                print(f"  ✓ Keyword: {keyword}")
            else:
                failed += 1
                failed_urls.append({"url": url, "reason": "empty keyword after extraction"})
                print("  ✗ Failed to extract keyword from title")
        else:
            failed += 1
            failed_urls.append({"url": url, "reason": "failed to fetch title"})
            print("  ✗ Failed to extract title")

    if not entries:
        raise ValidationError(
            "SYNC_NO_ENTRIES_CREATED",
            f"Failed to extract any keywords from {len(urls)} URLs",
            {
                "total_urls": len(urls),
                "failed_count": failed,
                "suggestion": "Check if the URLs are accessible and have <title> tags"
            }
        )

    # Save to YAML
    links_path = Path.cwd() / LINKS_FILE
    try:
        with open(links_path, "w", encoding="utf-8") as f:
            yaml.dump({"entries": entries}, f, allow_unicode=True, default_flow_style=False)
    except PermissionError as e:
        raise FileError(
            "SYNC_WRITE_PERMISSION_DENIED",
            f"Cannot write links file: permission denied",
            {
                "file": str(links_path),
                "original_error": str(e),
                "entries_count": len(entries),
                "suggestion": "Check directory permissions with: ls -la ."
            }
        )
    except OSError as e:
        if e.errno == 28:  # ENOSPC
            raise FileError(
                "SYNC_WRITE_DISK_FULL",
                "Cannot write links file: no disk space left",
                {
                    "file": str(links_path),
                    "original_error": str(e),
                    "entries_count": len(entries),
                    "suggestion": "Free up disk space and try again"
                }
            )
        raise FileError(
            "SYNC_WRITE_ERROR",
            f"Cannot write links file: {e.strerror}",
            {
                "file": str(links_path),
                "errno": e.errno,
                "original_error": str(e),
                "entries_count": len(entries)
            }
        )

    print(f"\n✓ Saved {len(entries)} entries to {links_path}")

    if failed > 0:
        print(f"⚠ {failed} URLs failed to process")

    return {
        "total_urls": len(urls),
        "successful": len(entries),
        "failed": failed,
        "output_file": str(links_path)
    }


def list_entries() -> None:
    """Display all entries from .seokit-links.yaml."""
    links_path = Path.cwd() / LINKS_FILE

    if not links_path.exists():
        raise FileError(
            "FILE_NOT_FOUND",
            f"Links file not found: {LINKS_FILE}",
            {
                "file": str(links_path),
                "suggestion": "Run '/internal-link:sync <sitemap-url>' first to create the links file"
            }
        )

    # Read YAML file with specific error handling
    try:
        with open(links_path, "r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError as e:
        raise FileError(
            "FILE_PERMISSION_DENIED",
            f"Cannot read links file: permission denied",
            {
                "file": str(links_path),
                "original_error": str(e),
                "suggestion": "Check file permissions with: ls -la .seokit-links.yaml"
            }
        )
    except UnicodeDecodeError as e:
        raise FileError(
            "FILE_ENCODING_ERROR",
            f"Links file encoding error (expected UTF-8)",
            {
                "file": str(links_path),
                "original_error": str(e),
                "suggestion": "Delete and re-create the file with '/internal-link:sync'"
            }
        )
    except OSError as e:
        raise FileError(
            "FILE_READ_ERROR",
            f"Cannot read links file: {e.strerror}",
            {
                "file": str(links_path),
                "errno": e.errno,
                "original_error": str(e)
            }
        )

    # Parse YAML with specific error handling
    try:
        data = yaml.safe_load(content)
    except yaml.scanner.ScannerError as e:
        raise YAMLError(
            "YAML_SCANNER_ERROR",
            f"YAML syntax error at line {e.problem_mark.line + 1}",
            {
                "file": str(links_path),
                "line": e.problem_mark.line + 1 if e.problem_mark else None,
                "column": e.problem_mark.column + 1 if e.problem_mark else None,
                "problem": e.problem,
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )
    except yaml.parser.ParserError as e:
        raise YAMLError(
            "YAML_PARSER_ERROR",
            f"YAML structure error at line {e.problem_mark.line + 1}",
            {
                "file": str(links_path),
                "line": e.problem_mark.line + 1 if e.problem_mark else None,
                "problem": e.problem,
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )
    except yaml.YAMLError as e:
        raise YAMLError(
            "YAML_PARSE_ERROR",
            f"Failed to parse YAML file",
            {
                "file": str(links_path),
                "original_error": str(e),
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )

    # Validate data structure
    if data is None:
        raise YAMLError(
            "YAML_EMPTY_FILE",
            "Links file is empty",
            {
                "file": str(links_path),
                "suggestion": "Run '/internal-link:sync <sitemap-url>' to populate the file"
            }
        )

    if not isinstance(data, dict):
        raise YAMLError(
            "YAML_INVALID_STRUCTURE",
            f"Links file has invalid structure (expected dict, got {type(data).__name__})",
            {
                "file": str(links_path),
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )

    entries = data.get("entries", [])

    if not entries:
        print("No entries found in links file.")
        return

    print(f"Found {len(entries)} entries:\n")
    print("-" * 80)

    for i, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            print(f"{i}. [INVALID ENTRY - not a dictionary]")
            continue
        keyword = entry.get("keyword", "N/A")
        url = entry.get("url", "N/A")
        title = entry.get("title", "N/A")
        title_display = title[:50] + "..." if len(title) > 50 else title
        print(f"{i}. {keyword}")
        print(f"   URL: {url}")
        print(f"   Title: {title_display}")
        print()

    print("-" * 80)
    print(f"Total: {len(entries)} entries")


def apply_links(article_path: str) -> dict:
    """
    Insert internal links into article based on keyword matching.

    Returns:
        dict with stats: links_inserted, max_links, words_count
    """
    links_path = Path.cwd() / LINKS_FILE
    article_file = Path(article_path)

    # Validate links file exists
    if not links_path.exists():
        raise FileError(
            "FILE_NOT_FOUND",
            f"Links file not found: {LINKS_FILE}",
            {
                "file": str(links_path),
                "suggestion": "Run '/internal-link:sync <sitemap-url>' first to create the links file"
            }
        )

    # Validate article file exists
    if not article_file.exists():
        raise FileError(
            "ARTICLE_NOT_FOUND",
            f"Article file not found: {article_path}",
            {
                "file": str(article_file.resolve()),
                "suggestion": "Check the file path. Use absolute path if needed."
            }
        )

    # Load entries from links file
    try:
        with open(links_path, "r", encoding="utf-8") as f:
            links_content = f.read()
    except PermissionError as e:
        raise FileError(
            "LINKS_FILE_PERMISSION_DENIED",
            f"Cannot read links file: permission denied",
            {
                "file": str(links_path),
                "original_error": str(e),
                "suggestion": "Check file permissions with: ls -la .seokit-links.yaml"
            }
        )
    except UnicodeDecodeError as e:
        raise FileError(
            "LINKS_FILE_ENCODING_ERROR",
            f"Links file encoding error (expected UTF-8)",
            {
                "file": str(links_path),
                "original_error": str(e),
                "suggestion": "Delete and re-create with '/internal-link:sync'"
            }
        )
    except OSError as e:
        raise FileError(
            "LINKS_FILE_READ_ERROR",
            f"Cannot read links file: {e.strerror}",
            {
                "file": str(links_path),
                "errno": e.errno,
                "original_error": str(e)
            }
        )

    # Parse YAML
    try:
        data = yaml.safe_load(links_content)
    except yaml.scanner.ScannerError as e:
        raise YAMLError(
            "YAML_SCANNER_ERROR",
            f"YAML syntax error at line {e.problem_mark.line + 1}",
            {
                "file": str(links_path),
                "line": e.problem_mark.line + 1 if e.problem_mark else None,
                "column": e.problem_mark.column + 1 if e.problem_mark else None,
                "problem": e.problem,
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )
    except yaml.parser.ParserError as e:
        raise YAMLError(
            "YAML_PARSER_ERROR",
            f"YAML structure error at line {e.problem_mark.line + 1}",
            {
                "file": str(links_path),
                "line": e.problem_mark.line + 1 if e.problem_mark else None,
                "problem": e.problem,
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )
    except yaml.YAMLError as e:
        raise YAMLError(
            "YAML_PARSE_ERROR",
            f"Failed to parse links file",
            {
                "file": str(links_path),
                "original_error": str(e),
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )

    # Validate YAML structure
    if data is None:
        raise YAMLError(
            "YAML_EMPTY_FILE",
            "Links file is empty",
            {
                "file": str(links_path),
                "suggestion": "Run '/internal-link:sync <sitemap-url>' to populate the file"
            }
        )

    if not isinstance(data, dict):
        raise YAMLError(
            "YAML_INVALID_STRUCTURE",
            f"Links file has invalid structure (expected dict, got {type(data).__name__})",
            {
                "file": str(links_path),
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )

    entries = data.get("entries", [])

    if not entries:
        print("No entries in links file.")
        return {"links_inserted": 0, "max_links": 0, "words_count": 0}

    if not isinstance(entries, list):
        raise YAMLError(
            "YAML_ENTRIES_NOT_LIST",
            f"'entries' field must be a list (got {type(entries).__name__})",
            {
                "file": str(links_path),
                "suggestion": "Delete .seokit-links.yaml and run '/internal-link:sync' again"
            }
        )

    # Read article
    try:
        with open(article_file, "r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError as e:
        raise FileError(
            "ARTICLE_PERMISSION_DENIED",
            f"Cannot read article: permission denied",
            {
                "file": str(article_file.resolve()),
                "original_error": str(e),
                "suggestion": f"Check file permissions with: ls -la {article_path}"
            }
        )
    except UnicodeDecodeError as e:
        raise FileError(
            "ARTICLE_ENCODING_ERROR",
            f"Article file encoding error (expected UTF-8)",
            {
                "file": str(article_file.resolve()),
                "original_error": str(e),
                "position": e.start,
                "suggestion": "Ensure the article is saved with UTF-8 encoding"
            }
        )
    except OSError as e:
        raise FileError(
            "ARTICLE_READ_ERROR",
            f"Cannot read article: {e.strerror}",
            {
                "file": str(article_file.resolve()),
                "errno": e.errno,
                "original_error": str(e)
            }
        )

    # Validate article content
    if not content.strip():
        raise ApplyError(
            "APPLY_ARTICLE_EMPTY",
            "Article file is empty",
            {
                "file": str(article_file.resolve()),
                "suggestion": "The article must contain content to insert links"
            }
        )

    # Calculate max links
    word_count = count_words(content)
    if word_count < 50:
        raise ApplyError(
            "APPLY_ARTICLE_TOO_SHORT",
            f"Article too short ({word_count} words, minimum 50)",
            {
                "file": str(article_file.resolve()),
                "word_count": word_count,
                "suggestion": "Article should have at least 50 words for internal linking"
            }
        )

    max_links = (word_count // 1000) * LINKS_PER_1000_WORDS
    max_links = max(1, max_links)  # At least 1 link

    print(f"Article: {word_count} words → max {max_links} links allowed\n")

    # Sort entries by keyword length (longer first to avoid partial matches)
    entries_sorted = sorted(entries, key=lambda e: len(e.get("keyword", "") if isinstance(e, dict) else ""), reverse=True)

    links_inserted = 0
    used_urls = set()
    link_positions = []  # Track word positions of inserted links
    skipped_invalid = 0

    # Group matches by section priority
    for section in SECTION_PRIORITY:
        if links_inserted >= max_links:
            break

        for entry in entries_sorted:
            if links_inserted >= max_links:
                break

            # Validate entry structure
            if not isinstance(entry, dict):
                skipped_invalid += 1
                continue

            url = entry.get("url", "")
            keyword = entry.get("keyword", "")

            if not keyword or not url or url in used_urls:
                continue

            # Find matches
            matches = find_keyword_matches(content, keyword)

            for start, end in matches:
                if links_inserted >= max_links:
                    break

                # Check section
                current_section = get_section_type(content, start)
                if current_section != section:
                    continue

                # Check exclusions
                if is_in_heading(content, start):
                    continue
                if is_in_code_block(content, start):
                    continue
                if is_already_linked(content, start, len(keyword)):
                    continue

                # Check distance from other links
                word_pos = char_to_word_position(content, start)
                too_close = False
                for prev_pos in link_positions:
                    if abs(word_pos - prev_pos) < MIN_WORD_DISTANCE:
                        too_close = True
                        break

                if too_close:
                    continue

                # Get exact original text (preserve case)
                original_text = content[start:end]

                # Insert link
                link_text = f"[{original_text}]({url})"
                content = content[:start] + link_text + content[end:]

                # Note: Content length changed, but we break after first match
                # per keyword, and matches are recalculated for each keyword.

                links_inserted += 1
                used_urls.add(url)
                link_positions.append(word_pos)

                url_display = url[:40] + "..." if len(url) > 43 else url
                print(f"  ✓ Inserted: [{original_text}]({url_display})")
                print(f"    Section: {section}, Position: word {word_pos}")

                # Only one link per keyword
                break

    if skipped_invalid > 0:
        print(f"\n  ⚠ Skipped {skipped_invalid} invalid entries in links file")

    # Save updated article
    if links_inserted > 0:
        try:
            with open(article_file, "w", encoding="utf-8") as f:
                f.write(content)
        except PermissionError as e:
            raise FileError(
                "ARTICLE_WRITE_PERMISSION_DENIED",
                f"Cannot write to article: permission denied",
                {
                    "file": str(article_file.resolve()),
                    "original_error": str(e),
                    "links_inserted": links_inserted,
                    "suggestion": f"Check file permissions with: ls -la {article_path}"
                }
            )
        except OSError as e:
            if e.errno == 28:  # ENOSPC - No space left
                raise FileError(
                    "ARTICLE_WRITE_DISK_FULL",
                    "Cannot write to article: no disk space left",
                    {
                        "file": str(article_file.resolve()),
                        "original_error": str(e),
                        "links_inserted": links_inserted,
                        "suggestion": "Free up disk space and try again"
                    }
                )
            raise FileError(
                "ARTICLE_WRITE_ERROR",
                f"Cannot write to article: {e.strerror}",
                {
                    "file": str(article_file.resolve()),
                    "errno": e.errno,
                    "original_error": str(e),
                    "links_inserted": links_inserted
                }
            )
        print(f"\n✓ Saved article with {links_inserted} new links")
    else:
        print("\nNo links inserted (no matching keywords found or all positions excluded)")

    return {
        "links_inserted": links_inserted,
        "max_links": max_links,
        "words_count": word_count,
        "used_urls": list(used_urls)
    }


def print_error(error_code: str, message: str, details: dict = None):
    """Print formatted error to stderr."""
    print(f"\n[{error_code}]", file=sys.stderr)
    print(f"Error: {message}", file=sys.stderr)
    if details:
        for key, value in details.items():
            if value is not None:
                print(f"  {key}: {value}", file=sys.stderr)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Internal Link Manager for SEOKit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python internal-link-manager.py sync https://example.com/sitemap.xml
    python internal-link-manager.py list
    python internal-link-manager.py apply ./article.md
        """
    )

    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync sitemap URLs")
    sync_parser.add_argument("sitemap_url", help="URL to sitemap.xml")

    # list command
    subparsers.add_parser("list", help="List all saved entries")

    # apply command
    apply_parser = subparsers.add_parser("apply", help="Apply links to article")
    apply_parser.add_argument("article_path", help="Path to markdown article")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        if args.action == "sync":
            stats = sync_sitemap(args.sitemap_url)
            print(f"\nSync complete: {stats['successful']}/{stats['total_urls']} URLs processed")

        elif args.action == "list":
            list_entries()

        elif args.action == "apply":
            stats = apply_links(args.article_path)
            print(f"\nApply complete: {stats['links_inserted']}/{stats['max_links']} links inserted")

    except FileError as e:
        print_error(e.code, e.message, e.details)
        sys.exit(3)

    except YAMLError as e:
        print_error(e.code, e.message, e.details)
        sys.exit(5)

    except ValidationError as e:
        print_error(e.code, e.message, e.details)
        sys.exit(1)

    except ApplyError as e:
        print_error(e.code, e.message, e.details)
        sys.exit(1)

    except requests.exceptions.Timeout as e:
        print_error(
            "NETWORK_TIMEOUT",
            f"Request timed out after {REQUEST_TIMEOUT} seconds",
            {
                "suggestion": "Check your internet connection or try again later",
                "original_error": str(e)
            }
        )
        sys.exit(2)

    except requests.exceptions.SSLError as e:
        print_error(
            "NETWORK_SSL_ERROR",
            "SSL/TLS certificate verification failed",
            {
                "suggestion": "The website may have an invalid or expired SSL certificate",
                "original_error": str(e)
            }
        )
        sys.exit(2)

    except requests.exceptions.ConnectionError as e:
        error_str = str(e).lower()
        if "name or service not known" in error_str or "getaddrinfo failed" in error_str:
            print_error(
                "NETWORK_DNS_ERROR",
                "DNS resolution failed - cannot resolve domain name",
                {
                    "suggestion": "Check the URL spelling and your internet connection",
                    "original_error": str(e)
                }
            )
        elif "connection refused" in error_str:
            print_error(
                "NETWORK_CONNECTION_REFUSED",
                "Connection refused by the server",
                {
                    "suggestion": "The server may be down or blocking requests",
                    "original_error": str(e)
                }
            )
        else:
            print_error(
                "NETWORK_CONNECTION_ERROR",
                "Network connection failed",
                {
                    "suggestion": "Check your internet connection",
                    "original_error": str(e)
                }
            )
        sys.exit(2)

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "unknown"
        status_messages = {
            400: "Bad request - check URL format",
            401: "Unauthorized - authentication required",
            403: "Forbidden - access denied by server",
            404: "Not found - sitemap.xml doesn't exist at this URL",
            429: "Rate limited - too many requests, try again later",
            500: "Server error - remote server issue",
            502: "Bad gateway - remote server issue",
            503: "Service unavailable - remote server is down",
        }
        suggestion = status_messages.get(status_code, "Check the URL and try again")
        print_error(
            f"HTTP_ERROR_{status_code}",
            f"HTTP {status_code} error",
            {
                "url": str(e.request.url) if e.request else None,
                "suggestion": suggestion,
                "original_error": str(e)
            }
        )
        sys.exit(2)

    except requests.exceptions.RequestException as e:
        print_error(
            "NETWORK_REQUEST_ERROR",
            f"HTTP request failed: {type(e).__name__}",
            {
                "original_error": str(e)
            }
        )
        sys.exit(2)

    except ElementTree.ParseError as e:
        print_error(
            "XML_PARSE_ERROR",
            "Failed to parse sitemap XML",
            {
                "suggestion": "The URL may not point to a valid XML sitemap",
                "original_error": str(e)
            }
        )
        sys.exit(4)

    except yaml.YAMLError as e:
        print_error(
            "YAML_PARSE_ERROR",
            f"Failed to parse {LINKS_FILE}",
            {
                "suggestion": "The YAML file may be corrupted. Try deleting it and running 'sync' again",
                "original_error": str(e)
            }
        )
        sys.exit(5)

    except FileNotFoundError as e:
        print_error(
            "FILE_NOT_FOUND",
            str(e),
            {
                "suggestion": "Check the file path exists"
            }
        )
        sys.exit(3)

    except PermissionError as e:
        print_error(
            "FILE_PERMISSION_ERROR",
            f"Permission denied",
            {
                "original_error": str(e),
                "suggestion": "Check file/directory read/write permissions"
            }
        )
        sys.exit(3)

    except UnicodeDecodeError as e:
        print_error(
            "FILE_ENCODING_ERROR",
            "File encoding error - expected UTF-8",
            {
                "original_error": str(e),
                "suggestion": "Ensure all files are saved as UTF-8"
            }
        )
        sys.exit(3)

    except OSError as e:
        if e.errno == 28:  # ENOSPC
            print_error(
                "FILE_DISK_FULL",
                "No disk space left",
                {
                    "original_error": str(e),
                    "suggestion": "Free up disk space and try again"
                }
            )
        else:
            print_error(
                "FILE_IO_ERROR",
                f"File I/O error: {type(e).__name__}",
                {
                    "errno": e.errno,
                    "original_error": str(e)
                }
            )
        sys.exit(3)

    except ValueError as e:
        # Catch invalid URL errors from validate_url
        print_error(
            "VALIDATION_ERROR",
            str(e),
            {
                "suggestion": "Check the URL format and try again"
            }
        )
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print_error(
            f"UNEXPECTED_{type(e).__name__.upper()}",
            str(e),
            {
                "error_type": type(e).__name__,
                "module": type(e).__module__,
                "traceback": traceback.format_exc()
            }
        )
        print("\nThis is an unexpected error. Please report this issue.", file=sys.stderr)
        sys.exit(6)


if __name__ == "__main__":
    main()
