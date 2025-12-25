Create SEO article outline based on research.

## Error Codes Reference

| Code | Description | Suggestion |
|------|-------------|------------|
| `PREREQ_MISSING_FOLDER` | Keyword folder not found | Run `/search-intent [keyword]` first |
| `PREREQ_MISSING_SEARCH_INTENT` | search-intent.md not found | Run `/search-intent [keyword]` |
| `PREREQ_MISSING_TOP_ARTICLES` | top-articles.md not found | Run `/top-article [keyword]` |
| `CONTEXT_FILE_NOT_FOUND` | .seokit-context.md not found | Optional - run `/seokit-init` or continue |
| `GUIDELINES_NOT_FOUND` | Google E-E-A-T guidelines missing | Check SEOKit installation |
| `CHECKLIST_COMMON_NOT_FOUND` | Common checklist missing | Check $SEOKIT_HOME/checklists/ |
| `CHECKLIST_CUSTOM_INVALID` | Custom checklist has invalid format | Fix seokit-checklist.md syntax |
| `COMPETITOR_PARSE_ERROR` | Cannot parse top-articles.md | Re-run `/top-article [keyword]` |
| `OUTLINE_WRITE_ERROR` | Cannot write outline.md | Check folder write permissions |

---

## Prerequisites

Before running this command, ensure you have completed:
1. `/search-intent [keyword]` - Understanding user intent
2. `/top-article [keyword]` - Competitor analysis

Check `./{keyword-slug}/` folder for: `search-intent.md` and `top-articles.md`

---

## Step 0: Validate Prerequisites

**Step 0.1: Check Keyword Folder**

```bash
export KEYWORD_SLUG="[keyword-slug]"  # Replace with actual slug
if [ -d "./$KEYWORD_SLUG" ]; then
  echo "[OK] Keyword folder exists: ./$KEYWORD_SLUG"
else
  echo "[PREREQ_MISSING_FOLDER] Keyword folder not found: ./$KEYWORD_SLUG"
  echo "Suggestion: Run /search-intent $KEYWORD_SLUG first"
  exit 1
fi
```

**Step 0.2: Check Required Files**

```bash
# Check search-intent.md
if [ -f "./$KEYWORD_SLUG/search-intent.md" ]; then
  echo "[OK] Found: search-intent.md"
else
  echo "[PREREQ_MISSING_SEARCH_INTENT] Missing: ./$KEYWORD_SLUG/search-intent.md"
  echo "Suggestion: Run /search-intent $KEYWORD_SLUG"
  exit 1
fi

# Check top-articles.md
if [ -f "./$KEYWORD_SLUG/top-articles.md" ]; then
  echo "[OK] Found: top-articles.md"
else
  echo "[PREREQ_MISSING_TOP_ARTICLES] Missing: ./$KEYWORD_SLUG/top-articles.md"
  echo "Suggestion: Run /top-article $KEYWORD_SLUG"
  exit 1
fi
```

---

## Step 1: Workspace Context

**Check for workspace context file:**

```bash
if [ -f ".seokit-context.md" ]; then
  echo "[OK] Workspace context found"
  cat ".seokit-context.md"
else
  echo "[CONTEXT_FILE_NOT_FOUND] No workspace context at .seokit-context.md"
  echo "This is optional - you can:"
  echo "  1. Run /seokit-init to set up context"
  echo "  2. Continue without context (generic outline)"
fi
```

**If file exists**:
- Load context for use in outline generation
- Use industry to suggest relevant sections
- Note products for natural mention opportunities

**If file not found**:
Ask user: "Bạn có muốn khai báo thông tin workspace không?"
- **YES** → Suggest running `/seokit-init` first, then return to this command
- **NO** → Continue with generic outline (no context applied)

---

## Step 2: Mode Selection

Ask user: **Auto or Manual competitor selection?**

### Auto Mode
- Automatically select top 5 articles from `/top-article` results
- Analyze and synthesize into optimal outline

### Manual Mode
- Present numbered list of competitors found
- User selects which articles to analyze (e.g., "1, 3, 5, 7, 9")
- Minimum 3 articles recommended

---

## Step 3: Language Settings

Detect keyword language and ask user:

1. **Detected keyword language**: [Auto-detected or specify]
2. **Output language**: (default: same as keyword)
   - If keyword is English but user wants Vietnamese output, specify here

---

## Step 4: Read Reference Materials

### 4.1 Google Guidelines Integration

**IMPORTANT:** First read the complete guidelines:

```bash
GUIDELINES_PATH="docs/seo-guidelines/google-eeat-quality-guidelines.md"
if [ -f "$GUIDELINES_PATH" ]; then
  echo "[OK] Loading Google E-E-A-T guidelines"
  cat "$GUIDELINES_PATH"
else
  echo "[GUIDELINES_NOT_FOUND] Missing: $GUIDELINES_PATH"
  echo "Suggestion: Check SEOKit installation or run: seokit --reinstall"
  echo "Continuing with built-in E-E-A-T knowledge..."
fi
```

Apply these key principles from Google's Search Quality Evaluator Guidelines:

**E-E-A-T Framework:**
- **Experience**: Include sections demonstrating first-hand experience
- **Expertise**: Structure shows deep knowledge of subject
- **Authoritativeness**: Reference authoritative sources
- **Trustworthiness**: Clear, accurate, verifiable information

**Helpful Content Principles:**
- Created for humans first, not search engines
- Provides substantial value beyond what competitors offer
- Demonstrates original insights or unique perspective
- Satisfies user need completely

### 4.2 Load Checklists

**Step A: Load Common Outline Checklist**

```bash
export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"
CHECKLIST_PATH="$SEOKIT_HOME/checklists/outline-checklist.md"

if [ -f "$CHECKLIST_PATH" ]; then
  echo "[OK] Loading common outline checklist"
  cat "$CHECKLIST_PATH"
else
  echo "[CHECKLIST_COMMON_NOT_FOUND] Missing: $CHECKLIST_PATH"
  echo "Suggestion: Check SEOKIT_HOME env var or reinstall SEOKit"
  echo "SEOKIT_HOME is currently: $SEOKIT_HOME"
  # Non-fatal - continue with built-in rules
fi
```

**Step B: Load Custom Checklist (if exists)**

```bash
CUSTOM_CHECKLIST="./seokit-checklist.md"
if [ -f "$CUSTOM_CHECKLIST" ]; then
  echo "[OK] Loading custom checklist"
  # Validate basic structure
  if grep -q "^## " "$CUSTOM_CHECKLIST"; then
    cat "$CUSTOM_CHECKLIST"
  else
    echo "[CHECKLIST_CUSTOM_INVALID] Custom checklist missing ## headers"
    echo "Expected sections: ## Shared Rules, ## Outline Overrides"
    echo "File: $CUSTOM_CHECKLIST"
  fi
else
  echo "[INFO] No custom checklist at $CUSTOM_CHECKLIST (optional)"
fi
```

**Application Rules:**
1. Apply ALL rules from common checklist
2. If custom exists, apply:
   - `## Shared Rules` section
   - `## Outline Overrides` section
3. Custom rules CAN override common rules (e.g., stricter limits)

---

## Step 5: Competitor Analysis

**Load and parse top-articles.md:**

```bash
TOP_ARTICLES="./$KEYWORD_SLUG/top-articles.md"
if [ -f "$TOP_ARTICLES" ]; then
  # Check if file has expected structure
  if grep -q "^## " "$TOP_ARTICLES"; then
    echo "[OK] Parsing competitor data from: $TOP_ARTICLES"
  else
    echo "[COMPETITOR_PARSE_ERROR] Invalid format in: $TOP_ARTICLES"
    echo "Expected: ## headers for each competitor article"
    echo "Suggestion: Re-run /top-article $KEYWORD_SLUG"
  fi
else
  echo "[PREREQ_MISSING_TOP_ARTICLES] File not found: $TOP_ARTICLES"
  exit 1
fi
```

For selected articles, analyze and extract:

1. **Common Topics** (must include):
   - H2 headings that appear in 3+ articles
   - Core subtopics users expect

2. **Unique Topics** (differentiation):
   - Valuable content only 1-2 articles have
   - Your opportunity to stand out

3. **Content Gaps** (opportunities):
   - Questions not fully answered
   - Missing perspectives or data
   - Outdated information to refresh

4. **Structural Patterns**:
   - Average word count per section
   - FAQ patterns and questions
   - Media usage (images, tables, videos)

---

## Step 6: Generate Outline

**If workspace context loaded (Step 1)**:
- Include industry-relevant sections based on context
- Plan natural product/service mention opportunities
- Use author pronoun and reader address from context

Create outline following this structure:

```markdown
# H1: [Main Title - Matches Primary Search Intent]

> Target word count: [based on competitor average + 20%]
> Primary keyword: [keyword]
> Secondary keywords: [from research]

## Introduction
- Hook addressing user pain point
- What reader will learn
- Why this content is authoritative
[~150-200 words]

---
## MAIN CONTENT (80% of article)
---

## H2: [Core Topic 1 - Most Important]
### H3: [Subtopic if needed]
### H3: [Subtopic if needed]
[Estimated words: XXX]

## H2: [Core Topic 2]
### H3: [Subtopic]
[Estimated words: XXX]

## H2: [Core Topic 3]
...

## H2: [Core Topic N]

---
## SUPPLEMENTAL CONTENT (20% of article)
---

## H2: Frequently Asked Questions
### Q1: [Boolean question]?
### Q2: [Definitional question]?
### Q3: [Grouping question]?
### Q4: [Comparative question]?

## H2: [Related Topic / Additional Context]
- Expand on related information
- Provide additional perspectives

---

## H2: Conclusion
- Summary of key points
- Actionable next steps
- Call to action
[~150-200 words]
```

---

## Step 7: Apply Outline Rules

Verify outline follows these rules:
- [ ] Single H1 only
- [ ] H2s are sub-headings of H1
- [ ] H3s are sub-headings of H2s
- [ ] Logical contextual flow throughout
- [ ] Main content (80%) fully addresses primary topic
- [ ] Supplemental content (20%) enhances without diluting
- [ ] First 10 headings are highest quality
- [ ] Related headings grouped together
- [ ] First and last headings connect/mirror each other
- [ ] FAQ uses 4 question types if possible
- [ ] Incremental lists where appropriate

---

## Step 8: Output

**Save outline with error handling:**

```bash
OUTPUT_FILE="./$KEYWORD_SLUG/outline.md"
OUTPUT_DIR="./$KEYWORD_SLUG"

# Check directory exists and is writable
if [ ! -d "$OUTPUT_DIR" ]; then
  echo "[OUTLINE_WRITE_ERROR] Directory not found: $OUTPUT_DIR"
  echo "Suggestion: Run /search-intent $KEYWORD_SLUG first"
  exit 1
fi

if [ ! -w "$OUTPUT_DIR" ]; then
  echo "[OUTLINE_WRITE_ERROR] No write permission for: $OUTPUT_DIR"
  echo "Suggestion: Check folder permissions with: ls -la $OUTPUT_DIR"
  exit 1
fi

# Write outline (Claude will generate content)
echo "[OK] Saving outline to: $OUTPUT_FILE"
```

Save outline to: `./{keyword-slug}/outline.md`

Present outline to user for review before proceeding to `/optimize-outline`.

---

## Next Steps

After user reviews outline:
1. Run `/optimize-outline` to refine and finalize
2. Export to DOCX for external review if needed
