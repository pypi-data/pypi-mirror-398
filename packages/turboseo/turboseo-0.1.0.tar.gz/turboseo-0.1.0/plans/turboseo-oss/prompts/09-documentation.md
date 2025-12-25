# Prompt 09: Documentation

## Task

Create comprehensive documentation for TurboSEO.

## Requirements

### 1. Main README.md

```markdown
# TurboSEO

An open-source SEO content toolkit that helps you write content that ranks—and sounds human.

## Why TurboSEO?

Most SEO tools help you optimize for search engines. TurboSEO also optimizes for **not sounding like AI wrote it**.

Based on [Wikipedia's "Signs of AI Writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guidelines, TurboSEO checks your content for:
- AI vocabulary (delve, tapestry, pivotal, etc.)
- Puffery patterns ("plays a vital role", "stands as a testament")
- Superficial analysis (sentences ending with "highlighting...", "emphasizing...")
- Structural clichés ("In conclusion", "Despite challenges...")

## Features

- **Human Writing Score** (0-100) - Detect AI-sounding patterns
- **SEO Analysis** - Keywords, readability, structure
- **CLI Tool** - Quick analysis from terminal
- **Claude Code Integration** - Slash commands and agents

## Installation

```bash
pip install turboseo
```

## Quick Start

### Check if content sounds human

```bash
turboseo check article.md
```

### Full SEO analysis

```bash
turboseo analyze article.md --keyword "podcast hosting"
```

### Use with Claude Code

```bash
cd your-content-project
# Copy .claude/ directory from turboseo
/write podcast monetization strategies
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Human Writing Rules](docs/human-writing-rules.md)
- [CLI Reference](docs/cli-reference.md)
- [Claude Code Setup](docs/claude-code-setup.md)
- [API Reference](docs/api-reference.md)

## License

MIT
```

### 2. docs/getting-started.md

```markdown
# Getting Started with TurboSEO

## Installation

### From PyPI

```bash
pip install turboseo
```

### From Source

```bash
git clone https://github.com/yourusername/turboseo.git
cd turboseo
pip install -e .
```

## Your First Analysis

### 1. Check Human Writing Score

Create a file `test-article.md`:

```markdown
# How to Start a Podcast

Starting a podcast is easier than you think...
```

Run the check:

```bash
turboseo check test-article.md
```

You'll see a score from 0-100:
- **90-100**: Sounds human
- **80-89**: Minor AI tells
- **70-79**: Noticeable AI patterns
- **<70**: Sounds AI-generated

### 2. Fix AI-Sounding Content

If your score is low, the output shows you exactly what to fix:

```
Line 5: "delve" - AI vocabulary
  → Replace with: explore, examine, look at

Line 12: "plays a pivotal role" - Puffery pattern
  → State the specific impact instead
```

### 3. Full SEO Analysis

```bash
turboseo analyze test-article.md \
  --keyword "start a podcast" \
  --title "How to Start a Podcast in 2024" \
  --description "Learn to start a podcast from scratch..."
```

## Using with Claude Code

TurboSEO works best as a Claude Code workspace.

### Setup

1. Copy the `.claude/` directory to your project
2. Create context files in `context/`
3. Use slash commands:

```
/research podcast monetization
/write podcast monetization strategies
/check-human drafts/podcast-monetization.md
```

See [Claude Code Setup](claude-code-setup.md) for details.
```

### 3. docs/human-writing-rules.md

```markdown
# Human Writing Rules

TurboSEO checks for patterns that make content sound AI-generated, based on Wikipedia's ["Signs of AI Writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guide.

## AI Vocabulary

These words are overused by AI and rarely used by humans:

| Word | Why It's a Problem | Better Alternatives |
|------|-------------------|---------------------|
| delve | AI uses it 10x more than humans | explore, examine, look at |
| tapestry | Almost never used naturally | mix, variety, combination |
| vibrant | Vague, overused | lively, active, specific adjective |
| pivotal | Sounds like marketing | important, key, critical |
| intricate | Often unnecessary | complex, detailed |
| foster | Corporate speak | build, encourage, develop |
| garner | Archaic | get, earn, attract |
| underscore | Pretentious | show, prove, demonstrate |
| testament | Cliché | proof, evidence, sign |
| leverage | Business jargon | use, apply |
| robust | Meaningless filler | strong, solid, reliable |
| seamless | Marketing speak | smooth, easy |
| groundbreaking | Hyperbole | new, innovative, first |
| realm | Fantasy novel vibes | area, field, space |
| embark | Unnecessarily dramatic | start, begin |

## Puffery Patterns

Phrases that sound impressive but say nothing:

| Pattern | Problem | Fix |
|---------|---------|-----|
| "plays a pivotal role in" | Vague | State the specific impact |
| "stands as a testament to" | Cliché | "shows", "proves" |
| "rich tapestry of" | Meaningless | "mix of", "variety of" |
| "nestled in" | Travel brochure cliché | "located in", "in" |
| "continues to captivate" | Empty | What does it actually do? |
| "in the heart of" | Cliché | Just say where |
| "boasts a" | Promotional | "has", "offers" |

## Superficial Analysis

Ending sentences with "-ing" phrases that add nothing:

❌ "Sales grew 40%, highlighting the importance of marketing."
✅ "Sales grew 40%. Good marketing works."

❌ "The company expanded, underscoring its commitment to growth."
✅ "The company expanded into three new markets."

The "-ing" phrase often states the obvious or adds vague significance. Cut it and be specific.

## Structural Clichés

### "In conclusion..."

Don't announce your conclusion. Just conclude.

❌ "In conclusion, podcasting offers many opportunities."
✅ "Start today. Pick a topic, hit record, and publish."

### The Challenge Formula

❌ "Despite its challenges, the industry continues to thrive."
✅ Mention specific challenges and how they're addressed—or don't mention them at all.

### Negative Parallelism

❌ "Not only does this improve efficiency, but it also reduces costs."
✅ "This improves efficiency and reduces costs."

## The Human Writing Test

Before publishing, ask:
1. Would I say this out loud to a friend?
2. Is every sentence specific, not vague?
3. Did I cut unnecessary words?
4. Does it sound like a person wrote it?

Run `turboseo check` to verify.
```

### 4. docs/cli-reference.md

```markdown
# CLI Reference

## Commands

### turboseo check

Check content for AI writing patterns.

```bash
turboseo check <file> [options]
```

**Options:**
- `--strict` - Use stricter thresholds
- `--json` - Output as JSON

**Example:**
```bash
turboseo check article.md
turboseo check article.md --strict --json > report.json
```

### turboseo analyze

Full SEO analysis.

```bash
turboseo analyze <file> [options]
```

**Options:**
- `-k, --keyword` - Primary keyword
- `-s, --secondary` - Secondary keywords (can repeat)
- `--title` - Meta title
- `--description` - Meta description
- `--json` - Output as JSON

**Example:**
```bash
turboseo analyze article.md \
  --keyword "podcast hosting" \
  --secondary "best podcast host" \
  --secondary "podcast platforms" \
  --title "Best Podcast Hosting in 2024"
```

### turboseo readability

Analyze readability only.

```bash
turboseo readability <file> [--json]
```

### turboseo keywords

Analyze keyword usage only.

```bash
turboseo keywords <file> -k <keyword> [options]
```

**Options:**
- `-k, --keyword` - Primary keyword (required)
- `-s, --secondary` - Secondary keywords
- `-d, --target-density` - Target density % (default: 1.5)
- `--json` - Output as JSON

### turboseo version

Show version.

```bash
turboseo version
```

## Exit Codes

- `0` - Success
- `1` - Error (file not found, invalid options)
- `2` - Analysis failed (score below threshold with --strict)

## JSON Output

All commands support `--json` for machine-readable output:

```json
{
  "score": 85,
  "grade": "B",
  "issues": [
    {
      "line": 5,
      "column": 10,
      "text": "delve",
      "category": "vocabulary",
      "severity": "medium",
      "suggestion": "Replace with: explore, examine"
    }
  ],
  "summary": {
    "vocabulary": 1,
    "puffery": 0,
    "superficial": 0,
    "structural": 0
  }
}
```
```

### 5. docs/claude-code-setup.md

```markdown
# Claude Code Setup

TurboSEO is designed to work as a Claude Code workspace.

## Installation

1. Install TurboSEO:
```bash
pip install turboseo
```

2. Copy the Claude Code configuration:
```bash
git clone https://github.com/yourusername/turboseo.git
cp -r turboseo/.claude your-project/
cp -r turboseo/context your-project/
```

3. Create your workspace directories:
```bash
mkdir -p topics research drafts published
```

## Slash Commands

### /research

Research a topic before writing.

```
/research podcast monetization
```

Creates a research brief in `research/`.

### /write

Write an SEO-optimized article.

```
/write podcast monetization strategies
```

Automatically:
- Checks human writing score
- Fixes AI tells if needed
- Saves to `drafts/`

### /check-human

Check if content sounds human.

```
/check-human drafts/podcast-monetization.md
```

### /analyze

Full SEO analysis.

```
/analyze drafts/podcast-monetization.md
```

### /optimize

Final optimization pass.

```
/optimize drafts/podcast-monetization.md
```

## Agents

### human-writer

Rewrites AI-sounding content to sound human.

### seo-optimizer

Provides SEO improvement recommendations.

### meta-creator

Generates meta titles and descriptions.

## Context Files

Customize these in `context/`:

- `brand-voice.md` - Your brand's voice and tone
- `style-guide.md` - Writing style preferences
- `human-writing-rules.md` - Rules reference
- `internal-links-map.md` - Pages for internal linking
- `seo-guidelines.md` - SEO requirements

## Workflow

1. `/research [topic]` - Create research brief
2. `/write [topic]` - Write article
3. Review human score, fix if needed
4. `/optimize [file]` - Final pass
5. Move to `published/`
```

## Acceptance Criteria

- [ ] README clearly explains the project
- [ ] Getting started guide works for new users
- [ ] Human writing rules are comprehensive
- [ ] CLI reference covers all commands
- [ ] Claude Code setup is step-by-step
- [ ] All examples work
