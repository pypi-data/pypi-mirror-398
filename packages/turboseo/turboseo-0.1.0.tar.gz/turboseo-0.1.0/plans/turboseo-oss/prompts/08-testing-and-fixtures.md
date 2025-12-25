# Prompt 08: Testing and Fixtures

## Task

Create comprehensive tests and fixture files for validating the writing standards checker.

## Requirements

### 1. Test Fixtures

Create `tests/fixtures/` with samples that have known scores.

#### AI-Generated Samples (Should score <70)

**`ai_sample_1.md`** - Heavy AI vocabulary
```markdown
# The Transformative Journey of Digital Marketing Excellence

In today's ever-evolving digital landscape, businesses must delve into the intricate tapestry of online marketing strategies to thrive. Digital marketing plays a pivotal role in fostering meaningful connections between brands and their audiences, showcasing the power of authentic engagement.

## Understanding the Digital Ecosystem

The realm of digital marketing encompasses a multifaceted array of channels and techniques. From social media to content marketing, each element serves as a testament to the innovative spirit of modern business practices. Organizations that leverage these tools effectively can unlock unprecedented growth opportunities.

## The Crucial Role of Content Strategy

Content stands as a beacon of value in the crowded digital space. A robust content strategy is paramount for businesses seeking to establish thought leadership. By crafting meticulous, comprehensive resources, brands can garner trust and underscore their expertise.

## Navigating Challenges and Embracing Opportunities

Despite the challenges inherent in the digital marketing landscape, forward-thinking organizations continue to captivate audiences through groundbreaking approaches. The seamless integration of data-driven insights with creative storytelling has become a game-changer for brands worldwide.

## Conclusion

In conclusion, the journey toward digital marketing excellence requires dedication, innovation, and a deep understanding of audience needs. By embracing these principles, businesses can create an enduring legacy in their respective industries.
```

**`ai_sample_2.md`** - Puffery and superficial analysis
```markdown
# Building Community Through Social Media

Social media has emerged as a vibrant platform for community building, highlighting the importance of authentic connection in our digital age. Brands that understand this play a vital role in fostering engagement.

## The Power of Authentic Engagement

Authentic engagement serves as a testament to a brand's commitment to its audience. By showcasing genuine interactions, companies can create a rich tapestry of community connections, underscoring the value of meaningful relationships.

Community building is not just about followers—it's about creating lasting connections that drive loyalty. This approach has proven to be groundbreaking in its impact, highlighting the transformative potential of social media.

## Strategies for Success

Successful community managers understand that consistency is crucial. They delve into analytics to understand their audience, leveraging data to enhance their strategies. The seamless integration of content and engagement creates a robust foundation for growth.

Despite the challenges of algorithm changes, these strategies continue to garner positive results, demonstrating the enduring importance of community-focused approaches.
```

**`ai_sample_3.md`** - Structural red flags
```markdown
# Podcast Monetization: A Complete Guide

In the realm of podcasting, monetization stands as a pivotal concern for creators seeking to transform their passion into a sustainable venture.

## Understanding Monetization Options

Not only do podcasters have access to traditional advertising, but they can also explore innovative revenue streams. It's not just about making money—it's about creating value for your audience while building a sustainable business.

Sponsorships play a crucial role in podcast monetization, underscoring the importance of audience size and engagement metrics.

## Building Your Monetization Strategy

Despite the challenges facing independent podcasters, the industry continues to offer robust opportunities for those willing to embrace multifaceted approaches.

Key factors include:
- Audience size and engagement
- Content quality and consistency
- Strategic partnerships

## In Conclusion

In summary, podcast monetization requires a comprehensive understanding of available options and a meticulous approach to implementation. By fostering authentic connections with listeners and leveraging multiple revenue streams, podcasters can build an enduring legacy in this vibrant medium.
```

#### Human-Written Samples (Should score >85)

**`human_sample_1.md`** - Direct, specific writing
```markdown
# How to Actually Make Money From Your Podcast

Most podcasters never make a dime. Here's how to be in the minority that does.

## The Math Behind Podcast Money

Let's start with reality: you need at least 1,000 downloads per episode before most sponsors will talk to you. At that level, expect $15-25 per 1,000 downloads (CPM) for a mid-roll ad.

Do the math: 1,000 downloads × $20 CPM = $20 per episode.

That's why smart podcasters don't rely on ads alone.

## Three Revenue Streams That Work

### 1. Premium Content

Offer bonus episodes or early access for $5/month. If 2% of your listeners subscribe, that's more predictable than chasing sponsors.

### 2. Services and Products

Use your podcast as a funnel. A B2B podcast with 500 listeners can generate more revenue than a comedy show with 50,000 if those 500 are decision-makers who hire you.

### 3. Affiliate Deals

Promote tools you actually use. Podcast hosting, microphones, editing software—if you'd recommend it anyway, get paid for it.

## What Most Guides Won't Tell You

The podcasters making real money aren't the ones with the most downloads. They're the ones who picked a specific audience and solved their problems.

Stop chasing download numbers. Start asking: "Who listens to my show, and what do they need?"
```

**`human_sample_2.md`** - Conversational, practical
```markdown
# Setting Up Your First Podcast Studio (Without Going Broke)

You don't need a professional studio to start a podcast. Here's what actually matters—and what doesn't.

## The Only Equipment That Matters

### Microphone: $60-100

The Audio-Technica ATR2100x or Samson Q2U are both USB mics that sound great. Don't spend more until you've recorded 20+ episodes.

### Headphones: $20-50

Any closed-back headphones work. The Sony MDR-7506 is the industry standard, but even Apple earbuds work in a pinch.

### Recording Space: $0

Your closet. Seriously. Clothes absorb sound better than foam panels. Record in there.

## Software Setup

Audacity is free and does everything you need. Descript is $12/month if you want easier editing.

Don't buy Pro Tools. Don't buy a Shure SM7B. Don't buy a GoXLR.

Not yet.

## The Setup That Actually Sounds Good

1. Put your mic 4-6 inches from your mouth
2. Talk across the mic, not into it
3. Record in a quiet room with soft surfaces
4. Use a pop filter (or a sock over the mic—yes, really)

That's it. Everything else is optimization for later.

## Common Mistakes

- Buying expensive gear before learning to use cheap gear
- Recording in echoey rooms
- Sitting too far from the mic
- Over-processing audio in post

Get the basics right first. Upgrade when you hit a wall, not before.
```

**`human_sample_3.md`** - Expert, no-fluff style
```markdown
# Fixing Slow Page Load Times: A Developer's Checklist

Your page loads in 4 seconds. Users leave at 3. Let's fix that.

## Diagnose First

Run Lighthouse. Look at three numbers:
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Total Blocking Time (TBT)

If LCP is over 2.5s, that's your priority.

## Quick Wins (Under 30 Minutes)

### Images

90% of slow pages have image problems.

```bash
# Convert to WebP
cwebp -q 80 image.png -o image.webp
```

Add `loading="lazy"` to images below the fold. Add explicit width/height to prevent layout shift.

### Fonts

Self-host your fonts. Google Fonts adds an extra DNS lookup + connection.

Use `font-display: swap` so text shows immediately.

### Third-Party Scripts

Move analytics and chat widgets to load after the page. They don't need to block rendering.

```html
<script defer src="analytics.js"></script>
```

## If That's Not Enough

Check your server response time. If TTFB is over 200ms:
- Add caching headers
- Use a CDN
- Upgrade your hosting

Measure again. Repeat until LCP is under 2.5s.
```

### 2. Test File: `tests/test_writing_standards.py`

```python
import pytest
from pathlib import Path
from turboseo.analyzers.writing_standards import analyze_writing_standards

FIXTURES = Path(__file__).parent / "fixtures"

class TestAIVocabulary:
    def test_detects_delve(self):
        result = analyze_writing_standards("We must delve into this topic.")
        assert any(i.text == "delve" for i in result.issues)

    def test_detects_tapestry(self):
        result = analyze_writing_standards("The rich tapestry of culture.")
        assert any("tapestry" in i.text for i in result.issues)

    def test_detects_multiple_ai_words(self):
        text = "We delve into the intricate tapestry of this vibrant field."
        result = analyze_writing_standards(text)
        assert len([i for i in result.issues if i.category == "vocabulary"]) >= 3

    def test_no_false_positives_on_normal_text(self):
        text = "This article explores the history of podcasting."
        result = analyze_writing_standards(text)
        vocab_issues = [i for i in result.issues if i.category == "vocabulary"]
        assert len(vocab_issues) == 0


class TestPufferyPatterns:
    def test_detects_pivotal_role(self):
        text = "Technology plays a pivotal role in modern business."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_testament(self):
        text = "This stands as a testament to human ingenuity."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_nested_in(self):
        text = "The village, nestled in the mountains, offers views."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)


class TestSuperficialAnalysis:
    def test_detects_highlighting(self):
        text = "Sales increased 40%, highlighting the importance of marketing."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)

    def test_detects_underscoring(self):
        text = "The results were positive, underscoring our approach."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)


class TestStructuralFlags:
    def test_detects_in_conclusion(self):
        text = "In conclusion, this shows the value of planning."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_challenge_formula(self):
        text = "Despite its popularity, the platform faces several challenges."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_negative_parallelism(self):
        text = "Not only does this improve efficiency, but it also reduces costs."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)


class TestScoring:
    def test_perfect_score_for_clean_text(self):
        text = "This is a simple, clear sentence about podcasting."
        result = analyze_writing_standards(text)
        assert result.score >= 95

    def test_low_score_for_ai_heavy_text(self):
        text = """
        We must delve into the intricate tapestry of digital marketing.
        It plays a pivotal role in fostering connections.
        This stands as a testament to innovation.
        In conclusion, success is crucial.
        """
        result = analyze_writing_standards(text)
        assert result.score < 60


class TestFixtures:
    @pytest.mark.parametrize("filename", [
        "ai_sample_1.md",
        "ai_sample_2.md",
        "ai_sample_3.md",
    ])
    def test_ai_samples_score_low(self, filename):
        content = (FIXTURES / filename).read_text()
        result = analyze_writing_standards(content)
        assert result.score < 70, f"{filename} scored {result.score}, expected <70"

    @pytest.mark.parametrize("filename", [
        "human_sample_1.md",
        "human_sample_2.md",
        "human_sample_3.md",
    ])
    def test_human_samples_score_high(self, filename):
        content = (FIXTURES / filename).read_text()
        result = analyze_writing_standards(content)
        assert result.score > 85, f"{filename} scored {result.score}, expected >85"


class TestSuggestions:
    def test_provides_alternatives_for_delve(self):
        result = analyze_writing_standards("We delve into the topic.")
        issue = next(i for i in result.issues if "delve" in i.text)
        assert "explore" in issue.suggestion.lower() or "examine" in issue.suggestion.lower()

    def test_provides_fix_for_highlighting(self):
        result = analyze_writing_standards("Sales grew, highlighting success.")
        issue = next(i for i in result.issues if i.category == "superficial")
        assert issue.suggestion  # Should have a suggestion
```

### 3. Pytest Configuration

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=turboseo --cov-report=term-missing"

[tool.coverage.run]
source = ["src/turboseo"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
]
```

## Acceptance Criteria

- [ ] All fixture files created
- [ ] AI samples consistently score <70
- [ ] Human samples consistently score >85
- [ ] All test categories pass
- [ ] Coverage >90% on writing_standards.py
- [ ] Tests run in <5 seconds
