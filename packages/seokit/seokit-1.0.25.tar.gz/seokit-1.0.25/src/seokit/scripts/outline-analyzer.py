"""
Outline Analyzer
Analyzes and validates SEO article outlines against optimization rules.

Exit codes:
    0: Success
    1: Usage error (no file provided)
    2: File not found
    3: File read error
    4: Unexpected error
"""
import re
import sys
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUTS_DIR


def analyze_outline(content: str) -> dict:
    """
    Analyze outline structure and return metrics.

    Args:
        content: Markdown outline content

    Returns:
        dict with analysis metrics
    """
    lines = content.split('\n')

    # Count heading levels
    h1_lines = [l for l in lines if re.match(r'^# [^#]', l)]
    h2_lines = [l for l in lines if re.match(r'^## [^#]', l)]
    h3_lines = [l for l in lines if re.match(r'^### [^#]', l)]
    h4_lines = [l for l in lines if re.match(r'^#### [^#]', l)]

    # Extract H1 for keyword analysis
    h1_text = h1_lines[0] if h1_lines else ""

    # Classify H2s as main vs supplemental
    supplemental_keywords = [
        'faq', 'frequently asked', 'conclusion', 'summary',
        'about', 'author', 'related', 'resources', 'additional',
        'further reading', 'next steps', 'final thoughts'
    ]

    main_h2s = []
    supplemental_h2s = []

    for h2 in h2_lines:
        h2_lower = h2.lower()
        if any(kw in h2_lower for kw in supplemental_keywords):
            supplemental_h2s.append(h2)
        else:
            main_h2s.append(h2)

    total_h2 = len(h2_lines)
    main_ratio = (len(main_h2s) / total_h2 * 100) if total_h2 > 0 else 0
    supplemental_ratio = 100 - main_ratio

    # Check for hierarchy issues
    issues = []

    if len(h1_lines) == 0:
        issues.append("Missing H1 - Add a main title")
    elif len(h1_lines) > 1:
        issues.append(f"Multiple H1s found ({len(h1_lines)}) - Keep only one main title")

    if total_h2 < 5:
        issues.append(f"Too few H2 sections ({total_h2}) - Recommend 5-10 for depth")
    elif total_h2 > 12:
        issues.append(f"Too many H2 sections ({total_h2}) - Consider consolidating")

    if main_ratio < 75:
        issues.append(f"Main content too low ({main_ratio:.0f}%) - Target 80%")
    elif main_ratio > 90:
        issues.append(f"Supplemental content too low ({100-main_ratio:.0f}%) - Add FAQ or related content")

    # Check for orphan H3s (H3 without parent H2)
    h3_without_content = len(h3_lines) > 0 and len(h2_lines) == 0
    if h3_without_content:
        issues.append("H3 sections without H2 parents - Fix heading hierarchy")

    return {
        "h1_count": len(h1_lines),
        "h1_text": h1_text,
        "h2_count": total_h2,
        "h3_count": len(h3_lines),
        "h4_count": len(h4_lines),
        "main_h2s": main_h2s,
        "supplemental_h2s": supplemental_h2s,
        "main_ratio": main_ratio,
        "supplemental_ratio": supplemental_ratio,
        "issues": issues,
        "total_lines": len(lines)
    }


def generate_recommendations(analysis: dict) -> list:
    """
    Generate actionable recommendations based on analysis.

    Args:
        analysis: Analysis dict from analyze_outline

    Returns:
        list of recommendation strings
    """
    recs = []

    # H1 issues
    if analysis["h1_count"] != 1:
        recs.append({
            "priority": "HIGH",
            "issue": f"H1 count is {analysis['h1_count']}",
            "fix": "Ensure exactly one H1 title containing primary keyword"
        })

    # H2 count issues
    if analysis["h2_count"] < 5:
        recs.append({
            "priority": "MEDIUM",
            "issue": f"Only {analysis['h2_count']} H2 sections",
            "fix": "Add more main sections to improve content depth (aim for 5-10)"
        })
    elif analysis["h2_count"] > 12:
        recs.append({
            "priority": "MEDIUM",
            "issue": f"Too many H2 sections ({analysis['h2_count']})",
            "fix": "Consolidate similar sections or demote some to H3"
        })

    # Content distribution
    if analysis["main_ratio"] < 75:
        recs.append({
            "priority": "HIGH",
            "issue": f"Main content is only {analysis['main_ratio']:.0f}%",
            "fix": "Move supplemental content to end, add more core topic sections"
        })
    elif analysis["main_ratio"] > 90:
        recs.append({
            "priority": "LOW",
            "issue": f"Supplemental content is only {analysis['supplemental_ratio']:.0f}%",
            "fix": "Add FAQ section or related topics for comprehensive coverage"
        })

    # Add general recommendations
    if analysis["h3_count"] == 0 and analysis["h2_count"] > 3:
        recs.append({
            "priority": "LOW",
            "issue": "No H3 subsections found",
            "fix": "Consider adding H3s to break down complex H2 sections"
        })

    return recs


def calculate_score(analysis: dict) -> int:
    """
    Calculate optimization score out of 100.

    Args:
        analysis: Analysis dict

    Returns:
        Score 0-100
    """
    score = 100

    # H1 check (-20 if wrong)
    if analysis["h1_count"] != 1:
        score -= 20

    # H2 count check (-10 if outside range)
    if analysis["h2_count"] < 5 or analysis["h2_count"] > 12:
        score -= 10

    # Content distribution check (-15 if outside 75-90%)
    if analysis["main_ratio"] < 75 or analysis["main_ratio"] > 90:
        score -= 15

    # H3 depth check (-5 if no H3s on complex outline)
    if analysis["h3_count"] == 0 and analysis["h2_count"] > 5:
        score -= 5

    # Issue penalty
    score -= len(analysis["issues"]) * 3

    return max(0, min(100, score))


def generate_report(content: str) -> str:
    """
    Generate full optimization report for an outline.

    Args:
        content: Markdown outline content

    Returns:
        Formatted report string
    """
    analysis = analyze_outline(content)
    recommendations = generate_recommendations(analysis)
    score = calculate_score(analysis)

    report = f"""# Outline Optimization Report

## Summary Score: {score}/100

---

## Structure Analysis

| Metric | Count | Status |
|--------|-------|--------|
| H1 (Title) | {analysis['h1_count']} | {'✓ OK' if analysis['h1_count'] == 1 else '✗ Fix needed'} |
| H2 (Main sections) | {analysis['h2_count']} | {'✓ OK' if 5 <= analysis['h2_count'] <= 12 else '⚠ Review'} |
| H3 (Subsections) | {analysis['h3_count']} | {'✓ Has depth' if analysis['h3_count'] > 0 else '⚠ Consider adding'} |
| H4 (Details) | {analysis['h4_count']} | - |

---

## Content Distribution

| Type | Sections | Percentage | Target |
|------|----------|------------|--------|
| Main Content | {len(analysis['main_h2s'])} | {analysis['main_ratio']:.0f}% | 80% |
| Supplemental | {len(analysis['supplemental_h2s'])} | {analysis['supplemental_ratio']:.0f}% | 20% |

**Status**: {'✓ Well balanced' if 75 <= analysis['main_ratio'] <= 90 else '⚠ Needs adjustment'}

---

## Main Content Sections
"""
    for h2 in analysis['main_h2s']:
        report += f"- {h2.replace('## ', '')}\n"

    report += "\n## Supplemental Sections\n"
    for h2 in analysis['supplemental_h2s']:
        report += f"- {h2.replace('## ', '')}\n"

    if not analysis['supplemental_h2s']:
        report += "- (None identified - consider adding FAQ or Related Topics)\n"

    report += "\n---\n\n## Issues Found\n"
    if analysis['issues']:
        for issue in analysis['issues']:
            report += f"- ⚠ {issue}\n"
    else:
        report += "- ✓ No critical issues found\n"

    report += "\n---\n\n## Recommendations\n"
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report += f"\n### {i}. [{rec['priority']}] {rec['issue']}\n"
            report += f"**Fix**: {rec['fix']}\n"
    else:
        report += "\n✓ Outline meets all optimization criteria!\n"

    return report


def print_error(error_code: str, message: str, details: dict = None):
    """Print formatted error to stderr."""
    print(f"\n[{error_code}]", file=sys.stderr)
    print(f"Error: {message}", file=sys.stderr)
    if details:
        for key, value in details.items():
            if value is not None:
                print(f"  {key}: {value}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_error(
            "USAGE_NO_FILE",
            "No outline file provided",
            {
                "usage": "python outline-analyzer.py <outline-file.md>",
                "example": "python outline-analyzer.py outputs/outline-best-running-shoes.md"
            }
        )
        sys.exit(1)

    filepath = Path(sys.argv[1])
    original_path = sys.argv[1]

    # Try multiple possible locations
    tried_paths = [str(filepath)]

    if not filepath.exists():
        # Try in outputs directory
        filepath = OUTPUTS_DIR / sys.argv[1]
        tried_paths.append(str(filepath))

    if not filepath.exists():
        # Try just the filename in outputs directory
        filepath = OUTPUTS_DIR / Path(sys.argv[1]).name
        tried_paths.append(str(filepath))

    if not filepath.exists():
        print_error(
            "FILE_NOT_FOUND",
            f"Outline file not found: {original_path}",
            {
                "tried_paths": ", ".join(tried_paths),
                "outputs_dir": str(OUTPUTS_DIR),
                "suggestion": "Check the file path and ensure the file exists"
            }
        )
        sys.exit(2)

    try:
        content = filepath.read_text(encoding='utf-8')
    except PermissionError as e:
        print_error(
            "FILE_PERMISSION_ERROR",
            f"Cannot read file: {filepath}",
            {
                "original_error": str(e),
                "suggestion": "Check file read permissions"
            }
        )
        sys.exit(3)
    except UnicodeDecodeError as e:
        print_error(
            "FILE_ENCODING_ERROR",
            f"Cannot decode file as UTF-8: {filepath}",
            {
                "original_error": str(e),
                "suggestion": "Ensure the file is saved as UTF-8 encoding"
            }
        )
        sys.exit(3)
    except OSError as e:
        print_error(
            "FILE_READ_ERROR",
            f"Failed to read file: {filepath}",
            {
                "error_type": type(e).__name__,
                "original_error": str(e)
            }
        )
        sys.exit(3)

    try:
        print(generate_report(content))
    except Exception as e:
        print_error(
            f"UNEXPECTED_{type(e).__name__.upper()}",
            str(e),
            {
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        print("\nThis is an unexpected error. Please report this issue.", file=sys.stderr)
        sys.exit(4)
