# /analyze

Run full SEO analysis on content.

## Instructions

1. Ask the user for any missing information:
   - Primary keyword (required for keyword analysis)
   - Meta title (optional)
   - Meta description (optional)

2. Run the Python analyzer:
   ```bash
   turboseo analyze $ARGUMENTS
   ```

3. Present results with clear explanations:
   - Overall score and grade (A-F)
   - Publishing readiness status
   - Category breakdown with what each score means
   - Critical issues (must fix before publishing)
   - Warnings (should fix for better performance)
   - Suggestions (nice to have improvements)

4. Prioritize fixes by impact - tell the user what to fix first.

5. If human writing score is low, offer to help rewrite problematic sections.

## Example Usage

```
/analyze drafts/article.md -k "podcast monetization"
/analyze content/guide.md -k "SEO tips" --title "10 SEO Tips for 2024" --description "Learn proven SEO strategies..."
```
