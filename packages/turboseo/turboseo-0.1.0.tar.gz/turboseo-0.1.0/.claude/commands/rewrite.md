# /rewrite

Rewrite content to sound more human and less AI-generated.

## Instructions

1. First, analyze the content:
   ```bash
   turboseo check $ARGUMENTS
   ```

2. For each issue found:
   - Show the original problematic text
   - Explain why it sounds AI-generated
   - Provide a rewritten version that sounds human

3. Apply all fixes and present the full rewritten content.

4. Run the checker again to verify improvement:
   ```bash
   turboseo check {rewritten-file}
   ```

5. Target score: 85+

## Rewriting Rules

### Replace AI Vocabulary
| AI Word | Human Alternatives |
|---------|-------------------|
| delve | explore, look at, examine, dig into |
| tapestry | mix, combination, variety |
| vibrant | lively, active, busy |
| pivotal | important, key, main |
| crucial | important, essential, key |
| intricate | complex, detailed, complicated |
| foster | encourage, build, develop |
| garner | get, earn, attract |
| underscore | show, highlight, prove |
| showcase | show, display, feature |
| testament | proof, evidence, sign |
| leverage | use, apply, take advantage of |
| robust | strong, solid, reliable |
| seamless | smooth, easy, simple |
| groundbreaking | new, innovative, first |
| realm | area, field, space |
| embark | start, begin, launch |
| beacon | example, model, guide |
| paramount | most important, top priority |
| meticulous | careful, detailed, thorough |

### Fix AI Patterns
| AI Pattern | Human Alternative |
|------------|-------------------|
| "plays a pivotal role in" | State the specific impact directly |
| "stands as a testament to" | "shows", "proves", "demonstrates" |
| "rich tapestry of" | "mix of", "variety of", just describe it |
| "nestled in" | "located in", "in" |
| "continues to captivate" | Be specific about what it does |
| "In conclusion" | Just conclude - don't announce it |
| ", highlighting..." | State the point in a new sentence |
| ", underscoring..." | Make it a direct statement |
| "Not only... but also" | "X and Y" or two sentences |

### Style Fixes
- Break long sentences into shorter ones
- Cut unnecessary words
- Replace passive voice with active
- Remove hedging ("It could be argued that...")
- Add specific examples instead of vague claims

## Example Usage

```
/rewrite drafts/article.md
/rewrite content/old-blog-post.md
```
