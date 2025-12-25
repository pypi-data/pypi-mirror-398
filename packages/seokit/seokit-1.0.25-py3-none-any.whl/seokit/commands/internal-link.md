Apply internal links to article: $ARGUMENTS

## Error Codes Reference

| Code | Error Code | Description | Suggestion |
|------|------------|-------------|------------|
| 0 | - | Success | Links inserted into article |
| 1 | `VALIDATION_*` | Validation error | Check input parameters |
| 1 | `APPLY_ARTICLE_EMPTY` | Article file is empty | Add content to article |
| 1 | `APPLY_ARTICLE_TOO_SHORT` | Article < 50 words | Article needs more content |
| 3 | `FILE_NOT_FOUND` | Links file missing | Run `/internal-link:sync` first |
| 3 | `ARTICLE_NOT_FOUND` | Article file not found | Check file path |
| 3 | `ARTICLE_PERMISSION_DENIED` | Cannot read article | Check file permissions |
| 3 | `ARTICLE_ENCODING_ERROR` | Article not UTF-8 | Re-save as UTF-8 |
| 3 | `ARTICLE_WRITE_*` | Cannot save article | Check permissions/disk space |
| 5 | `YAML_*` | Links file corrupted | Delete and re-sync |
| 10 | `SEOKIT_NOT_INSTALLED` | SEOKit directory missing | Run `seokit setup` |
| 11 | `VENV_NOT_FOUND` | Python venv missing | Run `seokit setup` |
| 12 | `SCRIPT_NOT_FOUND` | Script missing | Run `seokit update` |
| 13 | `VENV_ACTIVATION_FAILED` | Venv activation failed | Run `seokit setup --force` |
| 130 | - | User cancelled (Ctrl+C) | Re-run when ready |

---

## Instructions

Insert internal links into the specified article based on keyword matching:

```bash
# Step 0: Validate arguments
if [ -z "$ARGUMENTS" ]; then
    echo "[USAGE_ERROR] No article path provided"
    echo ""
    echo "Usage: /internal-link <article.md>"
    echo "Example: /internal-link ./my-keyword/article.md"
    exit 1
fi

ARTICLE_PATH="$ARGUMENTS"

# Step 1: Validate file exists
if [ ! -f "$ARTICLE_PATH" ]; then
    echo "[FILE_NOT_FOUND] Article file not found: $ARTICLE_PATH"
    echo ""
    echo "Suggestion: Check the file path and ensure the file exists"
    echo "  - Use absolute or relative path"
    echo "  - Verify filename spelling"
    exit 1
fi

# Step 2: Check if file is readable
if [ ! -r "$ARTICLE_PATH" ]; then
    echo "[FILE_PERMISSION_ERROR] Cannot read article: $ARTICLE_PATH"
    echo "Suggestion: Check file read permissions with: ls -la $ARTICLE_PATH"
    exit 3
fi

# Step 3: Check if file is writable (needed for inserting links)
if [ ! -w "$ARTICLE_PATH" ]; then
    echo "[FILE_PERMISSION_ERROR] Cannot write to article: $ARTICLE_PATH"
    echo "Suggestion: Check file write permissions with: ls -la $ARTICLE_PATH"
    exit 3
fi

# Step 4: Check links file exists
if [ ! -f ".seokit-links.yaml" ]; then
    echo "[LINKS_FILE_NOT_FOUND] No links file found: .seokit-links.yaml"
    echo ""
    echo "You must run '/internal-link:sync <sitemap-url>' first to create the links file."
    echo "Example: /internal-link:sync https://example.com/sitemap.xml"
    exit 1
fi

export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"

# Step 5: Check if SEOKit is installed
if [ ! -d "$SEOKIT_HOME" ]; then
    echo "[SEOKIT_NOT_INSTALLED]"
    echo "Error: SEOKit directory not found"
    echo "  Expected: $SEOKIT_HOME"
    echo "  Suggestion: Run 'seokit setup' to install SEOKit first"
    exit 10
fi

# Step 6: Check if venv exists
if [ ! -d "$SEOKIT_HOME/venv" ]; then
    echo "[VENV_NOT_FOUND]"
    echo "Error: Python virtual environment not found"
    echo "  Expected: $SEOKIT_HOME/venv"
    echo "  Suggestion: Run 'seokit setup' to create the virtual environment"
    exit 11
fi

# Step 7: Check if script exists
SCRIPT_PATH="$SEOKIT_HOME/scripts/internal-link-manager.py"
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[SCRIPT_NOT_FOUND]"
    echo "Error: internal-link-manager.py not found"
    echo "  Expected: $SCRIPT_PATH"
    echo "  Suggestion: Run 'seokit update' to install latest scripts"
    exit 12
fi

# Step 8: Activate venv
VENV_ACTIVATE="$SEOKIT_HOME/venv/bin/activate"
source "$VENV_ACTIVATE" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[VENV_ACTIVATION_FAILED]"
    echo "Error: Failed to activate Python virtual environment"
    echo "  Path: $VENV_ACTIVATE"
    echo "  Suggestion: Delete and recreate venv with 'seokit setup --force'"
    exit 13
fi

echo "[OK] Environment validated, running link insertion..."
echo ""

# Step 9: Run the apply command
python "$SCRIPT_PATH" apply "$ARTICLE_PATH"
EXIT_CODE=$?

# Step 10: Handle exit codes with detailed messages
case $EXIT_CODE in
    0)
        echo ""
        echo "════════════════════════════════════════"
        echo "[OK] Internal links applied successfully"
        echo "════════════════════════════════════════"
        ;;
    1)
        echo ""
        echo "──────────────────────────────────────"
        echo "[VALIDATION/APPLY_ERROR]"
        echo ""
        echo "The article could not be processed."
        echo ""
        echo "Common causes:"
        echo "  - Article file is empty"
        echo "  - Article too short (< 50 words)"
        echo "  - Validation error in input"
        echo ""
        echo "See error details above for specifics."
        echo "──────────────────────────────────────"
        ;;
    3)
        echo ""
        echo "──────────────────────────────────────"
        echo "[FILE_ERROR]"
        echo ""
        echo "File operation failed."
        echo ""
        echo "Common causes:"
        echo "  - Links file (.seokit-links.yaml) not found"
        echo "  - Article file not found"
        echo "  - Permission denied (read/write)"
        echo "  - Encoding error (not UTF-8)"
        echo "  - Disk full"
        echo ""
        echo "See error details above for specifics."
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

## How It Works

The script will:
1. Load URL-keyword mappings from `.seokit-links.yaml`
2. Calculate max links allowed (2 per 1000 words)
3. Find keyword matches in article content
4. Insert links following these rules:
   - Exact keyword matching (case-insensitive)
   - Skip headings (H1-H6)
   - Skip code blocks
   - Skip already-linked text
   - Maintain minimum 150 words between links
   - Prioritize sections: body > conclusion > faq > introduction
5. Save the updated article

## Prerequisites

1. Run `/internal-link:sync <sitemap-url>` to create the links file
2. Have an article file ready (.md format)

## Example

```bash
# First, sync your sitemap
/internal-link:sync https://example.com/sitemap.xml

# View available entries
/internal-link:list

# Apply links to your article
/internal-link ./my-keyword/article.md
```

## Expected Output

```
Article: 2500 words → max 5 links allowed

  ✓ Inserted: [keyword](https://example.com/page...)
    Section: body, Position: word 342

  ✓ Inserted: [another keyword](https://example.com/...)
    Section: body, Position: word 856

✓ Saved article with 2 new links

Apply complete: 2/5 links inserted
```
