# /research

Research a topic for SEO content creation.

## Instructions

1. Search for the topic using web search
2. Analyze top ranking pages for:
   - Primary keyword opportunities
   - Secondary/related keywords
   - Content gaps (what competitors miss)
   - Questions people ask (People Also Ask, forums, Reddit)
   - Typical word count of top results

3. Create a research brief saved to `research/brief-{topic}-{date}.md`

## Output Format

```markdown
# Research Brief: {Topic}

Date: {YYYY-MM-DD}

## Keywords

### Primary Keyword
- **Keyword:** {main keyword}
- **Search Intent:** {informational/transactional/navigational}

### Secondary Keywords
- {keyword 1}
- {keyword 2}
- {keyword 3}

## Competitor Analysis

| Rank | Title | Word Count | Key Sections |
|------|-------|------------|--------------|
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

## Content Gaps
Things competitors don't cover well:
- {gap 1}
- {gap 2}

## Questions to Answer
From People Also Ask and forums:
- {question 1}
- {question 2}
- {question 3}

## Recommended Outline

### H1: {Title}

### H2: {Section 1}
- Key points to cover

### H2: {Section 2}
- Key points to cover

...

## Target Metrics
- **Word count:** {X} words (competitor median + 20%)
- **H2 sections:** {X}
- **Reading level:** Grade 8-10
```

## Example Usage

```
/research podcast monetization strategies
/research how to start a blog in 2024
```
