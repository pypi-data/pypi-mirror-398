# Prompt 04: Keywords Module

## Task

Create `keywords.py` - a module for analyzing keyword usage, density, and distribution.

## Background

Port and simplify the keyword analyzer from seomachine. Remove the ML clustering for now (Phase 2 feature).

## Requirements

### 1. Create `src/turboseo/analyzers/keywords.py`

#### Core Features
- Keyword density calculation
- Keyword distribution across sections
- Critical placement checks (H1, first 100 words, H2s, conclusion)
- Keyword stuffing detection
- LSI keyword identification (simple version)

### 2. Main Function

```python
def analyze_keywords(
    content: str,
    primary_keyword: str,
    secondary_keywords: list[str] | None = None,
    target_density: float = 1.5
) -> KeywordResult:
    """
    Analyze keyword usage in content.

    Args:
        content: Article text
        primary_keyword: Main target keyword
        secondary_keywords: Optional secondary keywords
        target_density: Target density percentage (default 1.5%)

    Returns:
        KeywordResult with density, distribution, and recommendations
    """
```

### 3. Result Model

```python
class KeywordPlacement(BaseModel):
    in_h1: bool
    in_first_100_words: bool
    in_conclusion: bool
    h2_count: int
    h2_with_keyword: int

class KeywordAnalysis(BaseModel):
    keyword: str
    exact_matches: int
    total_occurrences: int
    density: float
    target_density: float
    status: str  # too_low, slightly_low, optimal, slightly_high, too_high
    placements: KeywordPlacement

class StuffingRisk(BaseModel):
    level: str  # none, low, medium, high
    warnings: list[str]

class KeywordResult(BaseModel):
    word_count: int
    primary: KeywordAnalysis
    secondary: list[KeywordAnalysis]
    stuffing_risk: StuffingRisk
    distribution: list[dict]  # Per-section breakdown
    recommendations: list[str]
```

### 4. Density Status

```python
def get_density_status(actual: float, target: float) -> str:
    if actual < target * 0.5:
        return "too_low"
    elif actual < target * 0.8:
        return "slightly_low"
    elif actual <= target * 1.2:
        return "optimal"
    elif actual <= target * 1.5:
        return "slightly_high"
    else:
        return "too_high"
```

### 5. Stuffing Detection

Flag as potential stuffing when:
- Overall density > 3%
- Any paragraph density > 5%
- Keyword in 5+ consecutive sentences
- Same exact phrase repeated 3+ times in 100 words

### 6. Recommendations

Generate specific recommendations:
- "Primary keyword density is 0.8% (target: 1.5%). Add 3-4 more natural mentions."
- "Keyword missing from H1. Include it in the title."
- "Keyword appears in 1/6 H2 headings. Aim for 2-3 H2s with keyword variations."
- "Warning: Paragraph 4 has 6% keyword density. Reduce to avoid stuffing."

## Tests

Create `tests/test_keywords.py`:

1. Test density calculation
2. Test placement detection
3. Test stuffing detection
4. Test section distribution
5. Test recommendations
6. Edge cases (no keywords, keyword in every sentence)

## Acceptance Criteria

- [ ] Accurate density calculation
- [ ] All critical placements detected
- [ ] Stuffing detection works
- [ ] Per-section distribution calculated
- [ ] Recommendations are actionable
- [ ] 90%+ test coverage
