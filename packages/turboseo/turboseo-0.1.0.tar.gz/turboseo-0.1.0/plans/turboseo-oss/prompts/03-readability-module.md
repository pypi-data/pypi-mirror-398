# Prompt 03: Readability Module

## Task

Create `readability.py` - a module for analyzing content readability using multiple metrics.

## Background

Port and improve the readability scorer from seomachine. Focus on metrics that matter for SEO content.

## Requirements

### 1. Create `src/turboseo/analyzers/readability.py`

#### Core Metrics (via textstat)
- Flesch Reading Ease (target: 60-70)
- Flesch-Kincaid Grade Level (target: 8-10)
- Gunning Fog Index
- SMOG Index
- Automated Readability Index

#### Structure Analysis
- Average sentence length (target: 15-20 words)
- Average paragraph length (target: 2-4 sentences)
- Longest sentence detection
- Very long sentences (>35 words) count

#### Complexity Analysis
- Passive voice percentage (target: <20%)
- Complex word ratio (3+ syllables)
- Transition word usage

### 2. Main Function

```python
def analyze_readability(content: str) -> ReadabilityResult:
    """
    Comprehensive readability analysis.

    Args:
        content: Text to analyze

    Returns:
        ReadabilityResult with scores, metrics, and recommendations
    """
```

### 3. Result Model

```python
class ReadabilityResult(BaseModel):
    score: int  # 0-100 overall readability score
    grade: str  # A, B, C, D, F

    # Core metrics
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    smog_index: float

    # Structure
    avg_sentence_length: float
    avg_paragraph_length: float
    long_sentence_count: int
    very_long_sentence_count: int

    # Complexity
    passive_voice_ratio: float
    complex_word_ratio: float
    transition_word_count: int

    # Recommendations
    recommendations: list[str]
    status: str  # excellent, good, needs_improvement, poor
```

### 4. Scoring

```
Starting score: 100

Flesch Reading Ease:
- <30 (very difficult): -30
- 30-50 (difficult): -20
- 50-60 (fairly difficult): -10
- 60-70 (optimal): 0
- >80 (too easy): -5

Grade Level:
- <6 (too simple): -10
- 6-8 (slightly simple): -5
- 8-10 (optimal): 0
- 10-12 (slightly complex): -10
- >12 (too complex): -20

Sentence Length:
- avg >30 words: -20
- avg >25 words: -10
- avg >20 words: -5

Very Long Sentences:
- Each sentence >35 words: -3

Passive Voice:
- >30%: -10
- >20%: -5

Paragraphs:
- avg >6 sentences: -10
- avg >4 sentences: -5
```

### 5. Recommendations

Generate specific, actionable recommendations:
- "Average sentence length is 28 words. Break up sentences for better readability. Target: 15-20 words."
- "3 sentences exceed 35 words. Split these into multiple sentences."
- "Passive voice at 25%. Convert to active voice where possible."

## Tests

Create `tests/test_readability.py`:

1. Test Flesch Reading Ease calculation
2. Test grade level calculation
3. Test sentence length analysis
4. Test passive voice detection
5. Test scoring logic
6. Test with samples at different reading levels

## Acceptance Criteria

- [ ] All metrics calculate correctly
- [ ] Scoring matches defined rules
- [ ] Recommendations are specific and actionable
- [ ] Handles edge cases (empty content, single sentence)
- [ ] 90%+ test coverage
