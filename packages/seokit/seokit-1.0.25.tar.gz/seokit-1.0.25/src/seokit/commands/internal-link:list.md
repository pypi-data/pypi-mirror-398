List all internal link entries.

## Error Codes Reference

| Code | Error Code | Description | Suggestion |
|------|------------|-------------|------------|
| 0 | - | Success | Entries displayed |
| 3 | `FILE_NOT_FOUND` | `.seokit-links.yaml` not found | Run `/internal-link:sync` first |
| 3 | `FILE_PERMISSION_DENIED` | Cannot read links file | Check file permissions |
| 3 | `FILE_ENCODING_ERROR` | File not UTF-8 | Delete and re-sync |
| 5 | `YAML_*` | YAML parsing error | Delete and re-sync |
| 6 | `UNEXPECTED_*` | Unexpected error | Check traceback |
| 10 | `SEOKIT_NOT_INSTALLED` | SEOKit directory missing | Run `seokit setup` |
| 11 | `VENV_NOT_FOUND` | Python venv missing | Run `seokit setup` |
| 12 | `SCRIPT_NOT_FOUND` | Script missing | Run `seokit update` |
| 13 | `VENV_ACTIVATION_FAILED` | Venv activation failed | Run `seokit setup --force` |
| 130 | - | User cancelled (Ctrl+C) | Re-run when ready |

---

## Instructions

Display all saved URL-keyword mappings:

```bash
# Step 0: Check links file exists first (quick check)
if [ ! -f ".seokit-links.yaml" ]; then
    echo "[NO_LINKS_FILE] No links file found: .seokit-links.yaml"
    echo ""
    echo "You must run '/internal-link:sync <sitemap-url>' first to create the links file."
    echo ""
    echo "Example:"
    echo "  /internal-link:sync https://example.com/sitemap.xml"
    exit 1
fi

# Step 1: Check links file is readable
if [ ! -r ".seokit-links.yaml" ]; then
    echo "[FILE_PERMISSION_ERROR] Cannot read: .seokit-links.yaml"
    echo "Suggestion: Check file permissions with: ls -la .seokit-links.yaml"
    exit 3
fi

export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"

# Step 2: Check if SEOKit is installed
if [ ! -d "$SEOKIT_HOME" ]; then
    echo "[SEOKIT_NOT_INSTALLED]"
    echo "Error: SEOKit directory not found"
    echo "  Expected: $SEOKIT_HOME"
    echo "  Suggestion: Run 'seokit setup' to install SEOKit first"
    exit 10
fi

# Step 3: Check if venv exists
if [ ! -d "$SEOKIT_HOME/venv" ]; then
    echo "[VENV_NOT_FOUND]"
    echo "Error: Python virtual environment not found"
    echo "  Expected: $SEOKIT_HOME/venv"
    echo "  Suggestion: Run 'seokit setup' to create the virtual environment"
    exit 11
fi

# Step 4: Check if script exists
SCRIPT_PATH="$SEOKIT_HOME/scripts/internal-link-manager.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[SCRIPT_NOT_FOUND]"
    echo "Error: internal-link-manager.py not found"
    echo "  Expected: $SCRIPT_PATH"
    echo "  Suggestion: Run 'seokit update' to install latest scripts"
    exit 12
fi

# Step 5: Activate venv
VENV_ACTIVATE="$SEOKIT_HOME/venv/bin/activate"
source "$VENV_ACTIVATE" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[VENV_ACTIVATION_FAILED]"
    echo "Error: Failed to activate Python virtual environment"
    echo "  Path: $VENV_ACTIVATE"
    echo "  Suggestion: Delete and recreate venv with 'seokit setup --force'"
    exit 13
fi

# Step 6: Run list command
python "$SCRIPT_PATH" list
EXIT_CODE=$?

# Step 7: Handle exit codes
case $EXIT_CODE in
    0)
        echo ""
        echo "[OK] List completed"
        ;;
    3)
        echo ""
        echo "──────────────────────────────────────"
        echo "[FILE_ERROR]"
        echo ""
        echo "Cannot access the links file."
        echo ""
        echo "Common causes:"
        echo "  - .seokit-links.yaml not found"
        echo "  - Permission denied"
        echo "  - File encoding error"
        echo ""
        echo "See error details above for specifics."
        echo ""
        echo "If file is missing, run:"
        echo "  /internal-link:sync <sitemap-url>"
        echo "──────────────────────────────────────"
        ;;
    5)
        echo ""
        echo "──────────────────────────────────────"
        echo "[YAML_ERROR]"
        echo ""
        echo "The .seokit-links.yaml file has an issue."
        echo ""
        echo "Common causes:"
        echo "  - File is corrupted or malformed"
        echo "  - File is empty"
        echo "  - Invalid YAML structure"
        echo ""
        echo "Suggestion: Delete and re-sync:"
        echo "  rm .seokit-links.yaml"
        echo "  /internal-link:sync <sitemap-url>"
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

Displays a numbered list of all URL-keyword entries:

```
Found N entries:

--------------------------------------------------------------------------------
1. keyword-name
   URL: https://example.com/page-url
   Title: Page Title...

2. another-keyword
   URL: https://example.com/another-page
   Title: Another Page Title...
--------------------------------------------------------------------------------
Total: N entries
```

## Prerequisites

Run `/internal-link:sync <sitemap-url>` first to create the links file.

## Next Steps

After viewing entries, use `/internal-link <article.md>` to apply links to an article.
