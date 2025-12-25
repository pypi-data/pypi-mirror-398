# Prompt 07: Claude Code Workspace Setup

## Task

Set up the Claude Code workspace with slash commands and agents that integrate with the Python modules.

## Requirements

### 1. Directory Structure

```
.claude/
├── commands/
│   ├── research.md
│   ├── write.md
│   ├── rewrite.md
│   ├── analyze.md
│   ├── check-human.md
│   └── optimize.md
└── agents/
    ├── content-analyzer.md
    ├── seo-optimizer.md
    ├── human-writer.md
    ├── meta-creator.md
    └── keyword-mapper.md
```

### 2. Slash Commands

#### `/research` - Research a topic
```markdown
# /research

Research a topic for SEO content creation.

## Instructions

1. Search for the topic using web search
2. Analyze top 10 ranking pages
3. Identify:
   - Primary keyword opportunities
   - Secondary keywords
   - Content gaps
   - Questions people ask
   - Recommended word count (based on competitors)

4. Create a research brief at `research/brief-{topic}-{date}.md`

## Output Format

```markdown
# Research Brief: {Topic}

## Keywords
- Primary: {keyword}
- Secondary: {list}

## Top Competitors
| Rank | URL | Word Count | Key Sections |
|------|-----|------------|--------------|

## Content Gaps
- {gaps competitors don't cover well}

## Questions to Answer
- {from People Also Ask, forums, etc}

## Recommended Outline
1. {H2}
2. {H2}
...

## Target Metrics
- Word count: {X} (competitor median + 20%)
- H2 sections: {X}
```
```

#### `/write` - Write an article
```markdown
# /write

Write an SEO-optimized article that sounds human.

## Instructions

1. If research brief exists, use it. Otherwise, do quick research first.

2. Write the article following these rules:

### CRITICAL: Human Writing Rules
- NO AI vocabulary: delve, tapestry, vibrant, pivotal, crucial, intricate, foster, garner, underscore, showcase, testament, leverage, robust, seamless, cutting-edge, groundbreaking, realm, embark, beacon, paramount, commendable, meticulous, ever-evolving, game-changer
- NO puffery: "plays a pivotal role", "stands as a testament", "rich tapestry", "nestled in", "continues to captivate"
- NO superficial analysis: Don't end sentences with ", highlighting...", ", emphasizing...", ", underscoring..."
- NO structural clichés: "In conclusion", "Despite its challenges...", "Not only... but also"
- Use specific examples, not vague claims
- Write like you're explaining to a smart friend
- Be direct. Cut the fluff.

### SEO Requirements
- Include primary keyword in H1, first 100 words, 2-3 H2s, conclusion
- Target 1-2% keyword density
- 2000-3000 words
- 4-6 H2 sections
- Include internal links (check context/internal-links-map.md)
- Include 2-3 external authority links

3. After writing, run the human check:
   ```bash
   turboseo check drafts/{filename}.md
   ```

4. If score < 80, revise using the human-writer agent.

5. Save to `drafts/{topic}-{date}.md`

## Output includes
- Full article in markdown
- Meta title (50-60 chars)
- Meta description (150-160 chars)
- Human writing score
```

#### `/check-human` - Check human writing score
```markdown
# /check-human

Check if content sounds human (not AI-generated).

## Instructions

1. Run the Python checker:
   ```bash
   turboseo check {file}
   ```

2. Review the output and explain:
   - Overall score and what it means
   - Each issue found
   - How to fix the issues

3. If score < 80, offer to run the human-writer agent to fix issues.
```

#### `/analyze` - Full SEO analysis
```markdown
# /analyze

Run full SEO analysis on content.

## Instructions

1. Run the Python analyzer:
   ```bash
   turboseo analyze {file} --keyword "{keyword}" --title "{title}" --description "{description}"
   ```

2. Present results with explanations:
   - Overall score and grade
   - Category breakdown
   - Critical issues (must fix)
   - Warnings (should fix)
   - Suggestions (nice to have)

3. Prioritize fixes by impact.
```

#### `/optimize` - Final optimization pass
```markdown
# /optimize

Final optimization before publishing.

## Instructions

1. Run full analysis: `/analyze {file}`

2. Check human score: `/check-human {file}`

3. Run all agents:
   - seo-optimizer
   - meta-creator
   - keyword-mapper

4. Create optimization report at `drafts/optimization-report-{topic}-{date}.md`

5. Report includes:
   - Publishing readiness (Yes/No)
   - Final scores
   - Remaining issues
   - Meta element options
```

### 3. Agents

#### `human-writer.md` - Rewrite to sound human
```markdown
# Human Writer Agent

You are an editor who makes AI-sounding content sound human.

## Your Task

Take content that has been flagged as AI-sounding and rewrite it to sound natural and human.

## Rules

### Words to Replace
| AI Word | Human Alternatives |
|---------|-------------------|
| delve | explore, look at, examine, dig into |
| tapestry | mix, combination, variety |
| vibrant | lively, active, energetic |
| pivotal | important, key, critical |
| crucial | important, essential, key |
| intricate | complex, detailed, complicated |
| foster | encourage, build, develop |
| garner | get, earn, attract |
| underscore | show, highlight, prove |
| showcase | show, display, demonstrate |
| testament | proof, evidence, sign |
| leverage | use, apply, take advantage of |
| robust | strong, solid, reliable |
| seamless | smooth, easy, integrated |
| groundbreaking | new, innovative, first |
| realm | area, field, world |
| embark | start, begin, launch |
| beacon | example, model, guide |
| paramount | most important, top priority |
| meticulous | careful, detailed, thorough |

### Patterns to Fix
| AI Pattern | Human Alternative |
|------------|-------------------|
| "plays a pivotal role in" | State the specific impact |
| "stands as a testament to" | "shows", "proves" |
| "rich tapestry of" | "mix of", "variety of" |
| "nestled in" | "located in", "in" |
| "continues to captivate" | Be specific about what it does |
| "In conclusion" | Just conclude, don't announce it |
| "Despite challenges, X continues to" | Be specific about what challenges and how |
| ", highlighting the importance of" | State why it's important directly |
| ", underscoring the need for" | State the need directly |

### Style Guidelines
1. Be specific, not vague
2. Use concrete examples
3. Write shorter sentences
4. Cut unnecessary words
5. Avoid passive voice
6. Don't hedge ("It could be argued that...")
7. Be direct

## Process

1. Identify all AI tells in the content
2. For each issue:
   - Show the original text
   - Explain why it sounds AI
   - Provide the rewritten version
3. Present the full rewritten content
4. Run `turboseo check` to verify improvement
```

#### `seo-optimizer.md`
```markdown
# SEO Optimizer Agent

Analyze content for SEO and provide specific improvements.

## Analysis Areas

1. **Keyword Optimization**
   - Is primary keyword in H1?
   - Is it in first 100 words?
   - How many H2s contain it?
   - What's the density?

2. **Content Structure**
   - H1/H2/H3 hierarchy
   - Section balance
   - Paragraph length

3. **Internal Linking**
   - Check context/internal-links-map.md
   - Suggest 3-5 relevant internal links
   - Provide anchor text options

4. **External Links**
   - Are there 2-3 authority links?
   - Are they relevant?

5. **Featured Snippet Opportunities**
   - Could any section answer a question directly?
   - Should we add a definition box?
   - Would a list format help?

## Output

For each area, provide:
- Current state
- Score (1-10)
- Specific improvements with examples
```

#### `meta-creator.md`
```markdown
# Meta Creator Agent

Create compelling meta titles and descriptions.

## Requirements

### Meta Title
- 50-60 characters
- Include primary keyword
- Be compelling (not just descriptive)
- Avoid AI-sounding language

### Meta Description
- 150-160 characters
- Include primary keyword
- Include a call to action
- Be specific about value

## Output

Provide 3 options for each, with:
- The text
- Character count
- Why it works
- SERP preview

## Examples

### Good Meta Titles
- "How to Start a Podcast in 2024 (Step-by-Step Guide)" - 52 chars
- "Podcast Hosting: 7 Platforms Compared [2024 Update]" - 51 chars

### Bad Meta Titles (AI-sounding)
- "The Ultimate Comprehensive Guide to Podcast Mastery" ❌
- "Unlocking the Power of Podcasting for Your Business" ❌

### Good Meta Descriptions
- "Learn how to start a podcast from scratch. We cover equipment, software, hosting, and launching—no experience needed. Free checklist included." - 156 chars

### Bad Meta Descriptions (AI-sounding)
- "Embark on your podcasting journey with our comprehensive guide. Discover the intricate world of podcast creation and unlock your potential." ❌
```

### 4. Context Files

Create templates in `context/`:

#### `context/human-writing-rules.md`
```markdown
# Human Writing Rules

This document defines the writing standards for TurboSEO content.

## The Goal

Write content that:
1. Sounds like a knowledgeable human wrote it
2. Passes AI detection tools
3. Is engaging and useful

## Words to Avoid

[Full list from writing_standards.py]

## Patterns to Avoid

[Full list of puffery and superficial patterns]

## Instead, Do This

1. Be specific, not vague
2. Use real examples
3. Write like you're explaining to a friend
4. Cut unnecessary words
5. State things directly
```

## Acceptance Criteria

- [ ] All slash commands created
- [ ] All agents created
- [ ] Commands integrate with Python CLI
- [ ] human-writer agent effectively fixes AI tells
- [ ] Context files document all rules
