Analyze search intent for keyword: $ARGUMENTS

## Instructions

Run the search intent analysis using Perplexity API:

```bash
# Validate arguments
if [ -z "$ARGUMENTS" ]; then
    echo "ERROR: No keyword provided"
    echo "Usage: /search-intent <keyword>"
    echo "Example: /search-intent best running shoes"
    exit 1
fi

# Generate slug from keyword
KEYWORD_SLUG="$ARGUMENTS"
KEYWORD_SLUG="${KEYWORD_SLUG// /-}"
KEYWORD_SLUG="${KEYWORD_SLUG,,}"

export SEOKIT_HOME="$HOME/.claude/seokit"
export SEOKIT_KEYWORD="$KEYWORD_SLUG"

# Check if SEOKit is installed
if [ ! -d "$SEOKIT_HOME" ]; then
    echo "[SEOKIT_NOT_INSTALLED]"
    echo "Error: SEOKit directory not found"
    echo "  Expected: $SEOKIT_HOME"
    echo "  Suggestion: Run 'seokit setup' to install SEOKit first"
    exit 10
fi

# Check if venv exists
if [ ! -d "$SEOKIT_HOME/venv" ]; then
    echo "[VENV_NOT_FOUND]"
    echo "Error: Python virtual environment not found"
    echo "  Expected: $SEOKIT_HOME/venv"
    echo "  Suggestion: Run 'seokit setup' to create the virtual environment"
    exit 11
fi

# Check if script exists
if [ ! -f "$SEOKIT_HOME/scripts/search-intent-analyzer.py" ]; then
    echo "[SCRIPT_NOT_FOUND]"
    echo "Error: search-intent-analyzer.py not found"
    echo "  Expected: $SEOKIT_HOME/scripts/search-intent-analyzer.py"
    echo "  Suggestion: Reinstall SEOKit with 'pip install --upgrade seokit'"
    exit 12
fi

# Activate venv and run the analyzer
source "$SEOKIT_HOME/venv/bin/activate" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[VENV_ACTIVATION_FAILED]"
    echo "Error: Failed to activate Python virtual environment"
    echo "  Path: $SEOKIT_HOME/venv/bin/activate"
    echo "  Suggestion: Delete and recreate venv with 'seokit setup --force'"
    exit 13
fi

python "$SEOKIT_HOME/scripts/search-intent-analyzer.py" "$ARGUMENTS"
EXIT_CODE=$?

# Handle exit codes with detailed messages
case $EXIT_CODE in
    0)
        echo ""
        echo "✓ Search intent analysis completed successfully"
        ;;
    1)
        echo ""
        echo "──────────────────────────────────────"
        echo "Usage error. Provide a keyword to analyze."
        echo "──────────────────────────────────────"
        ;;
    2)
        echo ""
        echo "──────────────────────────────────────"
        echo "API KEY ERROR"
        echo ""
        echo "The Perplexity API key is missing or invalid."
        echo ""
        echo "Options:"
        echo "  1. Add PERPLEXITY_API_KEY to $SEOKIT_HOME/.env"
        echo "     Get key from: https://perplexity.ai/settings/api"
        echo ""
        echo "  2. Ask Claude Code to run analysis directly:"
        echo "     \"Run search intent analysis for $ARGUMENTS directly\""
        echo "──────────────────────────────────────"
        ;;
    3)
        echo ""
        echo "──────────────────────────────────────"
        echo "API REQUEST ERROR"
        echo ""
        echo "The request to Perplexity API failed."
        echo "See error details above for specific cause."
        echo ""
        echo "Common causes:"
        echo "  - Network connectivity issues"
        echo "  - Rate limit exceeded (wait 1-2 min)"
        echo "  - API service temporarily unavailable"
        echo "  - Invalid/revoked API key"
        echo "──────────────────────────────────────"
        ;;
    4)
        echo ""
        echo "──────────────────────────────────────"
        echo "FILE WRITE ERROR"
        echo ""
        echo "Could not save the output file."
        echo "See error details above for specific cause."
        echo ""
        echo "Common causes:"
        echo "  - Insufficient permissions in output directory"
        echo "  - Disk is full"
        echo "  - Output path is read-only"
        echo "──────────────────────────────────────"
        ;;
    5)
        echo ""
        echo "──────────────────────────────────────"
        echo "UNEXPECTED ERROR"
        echo ""
        echo "An unexpected error occurred."
        echo "See traceback above for debugging info."
        echo ""
        echo "If this persists, please report at:"
        echo "  https://github.com/your-repo/seokit/issues"
        echo "──────────────────────────────────────"
        ;;
    130)
        echo ""
        echo "Operation cancelled by user."
        ;;
esac

exit $EXIT_CODE
```

## Exit Codes Reference

| Code | Error Code | Meaning | Action |
|------|------------|---------|--------|
| 0 | - | Success | Analysis saved to `./{keyword}/search-intent.md` |
| 1 | USAGE_NO_KEYWORD | No keyword provided | Provide a keyword argument |
| 2 | CONFIG_API_KEY_* | API key missing/invalid | Add key to .env OR ask Claude to run directly |
| 3 | API_* | API request failed | Check error details - network, auth, rate limit |
| 4 | FILE_* | File write error | Check directory permissions and disk space |
| 5 | UNEXPECTED_* | Unexpected error | Check traceback for debugging |
| 10 | SEOKIT_NOT_INSTALLED | SEOKit directory missing | Run `seokit setup` |
| 11 | VENV_NOT_FOUND | Python venv missing | Run `seokit setup` |
| 12 | SCRIPT_NOT_FOUND | Script missing | Reinstall SEOKit |
| 13 | VENV_ACTIVATION_FAILED | Venv activation failed | Run `seokit setup --force` |
| 130 | - | User cancelled (Ctrl+C) | Re-run when ready |

## Error Code Prefixes

- `CONFIG_*`: Configuration errors (API key, env file)
- `API_*`: API-related errors (network, auth, rate limit)
- `FILE_*`: File system errors (write, permissions)
- `UNEXPECTED_*`: Unexpected errors requiring investigation

## Expected Output

The script will provide:
1. **Primary Search Intent** - Type (informational/navigational/transactional/commercial)
2. **User Profile & Pain Points** - Who searches this and why
3. **Top Questions** - Common questions users ask
4. **Related Keywords** - Semantically related terms
5. **Content Recommendations** - Best format and approach
6. **SERP Features** - Opportunities for featured snippets, etc.

Results are saved to: `./{keyword-slug}/search-intent.md`

## Fallback: Run with Claude Code

If API key is missing (exit code 2), Claude Code can perform the analysis directly using web search. Just ask:
> "Run search intent analysis for [keyword] directly"

## Next Steps
After analyzing search intent, run `/top-article $ARGUMENTS` to find competitor articles.
