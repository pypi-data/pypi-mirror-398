# Prompt 06: CLI Tool

## Task

Create the `turboseo` CLI tool using Click and Rich for beautiful terminal output.

## Requirements

### 1. Create `src/turboseo/cli/main.py`

#### Commands

```
turboseo
├── check <file>           # Check content for AI writing patterns
├── analyze <file>         # Full SEO analysis
├── readability <file>     # Readability analysis only
├── keywords <file>        # Keyword analysis only
│   --keyword, -k          # Primary keyword
│   --secondary, -s        # Secondary keywords (multiple)
└── version                # Show version
```

### 2. Check Command (Human Writing)

```python
@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Use stricter thresholds")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def check(file: str, strict: bool, output_json: bool):
    """Check content for AI writing patterns."""
```

Output (Rich formatted):
```
╭─────────────────────────────────────────────────────────────╮
│                  Human Writing Check                         │
╰─────────────────────────────────────────────────────────────╯

Score: 72/100 (Fair)

Issues Found: 8

╭─ High Severity ──────────────────────────────────────────────╮
│ Line 5: "delve" - AI vocabulary                              │
│   → Replace with: explore, examine, look at                  │
│                                                              │
│ Line 12: "plays a pivotal role" - Puffery pattern            │
│   → State the specific impact instead                        │
╰──────────────────────────────────────────────────────────────╯

╭─ Medium Severity ────────────────────────────────────────────╮
│ Line 23: "highlighting its significance" - Superficial       │
│   → Remove -ing phrase, state significance directly          │
╰──────────────────────────────────────────────────────────────╯

Summary:
  Vocabulary issues: 3
  Puffery patterns:  2
  Superficial:       2
  Structural:        1
```

### 3. Analyze Command (Full SEO)

```python
@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--keyword", "-k", help="Primary keyword")
@click.option("--secondary", "-s", multiple=True, help="Secondary keywords")
@click.option("--title", help="Meta title")
@click.option("--description", help="Meta description")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def analyze(file: str, keyword: str, secondary: tuple, title: str, description: str, output_json: bool):
    """Full SEO analysis of content."""
```

Output:
```
╭─────────────────────────────────────────────────────────────╮
│                    SEO Analysis Report                       │
╰─────────────────────────────────────────────────────────────╯

Overall Score: 78/100 (C)
Publishing Ready: No

╭─ Category Scores ────────────────────────────────────────────╮
│ Human Writing    [████████░░]  80/100  (×0.25 = 20.0)       │
│ Keywords         [███████░░░]  72/100  (×0.20 = 14.4)       │
│ Readability      [████████░░]  85/100  (×0.15 = 12.8)       │
│ Content          [█████████░]  90/100  (×0.15 = 13.5)       │
│ Meta             [██████░░░░]  60/100  (×0.15 =  9.0)       │
│ Structure        [████████░░]  80/100  (×0.10 =  8.0)       │
╰──────────────────────────────────────────────────────────────╯

╭─ Critical Issues ────────────────────────────────────────────╮
│ • Meta description missing                                   │
│ • Keyword density too low (0.8%, target: 1.5%)               │
╰──────────────────────────────────────────────────────────────╯

╭─ Warnings ───────────────────────────────────────────────────╮
│ • 3 AI vocabulary words detected                             │
│ • Keyword missing from first 100 words                       │
╰──────────────────────────────────────────────────────────────╯

Word Count: 2,450
Reading Level: Grade 9
```

### 4. Readability Command

```python
@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True)
def readability(file: str, output_json: bool):
    """Analyze content readability."""
```

### 5. Keywords Command

```python
@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--keyword", "-k", required=True, help="Primary keyword")
@click.option("--secondary", "-s", multiple=True, help="Secondary keywords")
@click.option("--target-density", "-d", default=1.5, help="Target density %")
@click.option("--json", "output_json", is_flag=True)
def keywords(file: str, keyword: str, secondary: tuple, target_density: float, output_json: bool):
    """Analyze keyword usage."""
```

### 6. Entry Point

In `pyproject.toml`:
```toml
[project.scripts]
turboseo = "turboseo.cli.main:cli"
```

### 7. Rich Styling

Use Rich for:
- Progress spinners during analysis
- Colored output (green=good, yellow=warning, red=error)
- Tables for data
- Panels for sections
- Syntax highlighting for code/markdown

### 8. JSON Output

All commands support `--json` for machine-readable output:
```json
{
  "score": 72,
  "grade": "C",
  "issues": [...],
  "recommendations": [...]
}
```

## Tests

Create `tests/test_cli.py`:

1. Test each command with sample files
2. Test JSON output format
3. Test error handling (missing file, invalid options)
4. Test Rich output formatting

## Acceptance Criteria

- [ ] All commands work
- [ ] Rich output looks good in terminal
- [ ] JSON output is valid and complete
- [ ] Error messages are helpful
- [ ] `--help` shows clear documentation
- [ ] Exit codes are correct (0=success, 1=error)
