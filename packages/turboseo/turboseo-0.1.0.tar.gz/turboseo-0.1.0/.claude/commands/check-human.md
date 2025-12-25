# /check-human

Check if content sounds human (not AI-generated).

## Instructions

1. Run the Python checker:
   ```bash
   turboseo check $ARGUMENTS
   ```

2. Review the output and explain:
   - Overall score and what it means
   - Each issue found (grouped by severity)
   - How to fix the issues with specific examples

3. Score interpretation:
   - 90-100: Excellent - sounds human
   - 80-89: Good - minor AI patterns
   - 70-79: Fair - noticeable AI patterns
   - 60-69: Poor - significant AI patterns
   - Below 60: Fails - clearly AI-generated

4. If score < 80, offer to rewrite problematic sections to sound more human.

## Example Usage

```
/check-human drafts/article.md
/check-human content/blog-post.md --strict
```
