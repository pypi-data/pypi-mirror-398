Initialize SEOKit workspace context for your project.

Collects business context via interactive questionnaire and saves to `.seokit-context.md`. This context is automatically used by `/create-outline`, `/optimize-outline`, and `/write-seo` commands.

## Error Codes Reference

| Code | Description | Suggestion |
|------|-------------|------------|
| `CWD_NOT_WRITABLE` | Current directory not writable | Check folder permissions |
| `CONTEXT_READ_ERROR` | Cannot read existing .seokit-context.md | Check file permissions |
| `CONTEXT_PARSE_ERROR` | Existing context has invalid format | Delete and recreate with /seokit-init |
| `CONTEXT_WRITE_ERROR` | Cannot write .seokit-context.md | Check folder write permissions |
| `INPUT_VALIDATION_URL` | Invalid URL format | Use format: https://example.com |
| `INPUT_EMPTY_REQUIRED` | Required field left empty | Provide a value for this field |
| `USER_CANCELLED` | User cancelled the operation | Run /seokit-init again when ready |

---

## Step 0: Validate Environment

**Check current directory is writable:**

```bash
CWD="$(pwd)"
if [ -w "$CWD" ]; then
  echo "[OK] Current directory is writable: $CWD"
else
  echo "[CWD_NOT_WRITABLE] Cannot write to current directory: $CWD"
  echo "Suggestion: Check folder permissions or change to a writable directory"
  exit 1
fi
```

---

## Step 1: Detect Existing Context

**Check if `.seokit-context.md` exists:**

```bash
CONTEXT_FILE=".seokit-context.md"

if [ -f "$CONTEXT_FILE" ]; then
  echo "[INFO] Found existing context file: $CONTEXT_FILE"

  # Check if readable
  if [ -r "$CONTEXT_FILE" ]; then
    echo "[OK] Context file is readable"

    # Validate basic structure
    if grep -q "^## Website Info" "$CONTEXT_FILE" && grep -q "^## Voice" "$CONTEXT_FILE"; then
      echo "[OK] Context file has valid structure"
      CONTEXT_EXISTS="valid"
    else
      echo "[CONTEXT_PARSE_ERROR] Context file has invalid format"
      echo "Expected sections: ## Website Info, ## Voice & Tone"
      echo "Suggestion: Delete file and re-run /seokit-init, or fix manually"
      CONTEXT_EXISTS="invalid"
    fi
  else
    echo "[CONTEXT_READ_ERROR] Cannot read context file: $CONTEXT_FILE"
    echo "Suggestion: Check file permissions with: ls -la $CONTEXT_FILE"
    exit 1
  fi
else
  echo "[INFO] No existing context file found"
  CONTEXT_EXISTS="none"
fi
```

### If EXISTS (valid):
Ask user: **"Đã tìm thấy file `.seokit-context.md`. Bạn muốn cập nhật nó? [Y/n]"**

- **Y (default)**: Continue to questionnaire, pre-fill answers from existing file
- **n**: Exit with message "Đã giữ nguyên context hiện tại."

```bash
# If user chooses 'n'
echo "[USER_CANCELLED] User chose to keep existing context"
echo "Current context preserved at: $CONTEXT_FILE"
exit 0
```

### If EXISTS (invalid):
Ask user: **"File context hiện tại bị lỗi. Bạn muốn tạo mới? [Y/n]"**

- **Y (default)**: Continue to questionnaire (start fresh)
- **n**: Exit with error

### If NOT_FOUND:
Continue to Step 2 (Questionnaire).

---

## Step 2: Interactive Questionnaire

Ask user the following 8 questions in Vietnamese. Collect answers one by one.

**Input Validation Rules:**
- Required fields must not be empty
- URL should be validated for basic format
- Show `[INPUT_EMPTY_REQUIRED]` for empty required fields
- Show `[INPUT_VALIDATION_URL]` for invalid URLs

### Q1: Loại website (Required)
**Question**: "Loại website của bạn?"
**Options**:
- `personal_blog` - Blog cá nhân
- `business_website` - Website doanh nghiệp (default)
- `e_commerce` - Thương mại điện tử
- `news` - Tin tức
- `other` - Khác

```bash
# Validate selection
if [ -z "$WEBSITE_TYPE" ]; then
  echo "[INPUT_EMPTY_REQUIRED] Website type is required"
  echo "Please select one of the options above"
fi
```

### Q2: URL website (Optional but validated)
**Question**: "URL website của bạn? (VD: https://example.com)"
**Type**: Text input
**Validation**: Basic URL format check

```bash
# Validate URL format if provided
if [ -n "$WEBSITE_URL" ]; then
  if echo "$WEBSITE_URL" | grep -qE "^https?://[a-zA-Z0-9]"; then
    echo "[OK] Valid URL format"
  else
    echo "[INPUT_VALIDATION_URL] Invalid URL format: $WEBSITE_URL"
    echo "Expected format: https://example.com or http://example.com"
    echo "Leave empty to skip, or provide a valid URL"
  fi
fi
```

### Q3: Xưng hô tác giả (Required)
**Question**: "Bạn xưng gì khi viết bài?"
**Options**:
- `mình` - Mình (thân mật)
- `tôi` - Tôi (trang trọng cá nhân)
- `chúng tôi` - Chúng tôi (đại diện công ty) (default)
- `[custom]` - Khác (cho phép nhập tùy chọn)

### Q4: Gọi độc giả (Required)
**Question**: "Gọi độc giả là gì?"
**Options**:
- `bạn` - Bạn (thân thiện) (default)
- `anh/chị` - Anh/chị (lịch sự)
- `quý khách` - Quý khách (trang trọng)
- `[custom]` - Khác (cho phép nhập tùy chọn)

### Q5: Lĩnh vực (Required)
**Question**: "Website thuộc lĩnh vực nào?"
**Options**:
- `tech` - Công nghệ
- `health` - Sức khỏe
- `finance` - Tài chính
- `education` - Giáo dục
- `lifestyle` - Phong cách sống
- `food` - Ẩm thực
- `travel` - Du lịch
- `fashion` - Thời trang
- `real_estate` - Bất động sản
- `other` - Khác

### Q6: Sản phẩm/Dịch vụ (Optional)
**Question**: "Liệt kê các sản phẩm/dịch vụ muốn nhắc đến trong bài viết (mỗi dòng một sản phẩm):"
**Type**: Multi-line text input
**Format**: Accept multiple lines, each line is one product/service

```bash
echo "[INFO] Products/services list (optional - press Enter twice to skip)"
```

### Q7: Thông tin bổ sung (Optional)
**Question**: "Thông tin bổ sung về doanh nghiệp? (VD: thành lập năm nào, USP...)"
**Type**: Text input
**Default**: Empty (skip if user presses Enter)

### Q8: Lưu ý viết bài (Optional)
**Question**: "Lưu ý khi viết bài? (VD: tránh từ ngữ nào, phong cách...)"
**Type**: Text input
**Default**: Empty (skip if user presses Enter)

---

## Step 3: Generate Context File

**Validate all required fields before writing:**

```bash
# Final validation before write
VALIDATION_ERRORS=0

if [ -z "$WEBSITE_TYPE" ]; then
  echo "[INPUT_EMPTY_REQUIRED] Missing: Website type (Q1)"
  VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$AUTHOR_PRONOUN" ]; then
  echo "[INPUT_EMPTY_REQUIRED] Missing: Author pronoun (Q3)"
  VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$READER_ADDRESS" ]; then
  echo "[INPUT_EMPTY_REQUIRED] Missing: Reader address (Q4)"
  VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ -z "$INDUSTRY" ]; then
  echo "[INPUT_EMPTY_REQUIRED] Missing: Industry (Q5)"
  VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
fi

if [ $VALIDATION_ERRORS -gt 0 ]; then
  echo "[ERROR] $VALIDATION_ERRORS required field(s) missing"
  echo "Please provide values for all required fields"
  exit 1
fi

echo "[OK] All required fields validated"
```

**Write context file with error handling:**

```bash
CONTEXT_FILE=".seokit-context.md"

# Attempt to write file
cat > "$CONTEXT_FILE" << 'CONTEXT_EOF'
# SEOKit Workspace Context

## Website Info
- **Type**: [Q1 answer]
- **URL**: [Q2 answer]
- **Industry**: [Q5 answer]

## Voice & Tone
- **Author pronoun**: [Q3 answer]
- **Reader address**: [Q4 answer]

## Products/Services
[Q6 answers - each on new line with bullet point]
- Product 1
- Product 2
- ...

## Writing Notes
[Q8 answer or "Không có" if empty]

## Additional Info
[Q7 answer or "Không có" if empty]
CONTEXT_EOF

# Check if write succeeded
if [ $? -eq 0 ] && [ -f "$CONTEXT_FILE" ]; then
  echo "[OK] Context file created: $CONTEXT_FILE"
else
  echo "[CONTEXT_WRITE_ERROR] Failed to create context file: $CONTEXT_FILE"
  echo "Possible causes:"
  echo "  - Disk full"
  echo "  - Permission denied"
  echo "  - Directory doesn't exist"
  echo "Suggestion: Check available disk space and folder permissions"
  exit 1
fi

# Verify file is readable
if [ -r "$CONTEXT_FILE" ]; then
  echo "[OK] Context file is readable"
else
  echo "[CONTEXT_READ_ERROR] Created file but cannot read it: $CONTEXT_FILE"
  echo "Suggestion: Check file permissions"
  exit 1
fi
```

---

## Step 4: Confirmation

After generating file:

**Display success message with validation:**

```bash
# Verify file exists and show content
if [ -f "$CONTEXT_FILE" ] && [ -s "$CONTEXT_FILE" ]; then
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "[OK] Đã tạo file .seokit-context.md thành công!"
  echo "════════════════════════════════════════════════════════"
  echo ""
  echo "Generated content:"
  echo "──────────────────────────────────────────────────────────"
  cat "$CONTEXT_FILE"
  echo "──────────────────────────────────────────────────────────"
  echo ""
  echo "[INFO] Context này sẽ được sử dụng tự động bởi các lệnh:"
  echo "  - /create-outline"
  echo "  - /optimize-outline"
  echo "  - /write-seo"
else
  echo "[CONTEXT_WRITE_ERROR] File was not created properly"
  echo "File path: $CONTEXT_FILE"
  echo "Suggestion: Re-run /seokit-init"
  exit 1
fi
```

1. Display the generated content to user
2. Show message: **"Đã tạo file `.seokit-context.md` thành công!"**
3. Explain: "Context này sẽ được sử dụng tự động bởi các lệnh `/create-outline`, `/optimize-outline`, và `/write-seo`."

---

## Usage Notes

- Run this command once per project/workspace
- Context file can be edited manually if needed
- Re-run `/seokit-init` anytime to update context
- Other SEO commands will auto-detect and load this context

---

## Next Steps

After initialization:
1. Run `/search-intent [keyword]` to start SEO research
2. Or run existing SEO workflow if research already done
