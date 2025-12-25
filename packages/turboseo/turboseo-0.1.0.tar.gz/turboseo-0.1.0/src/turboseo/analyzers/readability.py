"""
Readability Analyzer

Analyzes content readability using multiple metrics including Flesch Reading Ease,
grade levels, sentence structure, and passive voice detection.
"""

import re

import textstat
from pydantic import BaseModel

# Common transition words/phrases
TRANSITION_WORDS = {
    # Addition
    "additionally", "also", "and", "besides", "furthermore", "in addition",
    "moreover", "plus", "too", "what's more",
    # Contrast
    "although", "but", "however", "in contrast", "instead", "nevertheless",
    "nonetheless", "on the other hand", "still", "yet", "whereas", "while",
    # Cause/Effect
    "accordingly", "as a result", "because", "consequently", "due to",
    "hence", "since", "so", "therefore", "thus",
    # Time
    "after", "afterward", "before", "currently", "during", "eventually",
    "finally", "first", "formerly", "immediately", "later", "meanwhile",
    "next", "now", "previously", "simultaneously", "soon", "subsequently",
    "then", "until", "when", # Example
    "for example", "for instance", "in particular", "namely", "specifically",
    "such as", "to illustrate",
    # Emphasis
    "above all", "certainly", "clearly", "especially", "importantly",
    "in fact", "indeed", "most importantly", "of course", "particularly",
    "significantly", "surely", "undoubtedly",
    # Conclusion
    "all in all", "briefly", "in brief", "in short", "overall",
    "to sum up", "ultimately",
    # Similarity
    "equally", "in the same way", "likewise", "similarly",
}

# Common irregular past participles for passive voice detection
IRREGULAR_PARTICIPLES = (
    "written|done|made|seen|known|taken|given|found|shown|thought|felt|become|"
    "thrown|won|begun|broken|chosen|driven|eaten|fallen|forgotten|frozen|"
    "gotten|gone|grown|hidden|ridden|risen|spoken|stolen|sworn|torn|worn|"
    "born|bought|brought|built|caught|cut|dealt|drawn|drunk|fed|fought|"
    "fled|flown|forgiven|held|hit|hurt|kept|left|lent|let|lost|met|paid|"
    "put|read|run|said|sat|set|sold|sent|shot|shut|slept|spent|split|"
    "spread|stood|struck|swept|taught|told|understood|woken|written"
)

# Passive voice indicators
PASSIVE_PATTERNS = [
    rf"\b(is|are|was|were|been|being|be)\s+(\w+ed|{IRREGULAR_PARTICIPLES})\b",
    rf"\b(has|have|had)\s+been\s+(\w+ed|{IRREGULAR_PARTICIPLES})\b",
    rf"\b(will|would|could|should|might|may|must)\s+be\s+(\w+ed|{IRREGULAR_PARTICIPLES})\b",
]


class ReadabilityResult(BaseModel):
    """Result of readability analysis."""

    score: int  # 0-100 overall readability score
    grade: str  # A, B, C, D, F

    # Core metrics
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    smog_index: float
    automated_readability_index: float

    # Structure
    avg_sentence_length: float
    avg_paragraph_length: float
    sentence_count: int
    paragraph_count: int
    long_sentence_count: int  # >25 words
    very_long_sentence_count: int  # >35 words

    # Complexity
    passive_voice_ratio: float
    passive_voice_count: int
    complex_word_ratio: float
    transition_word_count: int

    # Word stats
    word_count: int
    character_count: int

    # Recommendations
    recommendations: list[str]
    status: str  # excellent, good, needs_improvement, poor


def _split_sentences(content: str) -> list[str]:
    """Split content into sentences."""
    # Handle common abbreviations to avoid false splits
    content = re.sub(r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr)\.", r"\1<DOT>", content)
    content = re.sub(r"\b(e\.g|i\.e|etc|vs|fig|no)\.", r"\1<DOT>", content, flags=re.I)

    # Split on sentence-ending punctuation
    sentences = re.split(r"[.!?]+\s+", content)

    # Restore dots and clean up
    sentences = [s.replace("<DOT>", ".").strip() for s in sentences if s.strip()]

    return sentences


def _split_paragraphs(content: str) -> list[str]:
    """Split content into paragraphs."""
    # Split on double newlines or multiple newlines
    paragraphs = re.split(r"\n\s*\n", content)
    # Filter out empty paragraphs and strip markdown headings for counting
    return [p.strip() for p in paragraphs if p.strip() and not p.strip().startswith("#")]


def _count_passive_voice(content: str) -> int:
    """Count passive voice constructions."""
    count = 0
    for pattern in PASSIVE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        count += len(matches)
    return count


def _count_transition_words(content: str) -> int:
    """Count transition words and phrases."""
    content_lower = content.lower()
    count = 0

    # Sort by length (longest first) to match phrases before single words
    sorted_transitions = sorted(TRANSITION_WORDS, key=len, reverse=True)

    for word in sorted_transitions:
        # Use word boundaries for single words, looser matching for phrases
        if " " in word:
            pattern = re.escape(word)
        else:
            pattern = r"\b" + re.escape(word) + r"\b"

        matches = re.findall(pattern, content_lower)
        count += len(matches)

    return count


def _count_complex_words(content: str) -> int:
    """Count words with 3+ syllables (complex words)."""
    words = re.findall(r"\b[a-zA-Z]+\b", content)
    complex_count = 0

    for word in words:
        if textstat.syllable_count(word) >= 3:
            complex_count += 1

    return complex_count


def _calculate_score(
    flesch: float,
    grade: float,
    avg_sentence_len: float,
    very_long_count: int,
    passive_ratio: float,
    avg_para_len: float,
) -> int:
    """Calculate overall readability score based on metrics."""
    score = 100

    # Flesch Reading Ease scoring
    if flesch < 30:
        score -= 30  # Very difficult
    elif flesch < 50:
        score -= 20  # Difficult
    elif flesch < 60:
        score -= 10  # Fairly difficult
    elif flesch <= 70:
        score -= 0  # Optimal
    elif flesch > 80:
        score -= 5  # Too easy for most content

    # Grade Level scoring
    if grade < 6:
        score -= 10  # Too simple
    elif grade < 8:
        score -= 5  # Slightly simple
    elif grade <= 10:
        score -= 0  # Optimal
    elif grade <= 12:
        score -= 10  # Slightly complex
    else:
        score -= 20  # Too complex

    # Sentence Length scoring
    if avg_sentence_len > 30:
        score -= 20
    elif avg_sentence_len > 25:
        score -= 10
    elif avg_sentence_len > 20:
        score -= 5

    # Very Long Sentences penalty
    score -= min(very_long_count * 3, 15)  # Cap at -15

    # Passive Voice scoring
    if passive_ratio > 0.30:
        score -= 10
    elif passive_ratio > 0.20:
        score -= 5

    # Paragraph Length scoring
    if avg_para_len > 6:
        score -= 10
    elif avg_para_len > 4:
        score -= 5

    return max(0, min(100, score))


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


def _get_status(score: int) -> str:
    """Get status description based on score."""
    if score >= 90:
        return "excellent"
    elif score >= 80:
        return "good"
    elif score >= 60:
        return "needs_improvement"
    else:
        return "poor"


def _generate_recommendations(
    flesch: float,
    grade: float,
    avg_sentence_len: float,
    long_count: int,
    very_long_count: int,
    passive_ratio: float,
    passive_count: int,
    avg_para_len: float,
    transition_count: int,
    word_count: int,
) -> list[str]:
    """Generate specific, actionable recommendations."""
    recommendations = []

    # Flesch Reading Ease recommendations
    if flesch < 30:
        recommendations.append(
            f"Reading ease is {flesch:.0f} (very difficult). "
            "Simplify vocabulary and shorten sentences. Target: 60-70."
        )
    elif flesch < 50:
        recommendations.append(
            f"Reading ease is {flesch:.0f} (difficult). "
            "Use simpler words and break up complex sentences. Target: 60-70."
        )
    elif flesch < 60:
        recommendations.append(
            f"Reading ease is {flesch:.0f} (fairly difficult). "
            "Slightly simplify for broader audience. Target: 60-70."
        )

    # Grade Level recommendations
    if grade > 12:
        recommendations.append(
            f"Grade level is {grade:.1f} (college level). "
            "Simplify for a general audience. Target: 8-10th grade."
        )
    elif grade > 10:
        recommendations.append(
            f"Grade level is {grade:.1f} (slightly complex). "
            "Consider simplifying for wider accessibility. Target: 8-10th grade."
        )
    elif grade < 6:
        recommendations.append(
            f"Grade level is {grade:.1f} (very simple). "
            "Content may lack depth for adult readers."
        )

    # Sentence length recommendations
    if avg_sentence_len > 25:
        recommendations.append(
            f"Average sentence length is {avg_sentence_len:.0f} words. "
            "Break up sentences for better readability. Target: 15-20 words."
        )
    elif avg_sentence_len > 20:
        recommendations.append(
            f"Average sentence length is {avg_sentence_len:.0f} words. "
            "Consider shortening some sentences. Target: 15-20 words."
        )

    # Long sentences
    if very_long_count > 0:
        recommendations.append(
            f"{very_long_count} sentence{'s' if very_long_count != 1 else ''} "
            f"exceed{'s' if very_long_count == 1 else ''} 35 words. "
            "Split these into multiple sentences."
        )
    elif long_count > 3:
        recommendations.append(
            f"{long_count} sentences exceed 25 words. "
            "Consider breaking up some of these."
        )

    # Passive voice
    if passive_ratio > 0.20:
        pct = passive_ratio * 100
        recommendations.append(
            f"Passive voice at {pct:.0f}% ({passive_count} instances). "
            "Convert to active voice where possible. Target: under 20%."
        )

    # Paragraph length
    if avg_para_len > 5:
        recommendations.append(
            f"Average paragraph length is {avg_para_len:.1f} sentences. "
            "Break up long paragraphs for scannability. Target: 2-4 sentences."
        )

    # Transition words
    if word_count > 100:
        transition_ratio = transition_count / (word_count / 100)
        if transition_ratio < 2:
            recommendations.append(
                f"Only {transition_count} transition words found. "
                "Add more transitions to improve flow (e.g., however, therefore, additionally)."
            )

    return recommendations


def analyze_readability(content: str) -> ReadabilityResult:
    """
    Comprehensive readability analysis.

    Args:
        content: Text to analyze

    Returns:
        ReadabilityResult with scores, metrics, and recommendations
    """
    # Handle empty content
    if not content or not content.strip():
        return ReadabilityResult(
            score=100,
            grade="A",
            flesch_reading_ease=100.0,
            flesch_kincaid_grade=0.0,
            gunning_fog=0.0,
            smog_index=0.0,
            automated_readability_index=0.0,
            avg_sentence_length=0.0,
            avg_paragraph_length=0.0,
            sentence_count=0,
            paragraph_count=0,
            long_sentence_count=0,
            very_long_sentence_count=0,
            passive_voice_ratio=0.0,
            passive_voice_count=0,
            complex_word_ratio=0.0,
            transition_word_count=0,
            word_count=0,
            character_count=0,
            recommendations=[],
            status="excellent",
        )

    # Strip markdown formatting for analysis
    # Remove headers, links, images, code blocks
    clean_content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)  # Headers
    clean_content = re.sub(r"```[\s\S]*?```", "", clean_content)  # Code blocks
    clean_content = re.sub(r"`[^`]+`", "", clean_content)  # Inline code
    clean_content = re.sub(r"!\[.*?\]\(.*?\)", "", clean_content)  # Images
    clean_content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_content)  # Links
    clean_content = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", clean_content)  # Bold/italic
    clean_content = re.sub(r"^\s*[-*+]\s+", "", clean_content, flags=re.MULTILINE)  # List markers
    clean_content = re.sub(r"^\s*\d+\.\s+", "", clean_content, flags=re.MULTILINE)  # Numbered lists

    # Core metrics from textstat
    flesch = textstat.flesch_reading_ease(clean_content)
    fk_grade = textstat.flesch_kincaid_grade(clean_content)
    fog = textstat.gunning_fog(clean_content)
    smog = textstat.smog_index(clean_content)
    ari = textstat.automated_readability_index(clean_content)

    # Structure analysis
    sentences = _split_sentences(clean_content)
    paragraphs = _split_paragraphs(content)  # Use original for paragraph detection

    sentence_count = len(sentences)
    paragraph_count = len(paragraphs) if paragraphs else 1

    # Calculate sentence lengths
    sentence_lengths = [len(s.split()) for s in sentences if s]
    avg_sentence_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

    long_count = sum(1 for length in sentence_lengths if length > 25)
    very_long_count = sum(1 for length in sentence_lengths if length > 35)

    # Paragraph analysis
    para_sentence_counts = []
    for para in paragraphs:
        para_sentences = _split_sentences(para)
        if para_sentences:
            para_sentence_counts.append(len(para_sentences))

    avg_para_len = sum(para_sentence_counts) / len(para_sentence_counts) if para_sentence_counts else 0

    # Complexity analysis
    passive_count = _count_passive_voice(clean_content)
    passive_ratio = passive_count / sentence_count if sentence_count > 0 else 0

    word_count = len(clean_content.split())
    complex_count = _count_complex_words(clean_content)
    complex_ratio = complex_count / word_count if word_count > 0 else 0

    transition_count = _count_transition_words(clean_content)

    # Calculate score
    score = _calculate_score(
        flesch=flesch,
        grade=fk_grade,
        avg_sentence_len=avg_sentence_len,
        very_long_count=very_long_count,
        passive_ratio=passive_ratio,
        avg_para_len=avg_para_len,
    )

    # Generate recommendations
    recommendations = _generate_recommendations(
        flesch=flesch,
        grade=fk_grade,
        avg_sentence_len=avg_sentence_len,
        long_count=long_count,
        very_long_count=very_long_count,
        passive_ratio=passive_ratio,
        passive_count=passive_count,
        avg_para_len=avg_para_len,
        transition_count=transition_count,
        word_count=word_count,
    )

    return ReadabilityResult(
        score=score,
        grade=_get_grade(score),
        flesch_reading_ease=round(flesch, 1),
        flesch_kincaid_grade=round(fk_grade, 1),
        gunning_fog=round(fog, 1),
        smog_index=round(smog, 1),
        automated_readability_index=round(ari, 1),
        avg_sentence_length=round(avg_sentence_len, 1),
        avg_paragraph_length=round(avg_para_len, 1),
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        long_sentence_count=long_count,
        very_long_sentence_count=very_long_count,
        passive_voice_ratio=round(passive_ratio, 2),
        passive_voice_count=passive_count,
        complex_word_ratio=round(complex_ratio, 2),
        transition_word_count=transition_count,
        word_count=word_count,
        character_count=len(clean_content),
        recommendations=recommendations,
        status=_get_status(score),
    )
