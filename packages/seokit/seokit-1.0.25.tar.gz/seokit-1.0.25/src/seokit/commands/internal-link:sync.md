Sync internal links from sitemap: $ARGUMENTS

## Error Codes Reference

| Code | Error Code | Description | Suggestion |
|------|------------|-------------|------------|
| 0 | - | Success | Links saved to `.seokit-links.yaml` |
| 1 | `VALIDATION_INVALID_URL_SCHEME` | URL must be http/https | Use full URL |
| 1 | `VALIDATION_BLOCKED_URL` | Localhost/private IP blocked | Use public URL |
| 1 | `SYNC_NO_URLS_FOUND` | Sitemap has no URLs | Check sitemap format |
| 1 | `SYNC_NO_ENTRIES_CREATED` | No keywords extracted | Check page titles |
| 2 | `NETWORK_TIMEOUT` | Request timed out | Check connectivity |
| 2 | `NETWORK_DNS_ERROR` | Cannot resolve domain | Check URL spelling |
| 2 | `NETWORK_SSL_ERROR` | SSL certificate error | Check site SSL |
| 2 | `NETWORK_CONNECTION_*` | Connection failed | Check connectivity |
| 2 | `HTTP_ERROR_*` | HTTP error (404, 403, etc) | Check URL exists |
| 3 | `SYNC_WRITE_*` | Cannot write links file | Check permissions |
| 4 | `XML_PARSE_ERROR` | Invalid XML sitemap | Check URL points to XML |
| 10 | `SEOKIT_NOT_INSTALLED` | SEOKit directory missing | Run `seokit setup` |
| 11 | `VENV_NOT_FOUND` | Python venv missing | Run `seokit setup` |
| 12 | `SCRIPT_NOT_FOUND` | Script missing | Run `seokit update` |
| 13 | `VENV_ACTIVATION_FAILED` | Venv activation failed | Run `seokit setup --force` |
| 130 | - | User cancelled (Ctrl+C) | Re-run when ready |

---

## Instructions

Run the internal link sync using the sitemap URL:

```bash
# Step 0: Validate arguments
if [ -z "$ARGUMENTS" ]; then
    echo "[USAGE_ERROR] No sitemap URL provided"
    echo ""
    echo "Usage: /internal-link:sync <sitemap-url>"
    echo "Example: /internal-link:sync https://example.com/sitemap.xml"
    exit 1
fi

SITEMAP_URL="$ARGUMENTS"

# Step 1: Validate URL format
if ! echo "$SITEMAP_URL" | grep -qE "^https?://"; then
    echo "[URL_VALIDATION_ERROR] Invalid URL format: $SITEMAP_URL"
    echo ""
    echo "URL must start with http:// or https://"
    echo "Example: https://example.com/sitemap.xml"
    exit 1
fi

# Step 2: Check current directory is writable
if [ ! -w "$(pwd)" ]; then
    echo "[CWD_NOT_WRITABLE] Cannot write to current directory: $(pwd)"
    echo "Suggestion: Change to a writable directory or check permissions"
    exit 3
fi

export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"

# Step 3: Check if SEOKit is installed
if [ ! -d "$SEOKIT_HOME" ]; then
    echo "[SEOKIT_NOT_INSTALLED]"
    echo "Error: SEOKit directory not found"
    echo "  Expected: $SEOKIT_HOME"
    echo "  Suggestion: Run 'seokit setup' to install SEOKit first"
    exit 10
fi

# Step 4: Check if venv exists
if [ ! -d "$SEOKIT_HOME/venv" ]; then
    echo "[VENV_NOT_FOUND]"
    echo "Error: Python virtual environment not found"
    echo "  Expected: $SEOKIT_HOME/venv"
    echo "  Suggestion: Run 'seokit setup' to create the virtual environment"
    exit 11
fi

# Step 5: Check if script exists
SCRIPT_PATH="$SEOKIT_HOME/scripts/internal-link-manager.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[SCRIPT_NOT_FOUND]"
    echo "Error: internal-link-manager.py not found"
    echo "  Expected: $SCRIPT_PATH"
    echo "  Suggestion: Run 'seokit update' to install latest scripts"
    exit 12
fi

# Step 6: Activate venv
VENV_ACTIVATE="$SEOKIT_HOME/venv/bin/activate"
source "$VENV_ACTIVATE" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[VENV_ACTIVATION_FAILED]"
    echo "Error: Failed to activate Python virtual environment"
    echo "  Path: $VENV_ACTIVATE"
    echo "  Suggestion: Delete and recreate venv with 'seokit setup --force'"
    exit 13
fi

echo "[OK] Environment validated, starting sitemap sync..."
echo "URL: $SITEMAP_URL"
echo ""

# Step 7: Run the sync
python "$SCRIPT_PATH" sync "$SITEMAP_URL"
EXIT_CODE=$?

# Step 8: Handle exit codes with detailed messages
case $EXIT_CODE in
    0)
        echo ""
        echo "════════════════════════════════════════"
        echo "[OK] Sitemap sync completed successfully"
        echo "Links saved to: .seokit-links.yaml"
        echo "════════════════════════════════════════"
        ;;
    1)
        echo ""
        echo "──────────────────────────────────────"
        echo "[VALIDATION_ERROR]"
        echo ""
        echo "Input validation failed."
        echo ""
        echo "Common causes:"
        echo "  - URL doesn't start with http:// or https://"
        echo "  - URL is localhost or private IP (blocked)"
        echo "  - Sitemap has no URLs"
        echo "  - No keywords could be extracted"
        echo ""
        echo "See error details above for specifics."
        echo "──────────────────────────────────────"
        ;;
    2)
        echo ""
        echo "──────────────────────────────────────"
        echo "[NETWORK_ERROR]"
        echo ""
        echo "Network request failed."
        echo ""
        echo "Common causes:"
        echo "  - Request timed out"
        echo "  - DNS resolution failed"
        echo "  - SSL certificate error"
        echo "  - Connection refused"
        echo "  - HTTP error (404, 403, 500, etc)"
        echo ""
        echo "See error details above for specifics."
        echo "──────────────────────────────────────"
        ;;
    3)
        echo ""
        echo "──────────────────────────────────────"
        echo "[FILE_ERROR]"
        echo ""
        echo "Could not save the links file."
        echo ""
        echo "Common causes:"
        echo "  - Permission denied in current directory"
        echo "  - Disk is full"
        echo ""
        echo "Suggestion: Check permissions with: ls -la ."
        echo "──────────────────────────────────────"
        ;;
    4)
        echo ""
        echo "──────────────────────────────────────"
        echo "[XML_PARSE_ERROR]"
        echo ""
        echo "Failed to parse sitemap XML."
        echo ""
        echo "Common causes:"
        echo "  - URL doesn't point to a valid XML file"
        echo "  - Malformed XML content"
        echo "  - HTML error page returned instead"
        echo ""
        echo "Suggestion: Verify URL returns valid XML in browser"
        echo "──────────────────────────────────────"
        ;;
    6)
        echo ""
        echo "──────────────────────────────────────"
        echo "[UNEXPECTED_ERROR]"
        echo ""
        echo "An unexpected error occurred."
        echo "See traceback above for debugging info."
        echo "──────────────────────────────────────"
        ;;
    130)
        echo ""
        echo "[USER_CANCELLED] Operation cancelled by user."
        ;;
    *)
        echo ""
        echo "[UNKNOWN_ERROR] Exited with code: $EXIT_CODE"
        echo "Check the output above for details."
        ;;
esac

exit $EXIT_CODE
```

## Expected Output

The script will:
1. Fetch the sitemap.xml from the provided URL
2. Extract all page URLs (max 500)
3. Fetch each page to extract the title
4. Extract keywords from titles
5. Save URL-keyword mappings to `.seokit-links.yaml`

## Next Steps

After syncing, use:
- `/internal-link:list` to view all entries
- `/internal-link <article.md>` to apply links to an article
