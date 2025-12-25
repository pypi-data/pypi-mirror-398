Optimize an existing article outline.

## Error Codes Reference

| Code | Description | Suggestion |
|------|-------------|------------|
| `INPUT_MISSING_KEYWORD` | No keyword-slug provided | Specify keyword: `/optimize-outline keyword-slug` |
| `INPUT_FOLDER_NOT_FOUND` | Keyword folder not found | Run `/search-intent [keyword]` first |
| `INPUT_OUTLINE_NOT_FOUND` | outline.md not found | Run `/create-outline [keyword]` first |
| `INPUT_OUTLINE_EMPTY` | Outline file is empty | Re-run `/create-outline [keyword]` |
| `CONTEXT_FILE_NOT_FOUND` | .seokit-context.md not found | Optional - run `/seokit-init` or continue |
| `ANALYZER_VENV_NOT_FOUND` | Python venv not found | Run: `seokit --reinstall` |
| `ANALYZER_SCRIPT_NOT_FOUND` | outline-analyzer.py missing | Check $SEOKIT_HOME/scripts/ |
| `ANALYZER_EXEC_ERROR` | Script execution failed | Check Python environment |
| `OUTPUT_WRITE_ERROR` | Cannot write optimized outline | Check folder write permissions |
| `DOCX_GENERATOR_NOT_FOUND` | docx-generator.py missing | Check $SEOKIT_HOME/scripts/ |
| `DOCX_EXEC_ERROR` | DOCX export failed | Check python-docx installed |

---

## Input

Specify the outline file to optimize:
- Default: Look in `./{keyword-slug}/` for most recent outline
- Or specify path: `./{keyword-slug}/outline.md`

---

## Step 0: Validate Input

**Step 0.1: Determine Keyword Slug**

```bash
# If keyword-slug provided as argument
if [ -n "$1" ]; then
  KEYWORD_SLUG="$1"
  echo "[OK] Using keyword: $KEYWORD_SLUG"
else
  # Try to auto-detect from current directory name or prompt
  echo "[INPUT_MISSING_KEYWORD] No keyword-slug provided"
  echo "Usage: /optimize-outline [keyword-slug]"
  echo "Example: /optimize-outline best-running-shoes"
  exit 1
fi
```

**Step 0.2: Check Keyword Folder**

```bash
if [ -d "./$KEYWORD_SLUG" ]; then
  echo "[OK] Keyword folder exists: ./$KEYWORD_SLUG"
else
  echo "[INPUT_FOLDER_NOT_FOUND] Folder not found: ./$KEYWORD_SLUG"
  echo "Suggestion: Run /search-intent $KEYWORD_SLUG first"
  exit 1
fi
```

**Step 0.3: Check Outline File**

```bash
OUTLINE_PATH="./$KEYWORD_SLUG/outline.md"
if [ -f "$OUTLINE_PATH" ]; then
  # Check if file is not empty
  if [ -s "$OUTLINE_PATH" ]; then
    echo "[OK] Found outline: $OUTLINE_PATH"
  else
    echo "[INPUT_OUTLINE_EMPTY] Outline file is empty: $OUTLINE_PATH"
    echo "Suggestion: Re-run /create-outline $KEYWORD_SLUG"
    exit 1
  fi
else
  echo "[INPUT_OUTLINE_NOT_FOUND] Outline not found: $OUTLINE_PATH"
  echo "Suggestion: Run /create-outline $KEYWORD_SLUG first"
  exit 1
fi
```

---

## Step 1: Load Workspace Context (Optional)

**Check for workspace context file:**

```bash
if [ -f ".seokit-context.md" ]; then
  echo "[OK] Workspace context found"
  cat ".seokit-context.md"
  CONTEXT_LOADED="yes"
else
  echo "[CONTEXT_FILE_NOT_FOUND] No workspace context at .seokit-context.md"
  echo "This is optional - continuing with standard optimization"
  CONTEXT_LOADED="no"
fi
```

**If file exists**:
- Load context for use in optimization
- Apply voice settings (author pronoun, reader address) to optimize tone
- Use products list to identify mention opportunities in sections
- Consider industry for domain-specific best practices

**If file not found**:
- Continue with standard optimization (no context applied)

---

## Step 2: Run Outline Analyzer

**Set up environment and run analyzer:**

```bash
export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"
VENV_PATH="$SEOKIT_HOME/venv/bin/activate"
ANALYZER_PATH="$SEOKIT_HOME/scripts/outline-analyzer.py"

# Check venv exists
if [ -f "$VENV_PATH" ]; then
  echo "[OK] Found Python venv"
else
  echo "[ANALYZER_VENV_NOT_FOUND] Python venv not found: $VENV_PATH"
  echo "Suggestion: Run 'seokit --reinstall' to recreate environment"
  echo "SEOKIT_HOME is: $SEOKIT_HOME"
  exit 1
fi

# Check analyzer script exists
if [ -f "$ANALYZER_PATH" ]; then
  echo "[OK] Found outline analyzer"
else
  echo "[ANALYZER_SCRIPT_NOT_FOUND] Analyzer not found: $ANALYZER_PATH"
  echo "Suggestion: Check SEOKit installation or run 'seokit --reinstall'"
  exit 1
fi

# Run analyzer
source "$VENV_PATH"
python "$ANALYZER_PATH" "$OUTLINE_PATH"
ANALYZER_EXIT=$?

if [ $ANALYZER_EXIT -ne 0 ]; then
  echo "[ANALYZER_EXEC_ERROR] Analyzer failed with exit code: $ANALYZER_EXIT"
  echo "Check the error output above for details"
  # Non-fatal for some exit codes, fatal for others
  if [ $ANALYZER_EXIT -ge 3 ]; then
    exit 1
  fi
fi
```

This will generate a report showing:
- **Score**: 0-100 optimization score
- **Structure Analysis**: H1, H2, H3 counts and validation
- **Content Distribution**: Main vs Supplemental ratio (target 80/20)
- **Issues**: Problems that need fixing
- **Recommendations**: Actionable improvement steps

---

## Step 3: Apply Optimization Rules

Based on the analyzer report from Step 2, optimize the outline following these rules:

### Structural Rules
1. **Single H1** - Contains primary keyword, matches search intent
2. **H2 Hierarchy** - 5-10 main sections, logically ordered
3. **H3 Depth** - Subdivide complex H2s with 2+ H3s each
4. **No Level Skipping** - H1 → H2 → H3 → H4 (never skip)

### Content Distribution (80/20 Rule)
- **80% Main Content**: Core topics directly answering search intent
- **20% Supplemental**: FAQ, conclusion, related topics, resources

### Flow & Coherence Rules
1. **Logical Flow** - General → Specific → Application → Summary
2. **First 10 Headings** - Must be highest quality, answer key questions
3. **Group Related** - Similar topics clustered together
4. **Bridge Sections** - Smooth transition between main and supplemental
5. **First-Last Connection** - Opening and closing themes mirror each other

### List & Structure Rules
- Use **incremental lists** for benefits, steps, or features
- Each H2 should have roughly equal weight (10-15% of content)
- Introduction and conclusion: 5-8% each

### FAQ Section Rules
Use 4 types of questions:
1. **Boolean**: "Is X better than Y?"
2. **Definitional**: "What is X?"
3. **Grouping**: "What are the types of X?"
4. **Comparative**: "How does X compare to Y?"

### Context-Aware Optimization (If context loaded from Step 0)
- **Author pronoun**: Use consistent pronoun from context in section headers and content suggestions
- **Reader address**: Match reader address in question phrasing and call-to-action sections
- **Product mentions**: Flag 2-3 sections where products/services can be naturally mentioned
- **Industry best practices**: Apply industry-specific section ordering and terminology

---

## Step 4: Generate Optimized Outline

Re-structure the outline following this format:

```markdown
# H1: [Primary Keyword + Compelling Hook]

> **Target Word Count**: [competitor avg + 20%]
> **Primary Keyword**: [main keyword]
> **Search Intent**: [informational/transactional/etc.]
> **Context Applied**: [Yes/No - from .seokit-context.md]

---

## Introduction
- Hook addressing user pain point
- Promise of value (what reader will learn)
- Credibility signal
[Target: 150-200 words, 5-8% of total]

---
## === MAIN CONTENT (80%) ===
---

## H2: [Most Important Topic - Directly Answers Query]
### H3: [Subtopic 1]
### H3: [Subtopic 2]
[Target: 300-500 words per H2]

## H2: [Second Key Topic] 🏷️
### H3: [Detail 1]
### H3: [Detail 2]
[🏷️ = Product mention opportunity - if context loaded]

## H2: [Third Key Topic]
...

[Continue with 5-8 main H2 sections]

---
## === SUPPLEMENTAL CONTENT (20%) ===
---

## H2: Frequently Asked Questions
### Q1: [Boolean question]?
### Q2: [Definitional question]?
### Q3: [Grouping question]?
### Q4: [Comparative question]?

## H2: [Related Topic / Additional Context] 🏷️
- Bridge content connecting to broader context
- Additional perspectives
[🏷️ = Product mention opportunity - if context loaded]

---

## H2: Conclusion
- Summary of key takeaways (3-5 points)
- Actionable next steps
- Call to action
[Target: 150-200 words, 5-8% of total]
```

---

## Step 5: Validation Checklist

Before finalizing, verify:
- [ ] Single H1 with primary keyword
- [ ] 5-10 H2 sections with logical flow
- [ ] 80% main content / 20% supplemental ratio
- [ ] First 10 headings are highest quality
- [ ] Related headings grouped together
- [ ] First heading and last heading connect thematically
- [ ] FAQ uses multiple question types
- [ ] Incremental lists where appropriate
- [ ] All competitor topics covered + unique angles added
- [ ] Satisfies primary search intent

---

## Step 6: Output

**Save optimized outline with error handling:**

```bash
OUTPUT_FILE="./$KEYWORD_SLUG/outline-optimized.md"
OUTPUT_DIR="./$KEYWORD_SLUG"

# Check directory is writable
if [ ! -w "$OUTPUT_DIR" ]; then
  echo "[OUTPUT_WRITE_ERROR] No write permission for: $OUTPUT_DIR"
  echo "Suggestion: Check folder permissions with: ls -la $OUTPUT_DIR"
  exit 1
fi

# Write file (Claude will generate content)
echo "[OK] Saving optimized outline to: $OUTPUT_FILE"
```

Save optimized outline to: `./{keyword-slug}/outline-optimized.md`

Display optimization summary showing:
- Before/After score comparison
- Key changes made
- Ready for `/write-seo` command

---

## Step 7: Export to DOCX (Optional)

**If user requests DOCX export:**

```bash
export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"
VENV_PATH="$SEOKIT_HOME/venv/bin/activate"
DOCX_GENERATOR="$SEOKIT_HOME/scripts/docx-generator.py"
INPUT_FILE="./$KEYWORD_SLUG/outline-optimized.md"

# Check venv exists
if [ ! -f "$VENV_PATH" ]; then
  echo "[ANALYZER_VENV_NOT_FOUND] Python venv not found: $VENV_PATH"
  echo "Suggestion: Run 'seokit --reinstall'"
  exit 1
fi

# Check docx generator exists
if [ -f "$DOCX_GENERATOR" ]; then
  echo "[OK] Found DOCX generator"
else
  echo "[DOCX_GENERATOR_NOT_FOUND] Generator not found: $DOCX_GENERATOR"
  echo "Suggestion: Check SEOKit installation"
  exit 1
fi

# Check input file exists
if [ ! -f "$INPUT_FILE" ]; then
  echo "[INPUT_OUTLINE_NOT_FOUND] Optimized outline not found: $INPUT_FILE"
  echo "Suggestion: Complete Step 6 first"
  exit 1
fi

# Run generator
source "$VENV_PATH"
python "$DOCX_GENERATOR" "$INPUT_FILE"
DOCX_EXIT=$?

if [ $DOCX_EXIT -ne 0 ]; then
  echo "[DOCX_EXEC_ERROR] DOCX generator failed with exit code: $DOCX_EXIT"
  echo "Possible causes:"
  echo "  - python-docx not installed: pip install python-docx"
  echo "  - Invalid markdown format in input file"
  exit 1
fi

echo "[OK] DOCX exported successfully"
```

---

## Next Steps

After optimization is approved:
1. Run `/write-seo` to generate the full article
2. Follow the Article Checklist during writing
