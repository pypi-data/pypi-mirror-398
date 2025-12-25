# /write

Write an SEO-optimized article that sounds human.

## Instructions

1. If a research brief exists in `research/`, use it. Otherwise, do quick research first.

2. Write the article following these rules:

### CRITICAL: Human Writing Rules

**Words to NEVER use:**
delve, tapestry, vibrant, pivotal, crucial, intricate, foster, garner, underscore, showcase, testament, leverage, robust, seamless, cutting-edge, groundbreaking, realm, embark, beacon, paramount, commendable, meticulous, ever-evolving, game-changer, multifaceted, comprehensive, myriad, plethora, holistic, synergy

**Patterns to NEVER use:**
- "plays a pivotal role"
- "stands as a testament"
- "rich tapestry of"
- "nestled in"
- "continues to captivate"
- "In conclusion, ..."
- "Despite challenges, X continues to..."
- ", highlighting the importance of..."
- ", underscoring the need for..."
- "Not only... but also..."
- "It is important to note that..."

**Instead:**
- Be specific, not vague
- Use concrete examples and numbers
- Write like you're explaining to a smart friend
- Be direct - cut the fluff
- Short sentences are fine
- State things plainly

### SEO Requirements

- Include primary keyword in H1
- Include keyword in first 100 words
- Include keyword in 2-3 H2 headings (naturally)
- Include keyword in conclusion
- Target 1-2% keyword density
- 2000-3000 words
- 4-6 H2 sections minimum
- Include relevant internal links if available
- Include 2-3 external authority links

3. After writing, run the human check:
   ```bash
   turboseo check drafts/{filename}.md
   ```

4. If score < 80, revise the flagged sections.

5. Save to `drafts/{topic}-{date}.md`

## Output Includes

- Full article in markdown
- Meta title (50-60 characters, include keyword)
- Meta description (150-160 characters, include keyword)
- Human writing score from the checker

## Example Usage

```
/write podcast monetization guide
/write how to start a food blog
```
