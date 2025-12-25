# Prompt 05: SEO Score Module

## Task

Create `seo_score.py` - a module that combines all analyzers into an overall SEO quality score.

## Background

This is the main entry point that orchestrates all analyzers and produces a combined score.

## Requirements

### 1. Create `src/turboseo/analyzers/seo_score.py`

#### Weighted Scoring

```python
WEIGHTS = {
    "content": 0.15,        # Word count, structure
    "human_writing": 0.25,  # Writing standards (NEW - key differentiator)
    "keywords": 0.20,       # Keyword optimization
    "readability": 0.15,    # Readability metrics
    "meta": 0.15,           # Meta elements
    "structure": 0.10,      # Headings, sections
}
```

Note: `human_writing` has high weight - this is our differentiator.

### 2. Main Function

```python
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
        content: Article content
        primary_keyword: Target keyword
        secondary_keywords: Secondary keywords
        meta_title: Meta title tag
        meta_description: Meta description

    Returns:
        SEOResult with overall score and detailed breakdowns
    """
```

### 3. Result Model

```python
class CategoryScore(BaseModel):
    score: int
    weight: float
    weighted_score: float
    issues: list[str]

class SEOResult(BaseModel):
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

    # Action items
    critical_issues: list[str]
    warnings: list[str]
    suggestions: list[str]
```

### 4. Content Scoring

```python
def score_content(content: str) -> tuple[int, list[str]]:
    """Score content length and basic structure."""
    score = 100
    issues = []

    word_count = len(content.split())

    if word_count < 1500:
        score -= 30
        issues.append(f"Content too short ({word_count} words). Minimum: 1500.")
    elif word_count < 2000:
        score -= 15
        issues.append(f"Content could be longer ({word_count} words). Target: 2000+.")
    elif word_count > 4000:
        score -= 5
        issues.append(f"Content is very long ({word_count} words). Consider splitting.")

    return score, issues
```

### 5. Meta Scoring

```python
def score_meta(
    title: str | None,
    description: str | None,
    keyword: str | None
) -> tuple[int, list[str]]:
    """Score meta elements."""
    score = 100
    issues = []

    # Title: 50-60 characters
    if not title:
        score -= 40
        issues.append("Meta title missing.")
    else:
        if len(title) < 50:
            score -= 15
            issues.append(f"Meta title too short ({len(title)} chars). Target: 50-60.")
        elif len(title) > 60:
            score -= 10
            issues.append(f"Meta title too long ({len(title)} chars). Target: 50-60.")

        if keyword and keyword.lower() not in title.lower():
            score -= 15
            issues.append("Primary keyword not in meta title.")

    # Description: 150-160 characters
    if not description:
        score -= 40
        issues.append("Meta description missing.")
    else:
        if len(description) < 150:
            score -= 15
            issues.append(f"Meta description too short ({len(description)} chars). Target: 150-160.")
        elif len(description) > 160:
            score -= 10
            issues.append(f"Meta description too long ({len(description)} chars). Target: 150-160.")

    return score, issues
```

### 6. Structure Scoring

```python
def score_structure(content: str) -> tuple[int, list[str]]:
    """Score heading structure."""
    score = 100
    issues = []

    h1_count = len(re.findall(r'^#\s+', content, re.MULTILINE))
    h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))

    if h1_count == 0:
        score -= 30
        issues.append("Missing H1 heading.")
    elif h1_count > 1:
        score -= 20
        issues.append(f"Multiple H1 headings ({h1_count}). Should have exactly 1.")

    if h2_count < 4:
        score -= 15
        issues.append(f"Too few H2 sections ({h2_count}). Target: 4-6.")

    return score, issues
```

### 7. Grade Calculation

```python
def get_grade(score: int) -> str:
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
```

### 8. Priority Sorting

Sort issues by priority:
1. Critical: Score impact >20 points
2. Warning: Score impact 10-20 points
3. Suggestion: Score impact <10 points

## Tests

Create `tests/test_seo_score.py`:

1. Test overall score calculation
2. Test weight application
3. Test content scoring
4. Test meta scoring
5. Test structure scoring
6. Test grade assignment
7. Test issue prioritization
8. Integration test with all analyzers

## Acceptance Criteria

- [ ] Correctly weights all category scores
- [ ] Human writing score has significant impact
- [ ] All issues correctly prioritized
- [ ] Grade assignment matches score
- [ ] `publishing_ready` logic works
- [ ] 90%+ test coverage
