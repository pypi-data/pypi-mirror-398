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

For development:

```bash
git clone https://github.com/thijs/turboseo.git
cd turboseo
pip install -e ".[dev]"
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

## Commands

| Command | Description |
|---------|-------------|
| `turboseo check <file>` | Check for AI writing patterns |
| `turboseo analyze <file>` | Full SEO analysis |
| `turboseo readability <file>` | Readability analysis |
| `turboseo keywords <file> -k <keyword>` | Keyword analysis |

## Human Writing Score

TurboSEO scores your content from 0-100:

| Score | Grade | Meaning |
|-------|-------|---------|
| 90-100 | A | Sounds human |
| 80-89 | B | Minor AI tells |
| 70-79 | C | Noticeable AI patterns |
| 60-69 | D | Obvious AI writing |
| <60 | F | Clearly AI-generated |

## Documentation

- [Getting Started](docs/getting-started.md)
- [Human Writing Rules](docs/human-writing-rules.md)
- [CLI Reference](docs/cli-reference.md)
- [Claude Code Setup](docs/claude-code-setup.md)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
