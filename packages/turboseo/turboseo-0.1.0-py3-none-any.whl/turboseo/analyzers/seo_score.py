"""
SEO Score Analyzer

Combines all analyzers into an overall SEO quality score with weighted categories.
"""

import re

from pydantic import BaseModel

from turboseo.analyzers.keywords import KeywordResult, analyze_keywords
from turboseo.analyzers.readability import ReadabilityResult, analyze_readability
from turboseo.analyzers.writing_standards import (
    WritingStandardsResult,
    analyze_writing_standards,
)

# Category weights - human_writing is our key differentiator
WEIGHTS = {
    "content": 0.15,  # Word count, structure
    "human_writing": 0.25,  # Writing standards (key differentiator)
    "keywords": 0.20,  # Keyword optimization
    "readability": 0.15,  # Readability metrics
    "meta": 0.15,  # Meta elements
    "structure": 0.10,  # Headings, sections
}


class CategoryScore(BaseModel):
    """Score for a single category."""

    score: int
    weight: float
    weighted_score: float
    issues: list[str]


class SEOResult(BaseModel):
    """Complete SEO analysis result."""

    overall_score: int  # 0-100
    grade: str  # A, B, C, D, F
    publishing_ready: bool  # score >= 80 and no critical issues

    # Category breakdowns
    categories: dict[str, CategoryScore]

    # Detailed results from each analyzer
    human_writing: WritingStandardsResult
    readability: ReadabilityResult
    keywords: KeywordResult | None

    # Meta analysis
    meta_title_length: int | None
    meta_description_length: int | None
    meta_issues: list[str]

    # Structure
    word_count: int
    h1_count: int
    h2_count: int
    h3_count: int

    # Action items (prioritized)
    critical_issues: list[str]
    warnings: list[str]
    suggestions: list[str]


def _get_grade(score: int) -> str:
    """Convert score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _score_content(content: str) -> tuple[int, list[str]]:
    """
    Score content length and basic structure.

    Returns:
        Tuple of (score, issues)
    """
    score = 100
    issues = []

    # Clean content for word count (remove markdown syntax)
    clean_content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)
    clean_content = re.sub(r"[*_`\[\]()#]", "", clean_content)
    word_count = len(clean_content.split())

    if word_count < 300:
        score -= 50
        issues.append(f"Content very short ({word_count} words). Minimum: 300 for basic SEO.")
    elif word_count < 800:
        score -= 30
        issues.append(f"Content short ({word_count} words). Target: 800+ for better ranking.")
    elif word_count < 1500:
        score -= 15
        issues.append(f"Content could be longer ({word_count} words). Target: 1500+ for comprehensive coverage.")
    elif word_count > 5000:
        score -= 5
        issues.append(f"Content very long ({word_count} words). Consider splitting into multiple articles.")

    return max(0, score), issues


def _score_meta(
    title: str | None,
    description: str | None,
    keyword: str | None,
) -> tuple[int, list[str]]:
    """
    Score meta elements.

    Returns:
        Tuple of (score, issues)
    """
    score = 100
    issues = []

    # Title: 50-60 characters optimal
    if not title:
        score -= 40
        issues.append("Meta title missing.")
    else:
        title_len = len(title)
        if title_len < 30:
            score -= 25
            issues.append(f"Meta title too short ({title_len} chars). Target: 50-60.")
        elif title_len < 50:
            score -= 10
            issues.append(f"Meta title slightly short ({title_len} chars). Target: 50-60.")
        elif title_len > 70:
            score -= 15
            issues.append(f"Meta title too long ({title_len} chars). May be truncated. Target: 50-60.")
        elif title_len > 60:
            score -= 5
            issues.append(f"Meta title slightly long ({title_len} chars). Target: 50-60.")

        if keyword and keyword.lower() not in title.lower():
            score -= 15
            issues.append("Primary keyword not in meta title.")

    # Description: 150-160 characters optimal
    if not description:
        score -= 40
        issues.append("Meta description missing.")
    else:
        desc_len = len(description)
        if desc_len < 100:
            score -= 25
            issues.append(f"Meta description too short ({desc_len} chars). Target: 150-160.")
        elif desc_len < 150:
            score -= 10
            issues.append(f"Meta description slightly short ({desc_len} chars). Target: 150-160.")
        elif desc_len > 170:
            score -= 15
            issues.append(f"Meta description too long ({desc_len} chars). May be truncated. Target: 150-160.")
        elif desc_len > 160:
            score -= 5
            issues.append(f"Meta description slightly long ({desc_len} chars). Target: 150-160.")

        if keyword and keyword.lower() not in description.lower():
            score -= 10
            issues.append("Primary keyword not in meta description.")

    return max(0, score), issues


def _score_structure(content: str) -> tuple[int, list[str], int, int, int]:
    """
    Score heading structure.

    Returns:
        Tuple of (score, issues, h1_count, h2_count, h3_count)
    """
    score = 100
    issues = []

    h1_count = len(re.findall(r"^#\s+", content, re.MULTILINE))
    h2_count = len(re.findall(r"^##\s+", content, re.MULTILINE))
    h3_count = len(re.findall(r"^###\s+", content, re.MULTILINE))

    # H1 checks
    if h1_count == 0:
        score -= 30
        issues.append("Missing H1 heading.")
    elif h1_count > 1:
        score -= 20
        issues.append(f"Multiple H1 headings ({h1_count}). Should have exactly 1.")

    # H2 checks
    if h2_count == 0:
        score -= 25
        issues.append("No H2 headings. Add subheadings to structure content.")
    elif h2_count < 3:
        score -= 10
        issues.append(f"Few H2 sections ({h2_count}). Target: 3-6 for better structure.")
    elif h2_count > 10:
        score -= 5
        issues.append(f"Many H2 sections ({h2_count}). Consider consolidating.")

    return max(0, score), issues, h1_count, h2_count, h3_count


def _prioritize_issues(
    all_issues: list[tuple[str, int]],
) -> tuple[list[str], list[str], list[str]]:
    """
    Prioritize issues by impact.

    Args:
        all_issues: List of (issue_text, point_impact) tuples

    Returns:
        Tuple of (critical, warnings, suggestions)
    """
    critical = []
    warnings = []
    suggestions = []

    for issue, impact in all_issues:
        if impact >= 25:
            critical.append(issue)
        elif impact >= 10:
            warnings.append(issue)
        else:
            suggestions.append(issue)

    return critical, warnings, suggestions


def analyze_seo(
    content: str,
    primary_keyword: str | None = None,
    secondary_keywords: list[str] | None = None,
    meta_title: str | None = None,
    meta_description: str | None = None,
) -> SEOResult:
    """
    Comprehensive SEO analysis combining all modules.

    Args:
        content: Article content (markdown supported)
        primary_keyword: Target keyword for optimization
        secondary_keywords: Secondary keywords to track
        meta_title: Meta title tag content
        meta_description: Meta description content

    Returns:
        SEOResult with overall score and detailed breakdowns
    """
    categories: dict[str, CategoryScore] = {}
    all_issues: list[tuple[str, int]] = []

    # 1. Human Writing Analysis (25% weight)
    human_writing = analyze_writing_standards(content)
    hw_issues = []
    if human_writing.score < 70:
        hw_issues.append(f"Writing sounds AI-generated (score: {human_writing.score}). Review flagged patterns.")
    elif human_writing.score < 85:
        hw_issues.append(f"Writing has some AI patterns (score: {human_writing.score}). Minor revisions suggested.")

    categories["human_writing"] = CategoryScore(
        score=human_writing.score,
        weight=WEIGHTS["human_writing"],
        weighted_score=human_writing.score * WEIGHTS["human_writing"],
        issues=hw_issues,
    )
    for issue in hw_issues:
        impact = 30 if human_writing.score < 70 else 15
        all_issues.append((issue, impact))

    # 2. Readability Analysis (15% weight)
    readability = analyze_readability(content)
    rd_issues = []
    if readability.score < 60:
        rd_issues.append(f"Poor readability (score: {readability.score}). Simplify sentences and vocabulary.")
    elif readability.score < 80:
        rd_issues.append(f"Readability could improve (score: {readability.score}).")
    rd_issues.extend(readability.recommendations[:2])  # Top 2 recommendations

    categories["readability"] = CategoryScore(
        score=readability.score,
        weight=WEIGHTS["readability"],
        weighted_score=readability.score * WEIGHTS["readability"],
        issues=rd_issues,
    )
    for issue in rd_issues:
        impact = 20 if readability.score < 60 else 10
        all_issues.append((issue, impact))

    # 3. Keyword Analysis (20% weight) - only if keyword provided
    keywords_result: KeywordResult | None = None
    if primary_keyword:
        keywords_result = analyze_keywords(
            content,
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords,
            target_density=1.5,
        )
        kw_score = 100

        # Density scoring
        if keywords_result.primary.status == "too_low":
            kw_score -= 30
        elif keywords_result.primary.status == "slightly_low":
            kw_score -= 15
        elif keywords_result.primary.status == "too_high":
            kw_score -= 20
        elif keywords_result.primary.status == "slightly_high":
            kw_score -= 5

        # Placement scoring
        pl = keywords_result.primary.placements
        if not pl.in_h1:
            kw_score -= 15
        if not pl.in_first_100_words:
            kw_score -= 10
        if not pl.in_conclusion:
            kw_score -= 5

        # Stuffing penalty
        if keywords_result.stuffing_risk.level == "high":
            kw_score -= 25
        elif keywords_result.stuffing_risk.level == "medium":
            kw_score -= 15

        kw_score = max(0, kw_score)
        kw_issues = keywords_result.recommendations[:3]  # Top 3 recommendations

        categories["keywords"] = CategoryScore(
            score=kw_score,
            weight=WEIGHTS["keywords"],
            weighted_score=kw_score * WEIGHTS["keywords"],
            issues=kw_issues,
        )
        for issue in kw_issues:
            all_issues.append((issue, 15))
    else:
        # No keyword provided - neutral score
        categories["keywords"] = CategoryScore(
            score=70,
            weight=WEIGHTS["keywords"],
            weighted_score=70 * WEIGHTS["keywords"],
            issues=["No primary keyword specified for optimization."],
        )
        all_issues.append(("No primary keyword specified for optimization.", 10))

    # 4. Content Scoring (15% weight)
    content_score, content_issues = _score_content(content)
    categories["content"] = CategoryScore(
        score=content_score,
        weight=WEIGHTS["content"],
        weighted_score=content_score * WEIGHTS["content"],
        issues=content_issues,
    )
    for issue in content_issues:
        impact = 25 if "very short" in issue.lower() else 15 if "short" in issue.lower() else 5
        all_issues.append((issue, impact))

    # 5. Meta Scoring (15% weight)
    meta_score, meta_issues = _score_meta(meta_title, meta_description, primary_keyword)
    categories["meta"] = CategoryScore(
        score=meta_score,
        weight=WEIGHTS["meta"],
        weighted_score=meta_score * WEIGHTS["meta"],
        issues=meta_issues,
    )
    for issue in meta_issues:
        impact = 25 if "missing" in issue.lower() else 15 if "too" in issue.lower() else 10
        all_issues.append((issue, impact))

    # 6. Structure Scoring (10% weight)
    structure_score, structure_issues, h1_count, h2_count, h3_count = _score_structure(content)
    categories["structure"] = CategoryScore(
        score=structure_score,
        weight=WEIGHTS["structure"],
        weighted_score=structure_score * WEIGHTS["structure"],
        issues=structure_issues,
    )
    for issue in structure_issues:
        impact = 25 if "missing" in issue.lower().replace("few", "") else 10
        all_issues.append((issue, impact))

    # Calculate overall score
    overall_score = int(sum(cat.weighted_score for cat in categories.values()))
    overall_score = max(0, min(100, overall_score))

    # Prioritize issues
    critical, warnings, suggestions = _prioritize_issues(all_issues)

    # Determine publishing readiness
    publishing_ready = overall_score >= 80 and len(critical) == 0

    # Get word count
    clean_content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)
    clean_content = re.sub(r"[*_`\[\]()#]", "", clean_content)
    word_count = len(clean_content.split())

    return SEOResult(
        overall_score=overall_score,
        grade=_get_grade(overall_score),
        publishing_ready=publishing_ready,
        categories=categories,
        human_writing=human_writing,
        readability=readability,
        keywords=keywords_result,
        meta_title_length=len(meta_title) if meta_title else None,
        meta_description_length=len(meta_description) if meta_description else None,
        meta_issues=meta_issues,
        word_count=word_count,
        h1_count=h1_count,
        h2_count=h2_count,
        h3_count=h3_count,
        critical_issues=critical,
        warnings=warnings,
        suggestions=suggestions,
    )
