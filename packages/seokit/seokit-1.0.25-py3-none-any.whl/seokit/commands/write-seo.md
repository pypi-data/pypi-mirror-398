Write SEO article from optimized outline.

## Error Codes Reference

| Code | Description | Suggestion |
|------|-------------|------------|
| `INPUT_MISSING_KEYWORD` | No keyword-slug provided | Specify keyword: `/write-seo keyword-slug` |
| `INPUT_FOLDER_NOT_FOUND` | Keyword folder not found | Run `/search-intent [keyword]` first |
| `INPUT_OUTLINE_NOT_FOUND` | outline-optimized.md not found | Run `/optimize-outline [keyword]` first |
| `INPUT_OUTLINE_EMPTY` | Outline file is empty | Re-run `/optimize-outline [keyword]` |
| `CONTEXT_FILE_NOT_FOUND` | .seokit-context.md not found | Optional - run `/seokit-init` or continue |
| `GUIDELINES_NOT_FOUND` | Google E-E-A-T guidelines missing | Check SEOKit installation |
| `CHECKLIST_COMMON_NOT_FOUND` | Article checklist missing | Check $SEOKIT_HOME/checklists/ |
| `CHECKLIST_CUSTOM_INVALID` | Custom checklist has invalid format | Fix seokit-checklist.md syntax |
| `VENV_NOT_FOUND` | Python venv not found | Run: `seokit --reinstall` |
| `DOCX_GENERATOR_NOT_FOUND` | docx-generator.py missing | Check $SEOKIT_HOME/scripts/ |
| `DOCX_EXEC_ERROR` | DOCX export failed | Check python-docx installed |
| `OUTPUT_WRITE_ERROR` | Cannot write article.md | Check folder write permissions |

---

## Prerequisites

Ensure you have:
1. Optimized outline at: `./{keyword-slug}/outline-optimized.md`
2. Article checklist at: `$SEOKIT_HOME/checklists/article-checklist.md`

---

## Step 0: Validate Input

**Step 0.1: Determine Keyword Slug**

```bash
# If keyword-slug provided as argument
if [ -n "$1" ]; then
  KEYWORD_SLUG="$1"
  echo "[OK] Using keyword: $KEYWORD_SLUG"
else
  echo "[INPUT_MISSING_KEYWORD] No keyword-slug provided"
  echo "Usage: /write-seo [keyword-slug]"
  echo "Example: /write-seo best-running-shoes"
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

**Step 0.3: Check Optimized Outline**

```bash
OUTLINE_PATH="./$KEYWORD_SLUG/outline-optimized.md"

# Try optimized first, fall back to regular outline
if [ -f "$OUTLINE_PATH" ]; then
  if [ -s "$OUTLINE_PATH" ]; then
    echo "[OK] Found optimized outline: $OUTLINE_PATH"
  else
    echo "[INPUT_OUTLINE_EMPTY] Outline file is empty: $OUTLINE_PATH"
    echo "Suggestion: Re-run /optimize-outline $KEYWORD_SLUG"
    exit 1
  fi
else
  # Check for regular outline as fallback
  FALLBACK_PATH="./$KEYWORD_SLUG/outline.md"
  if [ -f "$FALLBACK_PATH" ]; then
    echo "[WARN] Optimized outline not found, using: $FALLBACK_PATH"
    echo "Recommendation: Run /optimize-outline $KEYWORD_SLUG for better results"
    OUTLINE_PATH="$FALLBACK_PATH"
  else
    echo "[INPUT_OUTLINE_NOT_FOUND] No outline found in: ./$KEYWORD_SLUG/"
    echo "Tried: outline-optimized.md, outline.md"
    echo "Suggestion: Run /create-outline $KEYWORD_SLUG first"
    exit 1
  fi
fi
```

---

## Step 1: Load Workspace Context

**Check for workspace context file:**

```bash
if [ -f ".seokit-context.md" ]; then
  echo "[OK] Workspace context found"
  cat ".seokit-context.md"
  CONTEXT_LOADED="yes"
else
  echo "[CONTEXT_FILE_NOT_FOUND] No workspace context at .seokit-context.md"
  echo "This is optional - continuing with standard writing"
  CONTEXT_LOADED="no"
fi
```

**If file exists**:
- Load context for use throughout article writing
- **Author pronoun**: Use consistently (e.g., "Chúng tôi..." vs "Mình...")
- **Reader address**: Use consistently (e.g., "Bạn có thể..." vs "Anh/chị...")
- **Products**: Note for natural mention in relevant sections (1-2 mentions max)
- **Writing notes**: Apply as style constraints throughout

**If file not found**:
- Continue with standard writing (no context applied)

---

## Step 2: Pre-Writing Setup

### 2.1 Load Google SEO Guidelines

**IMPORTANT:** Read the complete E-E-A-T guidelines first:

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

### 2.2 Load Outline

Read the optimized outline file and extract:
- Target word count
- Primary keyword
- Section structure (H2s, H3s)
- Content notes per section

```bash
echo "[OK] Reading outline from: $OUTLINE_PATH"
cat "$OUTLINE_PATH"
```

### 2.3 Load Checklists

**Step A: Load Common Article Checklist**

```bash
export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"
CHECKLIST_PATH="$SEOKIT_HOME/checklists/article-checklist.md"

if [ -f "$CHECKLIST_PATH" ]; then
  echo "[OK] Loading article checklist"
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
    echo "Expected sections: ## Shared Rules, ## Article Overrides"
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
   - `## Article Overrides` section
3. Custom rules CAN override common rules (e.g., stricter limits)

### 2.4 Confirm Settings

Ask user (pre-fill from context if available):
1. **Output language**: [From context or auto-detect from outline]
2. **Target word count**: [Use outline suggestion or specify]
3. **Tone**: [Suggest based on website type from context]
4. **Author pronoun**: [From context: {author_pronoun} or ask]
5. **Reader address**: [From context: {reader_address} or ask]
6. **Brand voice notes**: [From context: writing_notes or ask]

---

## Step 3: Section-by-Section Writing

Write each section following outline structure:

**Context Application (if loaded from Step 1):**
- Use **author pronoun** consistently throughout (e.g., "Chúng tôi giới thiệu..." not mixing with "Mình...")
- Use **reader address** consistently (e.g., "Bạn có thể..." not mixing with "Anh/chị...")
- Apply **writing notes** as style constraints
- Look for 1-2 natural opportunities to mention **products** (don't force)

### Introduction (5-8% of total)
- **Hook**: Open with compelling statement, question, or statistic
- **Context**: Briefly introduce the topic and why it matters
- **Promise**: What reader will learn/gain from this article
- **Keyword**: Include primary keyword naturally in first 100 words
- **Voice**: Use author pronoun in self-reference (if context loaded)

**Target**: 150-200 words

### Main Content Sections (H2s)

For each H2 section in outline:

1. **Topic Sentence**: Clear statement of what this section covers
2. **Body Content**:
   - Provide depth based on outline notes
   - Include specific examples and data
   - Use bullet points for lists (3+ items)
   - Add tables for comparisons
   - Reference sources where applicable
   - **Product mention** (if context loaded): Find natural opportunity in 1-2 relevant sections
3. **Subsections (H3s)**: Write as marked in outline
4. **Transition**: Smooth connection to next section

**Target per H2**: 300-500 words (adjust based on total target)

### FAQ Section

For each question:
- **Direct answer** in first sentence
- **Supporting detail** (1-2 sentences)
- **Actionable takeaway** if applicable

**Target per Q&A**: 50-100 words

Format for schema markup:
```markdown
### Q: [Question text]?

[Direct answer followed by supporting details.]
```

### Conclusion (5-8% of total)

1. **Summary**: Recap 3-5 key takeaways
2. **Reinforcement**: Restate primary keyword and main value
3. **Call to Action**: Clear next step for reader (use reader address if context loaded)
4. **Closing hook**: Connect back to opening theme

**Target**: 150-200 words

---

## Step 4: Quality Checklist Verification

After writing, verify:

### Content Quality
- [ ] Original, non-plagiarized content
- [ ] Accurate, fact-checked information
- [ ] Clear, concise writing style
- [ ] Active voice preferred
- [ ] Short paragraphs (3-4 sentences max)

### SEO Elements
- [ ] Primary keyword in first 100 words
- [ ] Primary keyword in at least one H2
- [ ] Natural keyword distribution (1-2% density)
- [ ] LSI keywords included naturally

### E-E-A-T Signals
- [ ] First-hand experience mentioned where relevant
- [ ] Expert perspective demonstrated
- [ ] Data and statistics cited
- [ ] Sources referenced

### Structure
- [ ] Hook in first paragraph
- [ ] Smooth transitions between sections
- [ ] Bullet points for lists
- [ ] Strong conclusion with CTA

### Context Compliance (if .seokit-context.md loaded)
- [ ] Author pronoun used consistently throughout
- [ ] Reader address used consistently throughout
- [ ] Products mentioned naturally (1-2 times, not forced)
- [ ] Writing notes applied as constraints

---

## Step 5: Generate Outputs

### 5.1 Save Markdown

**Save article with error handling:**

```bash
OUTPUT_FILE="./$KEYWORD_SLUG/article.md"
OUTPUT_DIR="./$KEYWORD_SLUG"

# Check directory is writable
if [ ! -w "$OUTPUT_DIR" ]; then
  echo "[OUTPUT_WRITE_ERROR] No write permission for: $OUTPUT_DIR"
  echo "Suggestion: Check folder permissions with: ls -la $OUTPUT_DIR"
  exit 1
fi

# Write file (Claude will generate content)
echo "[OK] Saving article to: $OUTPUT_FILE"
```

Save article to: `./{keyword-slug}/article.md`

### 5.2 Generate DOCX

**Export to DOCX with error handling:**

```bash
export SEOKIT_HOME="${SEOKIT_HOME:-$HOME/.claude/seokit}"
VENV_PATH="$SEOKIT_HOME/venv/bin/activate"
DOCX_GENERATOR="$SEOKIT_HOME/scripts/docx-generator.py"
INPUT_FILE="./$KEYWORD_SLUG/article.md"

# Check venv exists
if [ ! -f "$VENV_PATH" ]; then
  echo "[VENV_NOT_FOUND] Python venv not found: $VENV_PATH"
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
  echo "[OUTPUT_WRITE_ERROR] Article not found: $INPUT_FILE"
  echo "Suggestion: Complete Step 5.1 first"
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

echo "[OK] DOCX exported to: ./$KEYWORD_SLUG/article.docx"
```

### 5.3 Generate Statistics

Analyze the article:
- Word count
- Keyword density
- Readability score
- Section breakdown

---

## Step 6: Final Report

Present completion summary:

```markdown
## Article Generation Complete

### Article Details
- **Title**: [H1 Title]
- **Primary Keyword**: [keyword]
- **Word Count**: X words
- **Target**: Y words
- **Sections**: X H2s, Y H3s

### SEO Metrics
- **Keyword Density**: X.X%
- **Primary Keyword in First 100 Words**: ✓/✗
- **Readability Score**: X/100 (Grade Level)

### Output Files
- **Markdown**: `./{keyword-slug}/article.md`
- **DOCX**: `./{keyword-slug}/article.docx`

### Checklist Compliance
- Content Quality: X/Y items ✓
- SEO Elements: X/Y items ✓
- E-E-A-T Signals: X/Y items ✓
- Structure: X/Y items ✓
- Context Compliance: X/Y items ✓ (if context loaded)

### Suggested Next Steps
1. Add featured image (suggested: [topic-related image])
2. Insert in-content images at: [specific locations]
3. Review and personalize examples for your audience
4. Add internal links to related pages
5. Create meta description (150-160 characters)
6. Prepare alt text for images
```

---

## Meta Description Generator

Generate a compelling meta description:
- Include primary keyword
- 150-160 characters
- Include value proposition
- End with subtle CTA or hook

Example format:
```
[Primary benefit] + [Secondary value] + [Keyword] + [CTA/hook]. [150-160 chars]
```

---

## Optional: Export for Review

If user needs to share for review:
1. DOCX file is ready for Google Docs / Word review
2. Consider adding comments in document for reviewer notes
3. Highlight areas needing SME (Subject Matter Expert) input
