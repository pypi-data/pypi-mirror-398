"""Tests for the writing standards checker."""

from pathlib import Path

import pytest

from turboseo.analyzers.writing_standards import (
    WritingStandardsResult,
    analyze_writing_standards,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestAIVocabulary:
    """Tests for AI vocabulary detection."""

    def test_detects_delve(self):
        result = analyze_writing_standards("We must delve into this topic.")
        assert any(i.text.lower() == "delve" for i in result.issues)
        assert any(i.category == "vocabulary" for i in result.issues)

    def test_detects_tapestry(self):
        result = analyze_writing_standards("The rich tapestry of culture.")
        assert any("tapestry" in i.text.lower() for i in result.issues)

    def test_detects_pivotal(self):
        result = analyze_writing_standards("This was a pivotal moment.")
        assert any("pivotal" in i.text.lower() for i in result.issues)

    def test_detects_multiple_ai_words(self):
        text = "We delve into the intricate tapestry of this vibrant field."
        result = analyze_writing_standards(text)
        vocab_issues = [i for i in result.issues if i.category == "vocabulary"]
        assert len(vocab_issues) >= 3

    def test_no_false_positives_on_normal_text(self):
        text = "This article explores the history of podcasting. It covers the basics."
        result = analyze_writing_standards(text)
        vocab_issues = [i for i in result.issues if i.category == "vocabulary"]
        assert len(vocab_issues) == 0

    def test_detects_leverage(self):
        result = analyze_writing_standards("We leverage technology to improve.")
        assert any("leverage" in i.text.lower() for i in result.issues)

    def test_detects_robust(self):
        result = analyze_writing_standards("This provides a robust solution.")
        assert any("robust" in i.text.lower() for i in result.issues)

    def test_detects_seamless(self):
        result = analyze_writing_standards("The seamless integration works well.")
        assert any("seamless" in i.text.lower() for i in result.issues)

    def test_provides_alternatives(self):
        result = analyze_writing_standards("We must delve into the topic.")
        delve_issue = next(i for i in result.issues if "delve" in i.text.lower())
        assert "explore" in delve_issue.suggestion.lower()


class TestPufferyPatterns:
    """Tests for puffery pattern detection."""

    def test_detects_pivotal_role(self):
        text = "Technology plays a pivotal role in modern business."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_vital_role(self):
        text = "Education plays a vital role in society."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_testament(self):
        text = "This stands as a testament to human ingenuity."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_nestled_in(self):
        text = "The village, nestled in the mountains, offers views."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_rich_tapestry(self):
        text = "The rich tapestry of local traditions."
        result = analyze_writing_standards(text)
        puffery = [i for i in result.issues if i.category == "puffery"]
        assert len(puffery) >= 1

    def test_detects_continues_to_captivate(self):
        text = "The museum continues to captivate visitors."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)

    def test_detects_groundbreaking_approach(self):
        text = "Their groundbreaking approach changed the industry."
        result = analyze_writing_standards(text)
        assert any(i.category == "puffery" for i in result.issues)


class TestSuperficialAnalysis:
    """Tests for superficial analysis pattern detection."""

    def test_detects_highlighting_importance(self):
        text = "Sales increased 40%, highlighting the importance of marketing."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)

    def test_detects_underscoring(self):
        text = "The results were positive, underscoring the value of research."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)

    def test_detects_emphasizing(self):
        text = "Revenue grew, emphasizing the need for expansion."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)

    def test_detects_showcasing(self):
        text = "The event was successful, showcasing their expertise."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)

    def test_detects_demonstrating(self):
        text = "They finished first, demonstrating their skill."
        result = analyze_writing_standards(text)
        assert any(i.category == "superficial" for i in result.issues)


class TestStructuralFlags:
    """Tests for structural red flag detection."""

    def test_detects_in_conclusion(self):
        text = "In conclusion, this shows the value of planning."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_in_summary(self):
        text = "In summary, the project was a success."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_to_summarize(self):
        text = "To summarize, we achieved our goals."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_challenge_formula(self):
        text = "Despite its popularity, the platform faces several challenges."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_not_only_but_also(self):
        text = "Not only does this improve efficiency, but it also reduces costs."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_its_not_just_about(self):
        text = "It's not just about the money, it's about the impact."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)

    def test_detects_important_to_note(self):
        text = "It is important to note that results may vary."
        result = analyze_writing_standards(text)
        assert any(i.category == "structural" for i in result.issues)


class TestScoring:
    """Tests for score calculation."""

    def test_perfect_score_for_clean_text(self):
        text = "This is a simple, clear sentence about podcasting. It covers the basics."
        result = analyze_writing_standards(text)
        assert result.score >= 95

    def test_low_score_for_ai_heavy_text(self):
        text = """We must delve into the intricate tapestry of digital marketing.
It plays a pivotal role in fostering connections.
This stands as a testament to innovation.
In conclusion, success is crucial."""
        result = analyze_writing_standards(text)
        assert result.score <= 75  # Heavy AI vocabulary reduces score significantly

    def test_medium_score_for_mixed_text(self):
        text = """Podcasting has become popular in recent years.
Many creators leverage multiple platforms and foster growth.
The industry is transformative and continues to evolve."""
        result = analyze_writing_standards(text)
        assert 80 <= result.score <= 99  # Light AI vocabulary, still mostly clean

    def test_empty_content_returns_perfect_score(self):
        result = analyze_writing_standards("")
        assert result.score == 100
        assert result.grade == "A"

    def test_strict_mode_reduces_score_more(self):
        text = "We must delve into this topic and leverage our resources."
        normal_result = analyze_writing_standards(text, strict=False)
        strict_result = analyze_writing_standards(text, strict=True)
        assert strict_result.score < normal_result.score


class TestGrades:
    """Tests for grade assignment."""

    def test_grade_a_for_90_plus(self):
        result = analyze_writing_standards("Simple clear text here.")
        assert result.grade == "A"

    def test_grade_calculation(self):
        # Create text with known issues to get specific scores
        text_with_issues = "We delve into topics. " * 3  # 3 vocabulary issues
        result = analyze_writing_standards(text_with_issues)
        # Score should be 100 - (3 * 2) = 94 (medium severity words)
        assert result.score <= 94
        assert result.grade in ["A", "B"]


class TestSummary:
    """Tests for issue summary."""

    def test_summary_counts_categories(self):
        text = """We delve into the tapestry of knowledge.
This plays a pivotal role in success.
Results improved, highlighting the importance of effort.
In conclusion, we succeeded."""
        result = analyze_writing_standards(text)
        assert "vocabulary" in result.summary
        assert "puffery" in result.summary
        assert "superficial" in result.summary
        assert "structural" in result.summary


class TestFixtures:
    """Tests using fixture files."""

    @pytest.mark.parametrize(
        "filename",
        [
            "ai_sample_1.md",
            "ai_sample_2.md",
            "ai_sample_3.md",
        ],
    )
    def test_ai_samples_score_low(self, filename):
        content = (FIXTURES / filename).read_text()
        result = analyze_writing_standards(content)
        assert result.score < 70, f"{filename} scored {result.score}, expected <70"

    @pytest.mark.parametrize(
        "filename",
        [
            "human_sample_1.md",
            "human_sample_2.md",
            "human_sample_3.md",
        ],
    )
    def test_human_samples_score_high(self, filename):
        content = (FIXTURES / filename).read_text()
        result = analyze_writing_standards(content)
        assert result.score > 85, f"{filename} scored {result.score}, expected >85"


class TestLineNumbers:
    """Tests for line number reporting."""

    def test_reports_correct_line_number(self):
        text = "Line one.\nLine two.\nWe delve into this."
        result = analyze_writing_standards(text)
        delve_issue = next(i for i in result.issues if "delve" in i.text.lower())
        assert delve_issue.line == 3

    def test_reports_column_number(self):
        text = "Start delve end."
        result = analyze_writing_standards(text)
        delve_issue = next(i for i in result.issues if "delve" in i.text.lower())
        assert delve_issue.column == 7  # "Start " is 6 chars, delve starts at 7


class TestSuggestions:
    """Tests for suggestion generation."""

    def test_provides_alternatives_for_vocabulary(self):
        result = analyze_writing_standards("We delve into the topic.")
        issue = next(i for i in result.issues if "delve" in i.text.lower())
        assert "Replace with:" in issue.suggestion
        assert "explore" in issue.suggestion.lower()

    def test_provides_fix_for_puffery(self):
        result = analyze_writing_standards("This plays a vital role in success.")
        issue = next(i for i in result.issues if i.category == "puffery")
        assert issue.suggestion
        assert len(issue.suggestion) > 10

    def test_provides_fix_for_superficial(self):
        result = analyze_writing_standards("Sales grew, highlighting the importance.")
        issue = next(i for i in result.issues if i.category == "superficial")
        assert issue.suggestion
        assert "-ing" in issue.suggestion or "Remove" in issue.suggestion


class TestWordCount:
    """Tests for word count reporting."""

    def test_counts_words(self):
        text = "One two three four five."
        result = analyze_writing_standards(text)
        assert result.word_count == 5

    def test_word_count_with_multiple_lines(self):
        text = "One two.\nThree four five.\nSix."
        result = analyze_writing_standards(text)
        assert result.word_count == 6


class TestResultModel:
    """Tests for the result model structure."""

    def test_result_is_pydantic_model(self):
        result = analyze_writing_standards("Test content.")
        assert isinstance(result, WritingStandardsResult)

    def test_result_has_required_fields(self):
        result = analyze_writing_standards("Test content.")
        assert hasattr(result, "score")
        assert hasattr(result, "grade")
        assert hasattr(result, "issues")
        assert hasattr(result, "summary")
        assert hasattr(result, "word_count")

    def test_result_serializable_to_dict(self):
        result = analyze_writing_standards("We delve into topics.")
        result_dict = result.model_dump()
        assert isinstance(result_dict, dict)
        assert "score" in result_dict
        assert "issues" in result_dict
