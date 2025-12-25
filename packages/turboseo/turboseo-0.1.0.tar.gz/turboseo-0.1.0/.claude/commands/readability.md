# /readability

Analyze content readability.

## Instructions

1. Run the readability analyzer:
   ```bash
   turboseo readability $ARGUMENTS
   ```

2. Explain what each metric means:
   - Flesch Reading Ease (60-70 is ideal for web content)
   - Grade Level (8-10 is ideal for general audience)
   - Average sentence length
   - Passive voice percentage

3. Identify specific issues:
   - Sentences that are too long (quote them)
   - Complex vocabulary that could be simplified
   - Sections that need breaking up

4. Provide rewrite suggestions for problem areas.

## Target Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Flesch Reading Ease | 60-70 | Easy to read but not dumbed down |
| Grade Level | 8-10 | Accessible to most adults |
| Avg Sentence Length | 15-20 words | Easy to scan |
| Passive Voice | <20% | More engaging |

## Example Usage

```
/readability drafts/article.md
/readability content/technical-guide.md
```
