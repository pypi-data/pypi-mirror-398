# Prompt 02: Writing Standards Checker

## Task

Create `writing_standards.py` - the core module that detects AI-sounding writing based on Wikipedia's "Signs of AI writing" guidelines.

## Background

Wikipedia maintains a detailed guide on detecting AI-generated content. We'll encode these rules into a Python checker that scores content on how "human" it sounds.

## Requirements

### 1. Create `src/turboseo/analyzers/writing_standards.py`

#### AI Vocabulary Detection
```python
AI_VOCABULARY = {
    # High confidence AI words (from Wikipedia guide + research)
    "delve": 5,
    "tapestry": 5,
    "vibrant": 3,
    "pivotal": 4,
    "crucial": 3,
    "intricate": 4,
    "intricacies": 4,
    "foster": 3,
    "fostering": 3,
    "garner": 4,
    "underscore": 4,
    "showcase": 3,
    "testament": 4,
    "landscape": 2,  # Only when used abstractly
    "interplay": 4,
    "enhance": 2,
    "leverage": 3,
    "multifaceted": 4,
    "comprehensive": 2,
    "robust": 2,
    "seamless": 3,
    "cutting-edge": 3,
    "groundbreaking": 4,
    "realm": 3,
    "embark": 4,
    "journey": 2,  # When used metaphorically
    "navigate": 2,  # When used metaphorically
    "unveil": 3,
    "beacon": 4,
    "paramount": 4,
    "commendable": 3,
    "meticulous": 3,
    "ever-evolving": 4,
    "game-changer": 4,
}
```

#### Puffery Pattern Detection
```python
PUFFERY_PATTERNS = [
    (r"stands?\s+as\s+a?\s*(testament|reminder|symbol|beacon)", 10),
    (r"plays?\s+a\s+(vital|significant|crucial|pivotal|key)\s+role", 8),
    (r"(enduring|lasting|indelible)\s+(legacy|impact|mark)", 8),
    (r"nestled\s+(in|within|among)", 6),
    (r"rich\s+(tapestry|heritage|history|tradition)", 8),
    (r"in\s+the\s+heart\s+of", 5),
    (r"boasts?\s+(a|an)", 5),
    (r"continues?\s+to\s+captivate", 8),
    (r"(groundbreaking|revolutionary)\s+(approach|method|solution|work)", 8),
    (r"deeply\s+rooted", 6),
    (r"at\s+the\s+forefront", 5),
    (r"(stunning|breathtaking)\s+(natural\s+)?beauty", 6),
    (r"serves?\s+as\s+a\s+(reminder|testament|symbol)", 8),
]
```

#### Superficial Analysis Detection
```python
SUPERFICIAL_PATTERNS = [
    # Sentence-ending "-ing" phrases (major AI tell)
    (r",\s*(highlighting|emphasizing|reflecting|underscoring|showcasing)\s+", 8),
    (r",\s*ensuring\s+", 5),
    (r",\s*demonstrating\s+", 5),
    (r",\s*illustrating\s+", 5),

    # Vague analysis phrases
    (r"(conducive|tantamount|contributing)\s+to", 6),
    (r"aligns?\s+with", 4),
    (r"encompassing", 4),
    (r"reinforces?\s+(the\s+)?(importance|significance|need)", 6),
]
```

#### Structural Red Flags
```python
STRUCTURAL_PATTERNS = [
    # Conclusion formulas
    (r"^(In\s+summary|In\s+conclusion|Overall|To\s+summarize),", 10),

    # Challenge formula
    (r"Despite\s+(its|their|the)\s+.{10,60},?\s*.{5,40}\s+faces?\s+(several\s+)?(challenges|obstacles)", 12),

    # Negative parallelisms
    (r"Not\s+only\s+.{10,100}\s+but\s+(also\s+)?", 8),
    (r"It'?s\s+not\s+just\s+about\s+.{10,60},?\s*it'?s", 8),

    # Legacy/importance formula
    (r"(legacy|importance|significance)\s+.{5,30}\s+cannot\s+be\s+(overstated|understated)", 10),
]
```

#### Rule of Three Detection
Detect overuse of triple constructions:
- Count instances of "X, Y, and Z" patterns
- Flag if more than 2 per 1000 words

#### Formatting Issues
```python
FORMATTING_CHECKS = {
    "em_dash_density": 3,      # Max em-dashes per 1000 words
    "title_case_headings": True,  # Flag title case in ## headings
    "excessive_bold": 5,       # Max bold phrases per 1000 words
    "emoji_usage": True,       # Flag any emoji
}
```

### 2. Main Analysis Function

```python
def analyze_writing_standards(
    content: str,
    strict: bool = False
) -> WritingStandardsResult:
    """
    Analyze content for AI writing patterns.

    Args:
        content: The text to analyze
        strict: If True, use stricter thresholds

    Returns:
        WritingStandardsResult with score, issues, and suggestions
    """
```

### 3. Result Model (Pydantic)

```python
class WritingIssue(BaseModel):
    line: int
    column: int
    text: str
    category: str  # vocabulary, puffery, superficial, structural, formatting
    severity: str  # high, medium, low
    suggestion: str

class WritingStandardsResult(BaseModel):
    score: int  # 0-100
    grade: str  # A, B, C, D, F
    issues: list[WritingIssue]
    summary: dict[str, int]  # Count by category
    word_count: int
```

### 4. Scoring Logic

```
Starting score: 100

Deductions:
- AI vocabulary word: -[word_weight] points
- Puffery pattern: -[pattern_weight] points
- Superficial analysis: -[pattern_weight] points
- Structural red flag: -[pattern_weight] points
- Rule of three (excess): -3 points each
- Formatting issues: -2 points each

Minimum score: 0
```

### 5. Suggestion Generation

For each issue, provide a specific fix:
- "delve" → "explore", "examine", "look at"
- "plays a pivotal role" → "[specific impact]" or remove
- "highlighting its significance" → state the significance directly

## Tests

Create `tests/test_writing_standards.py`:

1. Test AI vocabulary detection
2. Test puffery pattern detection
3. Test superficial analysis detection
4. Test structural red flags
5. Test scoring calculation
6. Test with known AI-generated samples (high score = bad)
7. Test with known human samples (low deductions)

## Test Fixtures

Create `tests/fixtures/`:

### `ai_sample_1.md` (should score <70)
```markdown
# The Transformative Journey of Digital Marketing

In today's ever-evolving digital landscape, businesses must delve into
the intricate tapestry of online marketing strategies. Social media
plays a pivotal role in fostering meaningful connections with audiences,
highlighting the importance of authentic engagement.

Despite its challenges, digital marketing continues to captivate
organizations worldwide, showcasing its enduring legacy as a
cornerstone of modern business strategy.
```

### `human_sample_1.md` (should score >85)
```markdown
# How Digital Marketing Actually Works

Most businesses waste money on digital marketing because they copy
what big brands do. Here's what works for companies under $10M revenue.

First, forget about "building awareness." Track conversions. If you
can't measure it leading to revenue, stop doing it.

The biggest mistake? Spreading budget across too many channels. Pick
two. Get good at them. Then expand.
```

## Acceptance Criteria

- [ ] Detects all Wikipedia-listed AI vocabulary
- [ ] Identifies puffery and superficial analysis patterns
- [ ] Catches structural red flags
- [ ] Provides actionable suggestions
- [ ] AI samples score <70, human samples score >85
- [ ] 90%+ test coverage
