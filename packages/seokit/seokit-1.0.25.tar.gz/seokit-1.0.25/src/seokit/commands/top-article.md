Find top 10 articles for keyword: $ARGUMENTS

## Instructions

Run the top articles finder using Perplexity API:

```bash
# Validate arguments
if [ -z "$ARGUMENTS" ]; then
    echo "Error: No keyword provided. Usage: /top-article <keyword>"
    exit 1
fi

KEYWORD_SLUG=$(echo "$ARGUMENTS" | iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null || echo "$ARGUMENTS" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
if [ -z "$KEYWORD_SLUG" ]; then
    KEYWORD_SLUG=$(echo "$ARGUMENTS" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
fi

export SEOKIT_HOME="$HOME/.claude/seokit"
export SEOKIT_KEYWORD="$KEYWORD_SLUG"

# Check if venv exists
if [ ! -d "$SEOKIT_HOME/venv" ]; then
    echo "Error: SEOKit not properly installed. Run 'seokit setup' first."
    exit 1
fi

source "$SEOKIT_HOME/venv/bin/activate"
python "$SEOKIT_HOME/scripts/top-articles-finder.py" "$ARGUMENTS"
```

## Expected Output

For each of the top 10 articles:
- **Title and URL**
- **Estimated Word Count**
- **Content Type** (guide, listicle, comparison, etc.)
- **Main Topics/H2 Headings**
- **Unique Value** - What makes it rank well
- **E-E-A-T Signals** - Expertise and authority indicators
- **Content Gaps** - Areas for improvement

Plus a **Summary Analysis** with:
- Common topics across top articles
- Content gaps (opportunities)
- Average word count
- Recommended approach to outperform

Results are saved to: `./{keyword-slug}/top-articles.md`

## Next Steps
After finding top articles, run `/create-outline` to create an optimized content outline.
