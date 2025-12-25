# TurboSEO - Open Source SEO Content Toolkit

## Goal

Build a Claude Code workspace for creating SEO-optimized content that **doesn't sound AI-generated**. The key differentiator is a writing standards checker based on Wikipedia's "Signs of AI writing" guidelines.

## Background

Inspired by `seomachine`, but with critical improvements:
1. Writing that passes human-detection tests
2. Cleaner Python modules
3. Fewer paid API dependencies
4. Better open source packaging

## Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Workspace                     │
├─────────────────────────────────────────────────────────────┤
│  Slash Commands        │  Agents                            │
│  /research             │  content-analyzer                  │
│  /write                │  seo-optimizer                     │
│  /rewrite              │  human-writer (NEW!)               │
│  /analyze              │  meta-creator                      │
│  /check-human          │  internal-linker                   │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Python Analysis Engine                    │
├─────────────────────────────────────────────────────────────┤
│  writing_standards.py  ← NEW! Core differentiator           │
│  readability.py                                              │
│  keywords.py                                                 │
│  seo_score.py                                                │
│  intent.py                                                   │
└─────────────────────────────────────────────────────────────┘
```

## The Human Writing Standards Checker

Based on Wikipedia's "Signs of AI writing" guide, detect and penalize:

### Vocabulary Flags (AI-overused words)
```python
AI_VOCABULARY = [
    "delve", "tapestry", "vibrant", "pivotal", "crucial",
    "intricate", "foster", "garner", "underscore", "showcase",
    "testament", "landscape", "interplay", "enhance", "leverage",
    "multifaceted", "comprehensive", "robust", "seamless", "cutting-edge"
]
```

### Puffery Patterns
```python
PUFFERY_PATTERNS = [
    r"stands as a? ?(testament|reminder|symbol)",
    r"plays a (vital|significant|crucial|pivotal) role",
    r"(enduring|lasting) legacy",
    r"nestled (in|within|among)",
    r"rich (tapestry|heritage|history)",
    r"in the heart of",
    r"boasts a",
    r"continues to captivate",
    r"(groundbreaking|revolutionary) (approach|method|solution)",
]
```

### Superficial Analysis Patterns
```python
SUPERFICIAL_PATTERNS = [
    r",\s*(highlighting|emphasizing|reflecting|underscoring|showcasing)\s",
    r",\s*ensuring\s",
    r"(conducive|tantamount|contributing) to",
    r"aligns with",
    r"encompassing",
]
```

### Structural Red Flags
```python
STRUCTURAL_FLAGS = [
    r"^(In summary|In conclusion|Overall),",  # Section summaries
    r"Despite its .{10,50}, .{5,30} faces (several )?(challenges|obstacles)",  # Challenge formula
    r"Not only .{10,100} but (also )?",  # Negative parallelism
    r"It's not just about .{10,50}, it's",  # Another parallelism
]
```

### Rule of Three Detection
Detect overuse of triple adjectives/phrases:
- "adjective, adjective, and adjective"
- "phrase, phrase, and phrase"

### Formatting Issues
- Excessive em-dashes (—)
- Title case in headings
- Excessive boldface
- Emoji usage

## Scoring System

```
Human Writing Score: 0-100

Deductions:
- Each AI vocabulary word: -2 points
- Each puffery pattern: -5 points
- Each superficial analysis: -5 points
- Structural red flag: -10 points
- Excessive rule of three: -3 points each
- Em-dash overuse (>3 per 1000 words): -5 points
- Title case headings: -2 points each

Grades:
90-100: Excellent (sounds human)
80-89:  Good (minor AI tells)
70-79:  Fair (noticeable AI patterns)
60-69:  Poor (obvious AI writing)
<60:    Fail (clearly AI-generated)
```

## Project Structure

```
turboseo/
├── .claude/
│   ├── commands/
│   │   ├── research.md
│   │   ├── write.md
│   │   ├── rewrite.md
│   │   ├── analyze.md
│   │   ├── check-human.md      # NEW
│   │   └── optimize.md
│   └── agents/
│       ├── content-analyzer.md
│       ├── seo-optimizer.md
│       ├── human-writer.md     # NEW - rewrites to sound human
│       ├── meta-creator.md
│       ├── internal-linker.md
│       └── keyword-mapper.md
├── src/
│   └── turboseo/
│       ├── __init__.py
│       ├── analyzers/
│       │   ├── __init__.py
│       │   ├── writing_standards.py   # NEW - core differentiator
│       │   ├── readability.py
│       │   ├── keywords.py
│       │   ├── seo_score.py
│       │   └── intent.py
│       └── cli/
│           ├── __init__.py
│           └── main.py
├── context/
│   ├── brand-voice.md
│   ├── writing-examples.md
│   ├── style-guide.md
│   ├── human-writing-rules.md   # NEW
│   └── seo-guidelines.md
├── tests/
│   ├── test_writing_standards.py
│   ├── test_readability.py
│   └── fixtures/
│       ├── ai_generated_samples/
│       └── human_written_samples/
├── topics/
├── research/
├── drafts/
├── published/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
└── CONTRIBUTING.md
```

## Phases

### Phase 1: Core Python Modules
1. `writing_standards.py` - The human writing checker
2. `readability.py` - Port from seomachine
3. `keywords.py` - Port from seomachine
4. `seo_score.py` - Port from seomachine
5. CLI tool for testing

### Phase 2: Claude Code Workspace
1. Set up `.claude/` structure
2. Create slash commands
3. Create agents (especially `human-writer`)
4. Context files and templates

### Phase 3: Integration & Polish
1. Commands automatically run human check
2. Human-writer agent fixes AI tells
3. Documentation
4. PyPI packaging

### Phase 4: Optional Integrations
1. Google Search Console (optional)
2. Google Analytics 4 (optional)
3. Free SERP alternatives

## Key Differentiators from seomachine

| seomachine | TurboSEO |
|------------|----------|
| No AI detection | Human writing score (0-100) |
| Generic writing | Wikipedia-based writing rules |
| DataForSEO required | Core features free |
| Closed examples | Open source examples |
| Complex setup | Simple pip install + Claude Code |

## Acceptance Criteria

### Phase 1 Complete
- [ ] `writing_standards.py` detects all Wikipedia AI signs
- [ ] CLI: `turboseo check content.md` outputs human score
- [ ] 90%+ test coverage on writing standards
- [ ] Test fixtures with known AI vs human samples

### Phase 2 Complete
- [ ] All slash commands working
- [ ] `/check-human` command runs Python checker
- [ ] `human-writer` agent rewrites AI-sounding text
- [ ] Context files documented

### Phase 3 Complete
- [ ] `/write` auto-runs human check
- [ ] Installable via pip
- [ ] Full documentation
- [ ] Published to PyPI

## Example Usage

### CLI
```bash
# Check if content sounds human
turboseo check article.md

# Output:
# Human Writing Score: 72/100 (Fair)
#
# Issues found:
# - Line 5: "delve" (AI vocabulary)
# - Line 12: "plays a pivotal role" (puffery)
# - Line 23: "highlighting its significance" (superficial analysis)
# - Line 45: Challenge formula detected
#
# Suggestions:
# - Replace "delve into" with "explore" or "examine"
# - Replace "plays a pivotal role" with specific impact
# - Remove "-ing" phrase, state the significance directly
```

### Claude Code
```
/write podcast monetization strategies

> Writing article...
> Running human check...
> Human Score: 68/100 - Running human-writer agent...
> Final Human Score: 91/100
> Saved to drafts/podcast-monetization-strategies-2025-12-12.md
```

## Open Questions

1. Should we include a "rewrite to human" feature in the CLI?
2. How strict should the default thresholds be?
3. Should we train a small ML model for better detection, or keep it rule-based?
4. What's the best name? `turboseo`, `humanseo`, `cleanseo`?
