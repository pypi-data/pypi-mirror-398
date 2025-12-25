"""
Writing Standards Checker

Detects AI-sounding writing patterns based on Wikipedia's "Signs of AI Writing" guidelines.
Provides a human writing score (0-100) and specific suggestions for improvement.
"""

import re

from pydantic import BaseModel

# AI vocabulary words with penalty weights
# Higher weight = stronger AI signal
AI_VOCABULARY: dict[str, int] = {
    # High confidence AI words (weight 4-5)
    "delve": 5,
    "delving": 5,
    "tapestry": 5,
    "intricacies": 5,
    "intricate": 4,
    "pivotal": 4,
    "crucial": 3,
    "foster": 4,
    "fostering": 4,
    "garner": 5,
    "garnered": 5,
    "underscore": 5,
    "underscores": 5,
    "underscoring": 5,
    "showcase": 4,
    "showcases": 4,
    "showcasing": 4,
    "testament": 5,
    "multifaceted": 5,
    "comprehensive": 2,
    "robust": 3,
    "seamless": 4,
    "seamlessly": 4,
    "cutting-edge": 4,
    "groundbreaking": 4,
    "realm": 4,
    "realms": 4,
    "embark": 5,
    "embarking": 5,
    "embarked": 5,
    "beacon": 5,
    "paramount": 5,
    "commendable": 4,
    "meticulous": 4,
    "meticulously": 4,
    "ever-evolving": 5,
    "game-changer": 5,
    "game-changing": 5,
    "vibrant": 3,
    "leverage": 3,
    "leveraging": 3,
    "leveraged": 3,
    "enhance": 2,
    "enhancing": 2,
    "enhanced": 2,
    "interplay": 4,
    "landscape": 2,  # Only when used abstractly
    "navigate": 2,  # Only when used metaphorically
    "navigating": 2,
    "journey": 2,  # Only when used metaphorically
    "unlock": 3,
    "unlocking": 3,
    "unveil": 4,
    "unveiling": 4,
    "spearhead": 4,
    "spearheading": 4,
    "holistic": 4,
    "synergy": 4,
    "synergies": 4,
    "paradigm": 4,
    "elevate": 3,
    "elevating": 3,
    "captivate": 4,
    "captivating": 4,
    "captivates": 4,
    "resonate": 3,
    "resonates": 3,
    "resonating": 3,
    "endeavor": 4,
    "endeavors": 4,
    "myriad": 4,
    "plethora": 4,
    "bustling": 4,
    "bespoke": 4,
    "nuanced": 3,
    "transformative": 4,
}

# Alternative suggestions for AI vocabulary
AI_VOCABULARY_ALTERNATIVES: dict[str, list[str]] = {
    "delve": ["explore", "examine", "look at", "dig into", "investigate"],
    "delving": ["exploring", "examining", "looking at", "investigating"],
    "tapestry": ["mix", "combination", "variety", "collection"],
    "intricate": ["complex", "detailed", "complicated"],
    "intricacies": ["details", "complexities", "specifics"],
    "pivotal": ["important", "key", "critical", "major"],
    "crucial": ["important", "essential", "key", "necessary"],
    "foster": ["encourage", "build", "develop", "support"],
    "fostering": ["encouraging", "building", "developing", "supporting"],
    "garner": ["get", "earn", "attract", "gain", "receive"],
    "garnered": ["got", "earned", "attracted", "gained", "received"],
    "underscore": ["show", "highlight", "demonstrate", "prove"],
    "underscores": ["shows", "highlights", "demonstrates", "proves"],
    "underscoring": ["showing", "highlighting", "demonstrating"],
    "showcase": ["show", "display", "demonstrate", "present"],
    "showcases": ["shows", "displays", "demonstrates", "presents"],
    "showcasing": ["showing", "displaying", "demonstrating"],
    "testament": ["proof", "evidence", "sign", "example"],
    "multifaceted": ["complex", "varied", "diverse"],
    "comprehensive": ["complete", "full", "thorough", "detailed"],
    "robust": ["strong", "solid", "reliable", "sturdy"],
    "seamless": ["smooth", "easy", "integrated", "effortless"],
    "seamlessly": ["smoothly", "easily", "without friction"],
    "cutting-edge": ["new", "modern", "latest", "advanced"],
    "groundbreaking": ["new", "innovative", "first", "novel"],
    "realm": ["area", "field", "space", "domain"],
    "realms": ["areas", "fields", "spaces", "domains"],
    "embark": ["start", "begin", "launch", "set out"],
    "embarking": ["starting", "beginning", "launching"],
    "embarked": ["started", "began", "launched"],
    "beacon": ["example", "model", "guide", "light"],
    "paramount": ["most important", "top priority", "essential"],
    "commendable": ["good", "impressive", "worthy", "notable"],
    "meticulous": ["careful", "detailed", "thorough", "precise"],
    "meticulously": ["carefully", "thoroughly", "precisely"],
    "ever-evolving": ["changing", "growing", "developing"],
    "game-changer": ["breakthrough", "major change", "turning point"],
    "game-changing": ["transforming", "major", "significant"],
    "vibrant": ["lively", "active", "energetic", "dynamic"],
    "leverage": ["use", "apply", "take advantage of", "utilize"],
    "leveraging": ["using", "applying", "taking advantage of"],
    "leveraged": ["used", "applied", "took advantage of"],
    "enhance": ["improve", "boost", "strengthen", "increase"],
    "enhancing": ["improving", "boosting", "strengthening"],
    "enhanced": ["improved", "boosted", "strengthened"],
    "interplay": ["interaction", "relationship", "connection"],
    "landscape": ["field", "area", "environment", "scene"],
    "navigate": ["handle", "manage", "work through", "deal with"],
    "navigating": ["handling", "managing", "working through"],
    "journey": ["process", "path", "experience", "progress"],
    "unlock": ["enable", "open up", "access", "gain"],
    "unlocking": ["enabling", "opening up", "accessing"],
    "unveil": ["reveal", "show", "introduce", "announce"],
    "unveiling": ["revealing", "showing", "introducing"],
    "spearhead": ["lead", "drive", "head", "pioneer"],
    "spearheading": ["leading", "driving", "heading"],
    "holistic": ["complete", "whole", "overall", "comprehensive"],
    "synergy": ["cooperation", "collaboration", "combined effect"],
    "synergies": ["benefits", "advantages", "combinations"],
    "paradigm": ["model", "pattern", "framework", "approach"],
    "elevate": ["raise", "improve", "boost", "lift"],
    "elevating": ["raising", "improving", "boosting"],
    "captivate": ["interest", "engage", "attract", "fascinate"],
    "captivating": ["interesting", "engaging", "attractive"],
    "captivates": ["interests", "engages", "attracts"],
    "resonate": ["connect", "appeal", "speak to"],
    "resonates": ["connects", "appeals", "speaks to"],
    "resonating": ["connecting", "appealing", "speaking to"],
    "endeavor": ["effort", "attempt", "project", "work"],
    "endeavors": ["efforts", "attempts", "projects", "works"],
    "myriad": ["many", "numerous", "countless", "various"],
    "plethora": ["many", "lots of", "abundance of", "plenty of"],
    "bustling": ["busy", "active", "lively", "crowded"],
    "bespoke": ["custom", "tailored", "custom-made", "personalized"],
    "nuanced": ["subtle", "complex", "detailed", "refined"],
    "transformative": ["changing", "significant", "major", "powerful"],
}

# Puffery patterns with penalty weights
PUFFERY_PATTERNS: list[tuple[str, int, str]] = [
    # (pattern, weight, suggestion)
    (
        r"stands?\s+as\s+a?\s*(testament|reminder|symbol|beacon)",
        10,
        "Replace with a direct statement: 'shows', 'proves', or 'demonstrates'",
    ),
    (
        r"plays?\s+a\s+(vital|significant|crucial|pivotal|key|important)\s+role",
        8,
        "State the specific impact instead of using vague importance claims",
    ),
    (
        r"(enduring|lasting|indelible)\s+(legacy|impact|mark)",
        8,
        "Be specific about what the actual impact or result was",
    ),
    (
        r"nestled\s+(in|within|among)",
        6,
        "Replace with 'located in' or simply 'in'",
    ),
    (
        r"rich\s+(tapestry|heritage|history|tradition)",
        8,
        "Replace with 'mix of', 'variety of', or describe specifically",
    ),
    (
        r"in\s+the\s+heart\s+of",
        5,
        "Replace with 'in central' or just specify the location",
    ),
    (
        r"boasts?\s+(a|an)",
        5,
        "Replace with 'has' or 'offers'",
    ),
    (
        r"continues?\s+to\s+captivate",
        8,
        "Be specific about what it does and for whom",
    ),
    (
        r"(groundbreaking|revolutionary)\s+(approach|method|solution|work|innovation)",
        8,
        "Describe what makes it new or different specifically",
    ),
    (
        r"deeply\s+rooted",
        6,
        "Be specific about the connection or origin",
    ),
    (
        r"at\s+the\s+forefront",
        5,
        "Be specific about what they lead or pioneer",
    ),
    (
        r"(stunning|breathtaking)\s+(natural\s+)?beauty",
        6,
        "Describe specific visual features instead",
    ),
    (
        r"serves?\s+as\s+a\s+(reminder|testament|symbol)",
        8,
        "Replace with 'shows', 'proves', or 'demonstrates'",
    ),
    (
        r"(world|globally)\s*-?\s*renowned",
        5,
        "Be specific about who recognizes it and why",
    ),
    (
        r"(time|battle)\s*-?\s*tested",
        4,
        "Provide specific evidence or history instead",
    ),
]

# Superficial analysis patterns (sentence-ending -ing phrases)
SUPERFICIAL_PATTERNS: list[tuple[str, int, str]] = [
    (
        r",\s*highlighting\s+(the\s+)?(importance|significance|need|value)",
        8,
        "Remove the -ing phrase and state the importance directly in a new sentence",
    ),
    (
        r",\s*emphasizing\s+(the\s+)?(importance|significance|need|value)",
        8,
        "Remove the -ing phrase and state what's emphasized directly",
    ),
    (
        r",\s*underscoring\s+(the\s+)?(importance|significance|need|value)",
        8,
        "Remove the -ing phrase and state the point directly",
    ),
    (
        r",\s*showcasing\s+(the\s+|its\s+|their\s+)?",
        6,
        "Remove the -ing phrase and describe what's shown in a new sentence",
    ),
    (
        r",\s*demonstrating\s+(the\s+|its\s+|their\s+)?",
        5,
        "Remove the -ing phrase and state the demonstration directly",
    ),
    (
        r",\s*reflecting\s+(the\s+|its\s+|their\s+)?",
        5,
        "Remove the -ing phrase and explain the connection directly",
    ),
    (
        r",\s*illustrating\s+(the\s+|its\s+|their\s+)?",
        5,
        "Remove the -ing phrase and describe the illustration directly",
    ),
    (
        r",\s*ensuring\s+",
        5,
        "Remove the -ing phrase and state what's ensured as a separate point",
    ),
    (
        r",\s*fostering\s+",
        5,
        "Remove the -ing phrase and describe how it encourages something",
    ),
    (
        r",\s*reinforcing\s+(the\s+)?(importance|significance|need|idea)",
        6,
        "Remove the -ing phrase and make the reinforcement a direct statement",
    ),
]

# Structural red flags
STRUCTURAL_PATTERNS: list[tuple[str, int, str]] = [
    (
        r"^(In\s+summary|In\s+conclusion|Overall|To\s+summarize|To\s+conclude),?\s+",
        10,
        "Remove the announcement and just conclude directly",
    ),
    (
        r"Despite\s+(its|their|the)\s+.{10,60}?,?\s*.{5,40}\s+faces?\s+(several\s+)?(challenges|obstacles)",
        12,
        "Be specific about challenges without using this formula",
    ),
    (
        r"Not\s+only\s+.{10,100}\s+but\s+(also\s+)?",
        8,
        "Simplify to 'X and Y' instead of 'Not only X but also Y'",
    ),
    (
        r"It'?s\s+not\s+just\s+about\s+.{10,60},?\s*(it'?s|but)",
        8,
        "State your point directly without the contrast setup",
    ),
    (
        r"(legacy|importance|significance)\s+.{5,30}\s+cannot\s+be\s+(overstated|understated)",
        10,
        "State the specific importance instead of claiming it can't be overstated",
    ),
    (
        r"It\s+is\s+(important|crucial|vital|essential)\s+to\s+(note|remember|consider)",
        6,
        "Just state the point directly without announcing its importance",
    ),
    (
        r"This\s+(is\s+)?where\s+.{5,30}\s+(comes?|steps?)\s+in",
        5,
        "Introduce the solution directly without this setup phrase",
    ),
]


class WritingIssue(BaseModel):
    """A single writing issue found in the content."""

    line: int
    column: int
    text: str
    category: str  # vocabulary, puffery, superficial, structural, formatting
    severity: str  # high, medium, low
    suggestion: str


class WritingStandardsResult(BaseModel):
    """Result of writing standards analysis."""

    score: int  # 0-100
    grade: str  # A, B, C, D, F
    issues: list[WritingIssue]
    summary: dict[str, int]  # Count by category
    word_count: int


def _get_line_and_column(content: str, position: int) -> tuple[int, int]:
    """Get line number and column from character position."""
    lines = content[:position].split("\n")
    line_num = len(lines)
    col_num = len(lines[-1]) + 1 if lines else 1
    return line_num, col_num


def _get_severity(weight: int) -> str:
    """Convert weight to severity level."""
    if weight >= 8:
        return "high"
    elif weight >= 4:
        return "medium"
    else:
        return "low"


def _get_grade(score: int) -> str:
    """Convert score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _check_vocabulary(content: str) -> list[WritingIssue]:
    """Check for AI vocabulary words."""
    issues = []
    content_lower = content.lower()

    for word, weight in AI_VOCABULARY.items():
        # Use word boundary matching
        pattern = r"\b" + re.escape(word) + r"\b"
        for match in re.finditer(pattern, content_lower, re.IGNORECASE):
            line, col = _get_line_and_column(content, match.start())

            # Get the actual word as it appears in the text
            actual_word = content[match.start() : match.end()]

            # Get alternatives
            alternatives = AI_VOCABULARY_ALTERNATIVES.get(
                word, ["consider a simpler alternative"]
            )
            suggestion = f"Replace with: {', '.join(alternatives[:3])}"

            issues.append(
                WritingIssue(
                    line=line,
                    column=col,
                    text=actual_word,
                    category="vocabulary",
                    severity=_get_severity(weight),
                    suggestion=suggestion,
                )
            )

    return issues


def _check_puffery(content: str) -> list[WritingIssue]:
    """Check for puffery patterns."""
    issues = []

    for pattern, weight, suggestion in PUFFERY_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line, col = _get_line_and_column(content, match.start())
            matched_text = match.group(0)

            issues.append(
                WritingIssue(
                    line=line,
                    column=col,
                    text=matched_text,
                    category="puffery",
                    severity=_get_severity(weight),
                    suggestion=suggestion,
                )
            )

    return issues


def _check_superficial(content: str) -> list[WritingIssue]:
    """Check for superficial analysis patterns."""
    issues = []

    for pattern, weight, suggestion in SUPERFICIAL_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line, col = _get_line_and_column(content, match.start())
            matched_text = match.group(0)

            issues.append(
                WritingIssue(
                    line=line,
                    column=col,
                    text=matched_text,
                    category="superficial",
                    severity=_get_severity(weight),
                    suggestion=suggestion,
                )
            )

    return issues


def _check_structural(content: str) -> list[WritingIssue]:
    """Check for structural red flags."""
    issues = []

    for pattern, weight, suggestion in STRUCTURAL_PATTERNS:
        for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
            line, col = _get_line_and_column(content, match.start())
            matched_text = match.group(0)

            issues.append(
                WritingIssue(
                    line=line,
                    column=col,
                    text=matched_text,
                    category="structural",
                    severity=_get_severity(weight),
                    suggestion=suggestion,
                )
            )

    return issues


def _check_formatting(content: str) -> list[WritingIssue]:
    """Check for formatting issues like excessive em-dashes."""
    issues = []

    # Count em-dashes
    em_dash_count = content.count("—") + content.count("--")
    word_count = len(content.split())

    if word_count > 0 and em_dash_count >= 3:  # Need at least 3 to flag
        em_dash_density = (em_dash_count / word_count) * 1000

        if em_dash_density > 5:  # More than 5 per 1000 words
            issues.append(
                WritingIssue(
                    line=1,
                    column=1,
                    text=f"{em_dash_count} em-dashes in {word_count} words",
                    category="formatting",
                    severity="medium",
                    suggestion="Reduce em-dash usage. Use commas, periods, or parentheses instead.",
                )
            )

    # Check for title case in markdown headings (## Title Case Heading)
    heading_pattern = r"^(#{2,})\s+(.+)$"
    for match in re.finditer(heading_pattern, content, re.MULTILINE):
        heading_text = match.group(2).strip()
        words = heading_text.split()

        if len(words) > 2:
            # Check if most words are capitalized (title case)
            capitalized = sum(1 for w in words if w[0].isupper() and len(w) > 3)
            if capitalized >= len(words) * 0.7:  # 70%+ capitalized
                line, col = _get_line_and_column(content, match.start())
                issues.append(
                    WritingIssue(
                        line=line,
                        column=col,
                        text=heading_text,
                        category="formatting",
                        severity="low",
                        suggestion="Use sentence case for headings instead of title case",
                    )
                )

    return issues


def analyze_writing_standards(content: str, strict: bool = False) -> WritingStandardsResult:
    """
    Analyze content for AI writing patterns.

    Args:
        content: The text to analyze
        strict: If True, use stricter thresholds

    Returns:
        WritingStandardsResult with score, issues, and suggestions
    """
    if not content or not content.strip():
        return WritingStandardsResult(
            score=100,
            grade="A",
            issues=[],
            summary={},
            word_count=0,
        )

    # Collect all issues
    issues: list[WritingIssue] = []
    issues.extend(_check_vocabulary(content))
    issues.extend(_check_puffery(content))
    issues.extend(_check_superficial(content))
    issues.extend(_check_structural(content))
    issues.extend(_check_formatting(content))

    # Sort by line number
    issues.sort(key=lambda x: (x.line, x.column))

    # Calculate score
    score = 100
    for issue in issues:
        if issue.severity == "high":
            score -= 5 if strict else 4
        elif issue.severity == "medium":
            score -= 3 if strict else 2
        else:
            score -= 2 if strict else 1

    score = max(0, score)

    # Create summary
    summary: dict[str, int] = {}
    for issue in issues:
        summary[issue.category] = summary.get(issue.category, 0) + 1

    word_count = len(content.split())

    return WritingStandardsResult(
        score=score,
        grade=_get_grade(score),
        issues=issues,
        summary=summary,
        word_count=word_count,
    )
