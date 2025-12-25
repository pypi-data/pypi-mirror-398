"""
Keyword Analyzer

Analyzes keyword usage, density, distribution, and provides recommendations
for SEO optimization.
"""

import re

from pydantic import BaseModel


class KeywordPlacement(BaseModel):
    """Tracks where a keyword appears in critical positions."""

    in_h1: bool
    in_first_100_words: bool
    in_conclusion: bool
    h2_count: int  # Total number of H2 headings
    h2_with_keyword: int  # Number of H2s containing the keyword


class KeywordAnalysis(BaseModel):
    """Analysis results for a single keyword."""

    keyword: str
    exact_matches: int  # Exact phrase matches
    total_occurrences: int  # All occurrences (including partial)
    density: float  # Percentage of word count
    target_density: float
    status: str  # too_low, slightly_low, optimal, slightly_high, too_high
    placements: KeywordPlacement


class StuffingRisk(BaseModel):
    """Keyword stuffing risk assessment."""

    level: str  # none, low, medium, high
    warnings: list[str]


class SectionDistribution(BaseModel):
    """Keyword distribution within a section."""

    section_name: str
    section_type: str  # intro, body, conclusion, h2_section
    word_count: int
    keyword_count: int
    density: float


class KeywordResult(BaseModel):
    """Complete keyword analysis result."""

    word_count: int
    primary: KeywordAnalysis
    secondary: list[KeywordAnalysis]
    stuffing_risk: StuffingRisk
    distribution: list[SectionDistribution]
    recommendations: list[str]


def _get_density_status(actual: float, target: float) -> str:
    """Determine keyword density status relative to target."""
    if target == 0:
        return "optimal" if actual == 0 else "too_high"

    ratio = actual / target

    if ratio < 0.5:
        return "too_low"
    elif ratio < 0.8:
        return "slightly_low"
    elif ratio <= 1.2:
        return "optimal"
    elif ratio <= 1.5:
        return "slightly_high"
    else:
        return "too_high"


def _count_keyword(content: str, keyword: str) -> tuple[int, int]:
    """
    Count keyword occurrences.

    Returns:
        Tuple of (exact_matches, total_occurrences)
    """
    content_lower = content.lower()
    keyword_lower = keyword.lower()

    # Exact phrase matches (whole word boundaries)
    exact_pattern = r"\b" + re.escape(keyword_lower) + r"\b"
    exact_matches = len(re.findall(exact_pattern, content_lower))

    # For multi-word keywords, also count partial matches
    # (e.g., "SEO tips" would count "SEO" and "tips" separately)
    total = exact_matches

    return exact_matches, total


def _calculate_density(keyword_count: int, word_count: int) -> float:
    """Calculate keyword density as percentage."""
    if word_count == 0:
        return 0.0
    # For multi-word keywords, count the phrase as one unit
    return (keyword_count / word_count) * 100


def _extract_h1(content: str) -> str | None:
    """Extract H1 heading from markdown content."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1) if match else None


def _extract_h2s(content: str) -> list[str]:
    """Extract all H2 headings from markdown content."""
    matches = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    return matches


def _get_first_n_words(content: str, n: int) -> str:
    """Get the first n words of content (excluding markdown headers)."""
    # Remove markdown headers for word extraction
    clean = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)
    words = clean.split()
    return " ".join(words[:n])


def _get_conclusion(content: str) -> str:
    """Extract the conclusion section (last paragraph or section)."""
    # Try to find a conclusion heading
    conclusion_match = re.search(
        r"^##\s*(Conclusion|Summary|Final Thoughts|Wrapping Up|The Bottom Line).*?$\n([\s\S]*?)(?=^##|\Z)",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if conclusion_match:
        return conclusion_match.group(2)

    # Otherwise, take the last paragraph
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    # Filter out paragraphs that are just headers
    text_paragraphs = [p for p in paragraphs if not p.startswith("#")]
    if text_paragraphs:
        return text_paragraphs[-1]

    return ""


def _check_placements(content: str, keyword: str) -> KeywordPlacement:
    """Check keyword placement in critical positions."""
    keyword_lower = keyword.lower()
    pattern = r"\b" + re.escape(keyword_lower) + r"\b"

    # Check H1
    h1 = _extract_h1(content)
    in_h1 = bool(h1 and re.search(pattern, h1.lower()))

    # Check first 100 words
    first_100 = _get_first_n_words(content, 100)
    in_first_100 = bool(re.search(pattern, first_100.lower()))

    # Check conclusion
    conclusion = _get_conclusion(content)
    in_conclusion = bool(re.search(pattern, conclusion.lower()))

    # Check H2s
    h2s = _extract_h2s(content)
    h2_count = len(h2s)
    h2_with_keyword = sum(1 for h2 in h2s if re.search(pattern, h2.lower()))

    return KeywordPlacement(
        in_h1=in_h1,
        in_first_100_words=in_first_100,
        in_conclusion=in_conclusion,
        h2_count=h2_count,
        h2_with_keyword=h2_with_keyword,
    )


def _get_sections(content: str) -> list[tuple[str, str, str]]:
    """
    Split content into sections.

    Returns:
        List of (section_name, section_type, section_content)
    """
    sections = []

    # Split by H2 headers
    parts = re.split(r"(^##\s+.+$)", content, flags=re.MULTILINE)

    current_section = "Introduction"
    current_type = "intro"
    current_content = []

    for part in parts:
        if re.match(r"^##\s+", part):
            # Save previous section if it has content
            if current_content:
                text = "\n".join(current_content).strip()
                if text:
                    sections.append((current_section, current_type, text))

            # Start new section
            current_section = part.replace("##", "").strip()
            current_type = "h2_section"

            # Check if this is a conclusion section
            if re.search(
                r"(conclusion|summary|final thoughts|wrapping up|bottom line)",
                current_section,
                re.IGNORECASE,
            ):
                current_type = "conclusion"

            current_content = []
        else:
            # Skip H1 headers in content
            clean_part = re.sub(r"^#\s+.+$", "", part, flags=re.MULTILINE)
            if clean_part.strip():
                current_content.append(clean_part)

    # Don't forget the last section
    if current_content:
        text = "\n".join(current_content).strip()
        if text:
            # If no sections were found, treat entire content as body
            if not sections:
                current_type = "body"
            sections.append((current_section, current_type, text))

    return sections


def _analyze_distribution(
    content: str, keyword: str
) -> list[SectionDistribution]:
    """Analyze keyword distribution across sections."""
    sections = _get_sections(content)
    distribution = []

    for section_name, section_type, section_content in sections:
        word_count = len(section_content.split())
        exact_matches, _ = _count_keyword(section_content, keyword)
        density = _calculate_density(exact_matches, word_count)

        distribution.append(
            SectionDistribution(
                section_name=section_name,
                section_type=section_type,
                word_count=word_count,
                keyword_count=exact_matches,
                density=round(density, 2),
            )
        )

    return distribution


def _detect_stuffing(
    content: str, keyword: str, overall_density: float
) -> StuffingRisk:
    """Detect potential keyword stuffing."""
    warnings = []
    risk_score = 0

    # Check 1: Overall density > 3%
    if overall_density > 3.0:
        warnings.append(
            f"Overall keyword density is {overall_density:.1f}% (max recommended: 3%)"
        )
        risk_score += 2

    # Check 2: Any paragraph with density > 5%
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for i, para in enumerate(paragraphs, 1):
        if para.startswith("#"):
            continue
        word_count = len(para.split())
        if word_count < 20:  # Skip very short paragraphs
            continue
        exact_matches, _ = _count_keyword(para, keyword)
        para_density = _calculate_density(exact_matches, word_count)
        if para_density > 5.0:
            warnings.append(
                f"Paragraph {i} has {para_density:.1f}% keyword density (max: 5%)"
            )
            risk_score += 1

    # Check 3: Keyword in 5+ consecutive sentences
    sentences = re.split(r"[.!?]+\s+", content)
    consecutive = 0
    max_consecutive = 0
    keyword_pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

    for sentence in sentences:
        if re.search(keyword_pattern, sentence.lower()):
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0

    if max_consecutive >= 5:
        warnings.append(
            f"Keyword appears in {max_consecutive} consecutive sentences"
        )
        risk_score += 2

    # Check 4: Same phrase repeated 3+ times in 100 words
    words = content.split()
    window_size = 100

    for i in range(0, len(words) - window_size + 1, 50):  # Slide by 50 words
        window = " ".join(words[i : i + window_size]).lower()
        matches = len(re.findall(keyword_pattern, window))
        if matches >= 4:  # 4+ times in 100 words is suspicious
            warnings.append(
                f"Keyword repeated {matches} times within a 100-word span"
            )
            risk_score += 1
            break  # Only report once

    # Determine risk level
    if risk_score == 0:
        level = "none"
    elif risk_score <= 1:
        level = "low"
    elif risk_score <= 3:
        level = "medium"
    else:
        level = "high"

    return StuffingRisk(level=level, warnings=warnings)


def _generate_recommendations(
    primary: KeywordAnalysis,
    secondary: list[KeywordAnalysis],
    stuffing: StuffingRisk,
    word_count: int,
) -> list[str]:
    """Generate actionable keyword recommendations."""
    recommendations = []

    # Primary keyword recommendations
    p = primary
    target = p.target_density

    # Density recommendations
    if p.status == "too_low":
        needed = int((target / 100 * word_count) - p.exact_matches)
        recommendations.append(
            f"Primary keyword density is {p.density:.1f}% (target: {target}%). "
            f"Add {needed} more natural mentions."
        )
    elif p.status == "slightly_low":
        needed = int((target / 100 * word_count) - p.exact_matches)
        recommendations.append(
            f"Primary keyword density is {p.density:.1f}% (target: {target}%). "
            f"Consider adding {needed} more mentions."
        )
    elif p.status == "too_high":
        excess = int(p.exact_matches - (target * 1.2 / 100 * word_count))
        recommendations.append(
            f"Primary keyword density is {p.density:.1f}% (target: {target}%). "
            f"Remove or rephrase {excess} mentions to avoid over-optimization."
        )
    elif p.status == "slightly_high":
        recommendations.append(
            f"Primary keyword density is {p.density:.1f}%. "
            "Slightly above target but acceptable."
        )

    # Placement recommendations
    pl = p.placements
    if not pl.in_h1:
        recommendations.append(
            "Keyword missing from H1. Include it in the title."
        )
    if not pl.in_first_100_words:
        recommendations.append(
            "Keyword not in first 100 words. Add it to the introduction."
        )
    if not pl.in_conclusion:
        recommendations.append(
            "Keyword missing from conclusion. Reinforce it at the end."
        )
    if pl.h2_count > 0:
        target_h2s = min(3, max(2, pl.h2_count // 2))
        if pl.h2_with_keyword < target_h2s:
            recommendations.append(
                f"Keyword appears in {pl.h2_with_keyword}/{pl.h2_count} H2 headings. "
                f"Aim for {target_h2s} H2s with keyword variations."
            )

    # Secondary keyword recommendations
    for s in secondary:
        if s.status == "too_low":
            recommendations.append(
                f"Secondary keyword '{s.keyword}' has low density ({s.density:.1f}%). "
                "Add a few more mentions."
            )
        elif s.status == "too_high":
            recommendations.append(
                f"Secondary keyword '{s.keyword}' density is high ({s.density:.1f}%). "
                "Consider reducing."
            )

    # Stuffing warnings
    if stuffing.level in ["medium", "high"]:
        recommendations.append(
            f"Keyword stuffing risk: {stuffing.level}. Review and reduce repetition."
        )

    return recommendations


def analyze_keywords(
    content: str,
    primary_keyword: str,
    secondary_keywords: list[str] | None = None,
    target_density: float = 1.5,
) -> KeywordResult:
    """
    Analyze keyword usage in content.

    Args:
        content: Article text (markdown supported)
        primary_keyword: Main target keyword
        secondary_keywords: Optional secondary keywords
        target_density: Target density percentage (default 1.5%)

    Returns:
        KeywordResult with density, distribution, and recommendations
    """
    if secondary_keywords is None:
        secondary_keywords = []

    # Handle empty content
    if not content or not content.strip():
        empty_placement = KeywordPlacement(
            in_h1=False,
            in_first_100_words=False,
            in_conclusion=False,
            h2_count=0,
            h2_with_keyword=0,
        )
        return KeywordResult(
            word_count=0,
            primary=KeywordAnalysis(
                keyword=primary_keyword,
                exact_matches=0,
                total_occurrences=0,
                density=0.0,
                target_density=target_density,
                status="too_low",
                placements=empty_placement,
            ),
            secondary=[],
            stuffing_risk=StuffingRisk(level="none", warnings=[]),
            distribution=[],
            recommendations=["Add content with the target keyword."],
        )

    # Calculate word count (excluding markdown syntax)
    clean_content = re.sub(r"^#+\s+.*$", "", content, flags=re.MULTILINE)
    clean_content = re.sub(r"[*_`\[\]()#]", "", clean_content)
    word_count = len(clean_content.split())

    # Analyze primary keyword
    exact_matches, total_occurrences = _count_keyword(content, primary_keyword)
    density = _calculate_density(exact_matches, word_count)
    status = _get_density_status(density, target_density)
    placements = _check_placements(content, primary_keyword)

    primary_analysis = KeywordAnalysis(
        keyword=primary_keyword,
        exact_matches=exact_matches,
        total_occurrences=total_occurrences,
        density=round(density, 2),
        target_density=target_density,
        status=status,
        placements=placements,
    )

    # Analyze secondary keywords
    secondary_analysis = []
    for kw in secondary_keywords:
        exact, total = _count_keyword(content, kw)
        kw_density = _calculate_density(exact, word_count)
        kw_status = _get_density_status(kw_density, target_density * 0.5)  # Lower target for secondary
        kw_placements = _check_placements(content, kw)

        secondary_analysis.append(
            KeywordAnalysis(
                keyword=kw,
                exact_matches=exact,
                total_occurrences=total,
                density=round(kw_density, 2),
                target_density=round(target_density * 0.5, 2),
                status=kw_status,
                placements=kw_placements,
            )
        )

    # Check for stuffing
    stuffing_risk = _detect_stuffing(content, primary_keyword, density)

    # Analyze distribution
    distribution = _analyze_distribution(content, primary_keyword)

    # Generate recommendations
    recommendations = _generate_recommendations(
        primary_analysis, secondary_analysis, stuffing_risk, word_count
    )

    return KeywordResult(
        word_count=word_count,
        primary=primary_analysis,
        secondary=secondary_analysis,
        stuffing_risk=stuffing_risk,
        distribution=distribution,
        recommendations=recommendations,
    )
