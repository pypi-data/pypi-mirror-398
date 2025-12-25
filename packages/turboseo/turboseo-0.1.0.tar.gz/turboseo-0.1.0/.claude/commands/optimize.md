# /optimize

Final optimization pass before publishing.

## Instructions

1. Run full SEO analysis:
   ```bash
   turboseo analyze $ARGUMENTS
   ```

2. Check human writing score:
   ```bash
   turboseo check {file}
   ```

3. Review all results and create an optimization checklist.

4. For each issue found, either:
   - Fix it directly in the content
   - Explain why it can be left as-is

5. Generate meta title and description options (3 each).

6. Create optimization report at `drafts/optimization-report-{date}.md`

## Optimization Report Format

```markdown
# Optimization Report

**File:** {filename}
**Date:** {YYYY-MM-DD}

## Publishing Readiness

**Status:** Ready / Not Ready
**Overall Score:** {X}/100 ({Grade})

## Scores Breakdown

| Category | Score | Status |
|----------|-------|--------|
| Human Writing | {X} | {OK/Needs Work} |
| Keywords | {X} | {OK/Needs Work} |
| Readability | {X} | {OK/Needs Work} |
| Content | {X} | {OK/Needs Work} |
| Meta | {X} | {OK/Needs Work} |
| Structure | {X} | {OK/Needs Work} |

## Issues Fixed

- [x] {issue 1}
- [x] {issue 2}

## Remaining Issues

- [ ] {issue if any}

## Meta Options

### Title Options
1. "{title 1}" ({X} chars)
2. "{title 2}" ({X} chars)
3. "{title 3}" ({X} chars)

**Recommended:** Option {X}

### Description Options
1. "{desc 1}" ({X} chars)
2. "{desc 2}" ({X} chars)
3. "{desc 3}" ({X} chars)

**Recommended:** Option {X}

## Final Checklist

- [ ] Human writing score 80+
- [ ] Keyword in H1
- [ ] Keyword in first 100 words
- [ ] Keyword in conclusion
- [ ] 4+ H2 sections
- [ ] Meta title 50-60 chars
- [ ] Meta description 150-160 chars
- [ ] No critical issues
```

## Example Usage

```
/optimize drafts/article.md -k "podcast monetization"
```
