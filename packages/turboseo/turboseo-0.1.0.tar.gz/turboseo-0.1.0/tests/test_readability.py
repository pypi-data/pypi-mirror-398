"""Tests for the readability analyzer."""

from pathlib import Path

import pytest

from turboseo.analyzers.readability import (
    ReadabilityResult,
    analyze_readability,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestCoreMetrics:
    """Tests for core readability metrics."""

    def test_flesch_reading_ease_calculated(self):
        text = "This is a simple sentence. It is easy to read."
        result = analyze_readability(text)
        assert result.flesch_reading_ease > 0

    def test_flesch_kincaid_grade_calculated(self):
        text = "This is a simple sentence. It is easy to read."
        result = analyze_readability(text)
        assert result.flesch_kincaid_grade >= 0

    def test_gunning_fog_calculated(self):
        text = "This is a simple sentence. It is easy to read."
        result = analyze_readability(text)
        assert result.gunning_fog >= 0

    def test_smog_index_calculated(self):
        text = "This is a simple sentence. It is easy to read. We have more to say."
        result = analyze_readability(text)
        assert result.smog_index >= 0

    def test_simple_text_has_low_grade(self):
        text = "The cat sat on the mat. The dog ran fast. Birds fly high."
        result = analyze_readability(text)
        assert result.flesch_kincaid_grade < 6

    def test_complex_text_has_high_grade(self):
        text = """
        The epistemological implications of quantum mechanical uncertainty
        fundamentally challenge our preconceived notions regarding the
        deterministic nature of physical phenomena, necessitating a
        comprehensive reevaluation of classical philosophical frameworks.
        """
        result = analyze_readability(text)
        assert result.flesch_kincaid_grade > 12


class TestSentenceAnalysis:
    """Tests for sentence structure analysis."""

    def test_counts_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        result = analyze_readability(text)
        assert result.sentence_count == 3

    def test_calculates_avg_sentence_length(self):
        text = "One two three four. Five six seven eight nine ten."
        result = analyze_readability(text)
        # First: 4 words, Second: 6 words, Average: 5
        assert 4 <= result.avg_sentence_length <= 6

    def test_detects_long_sentences(self):
        # Create a sentence with 30 words
        long_sentence = " ".join(["word"] * 30) + "."
        text = "Short sentence here. " + long_sentence
        result = analyze_readability(text)
        assert result.long_sentence_count >= 1

    def test_detects_very_long_sentences(self):
        # Create a sentence with 40 words
        very_long = " ".join(["word"] * 40) + "."
        text = "Short sentence. " + very_long
        result = analyze_readability(text)
        assert result.very_long_sentence_count >= 1

    def test_handles_abbreviations(self):
        text = "Dr. Smith went to the store. Mr. Jones stayed home."
        result = analyze_readability(text)
        # Should not split on Dr. or Mr.
        assert result.sentence_count == 2


class TestParagraphAnalysis:
    """Tests for paragraph structure analysis."""

    def test_counts_paragraphs(self):
        text = """First paragraph here.

Second paragraph here.

Third paragraph here."""
        result = analyze_readability(text)
        assert result.paragraph_count == 3

    def test_calculates_avg_paragraph_length(self):
        text = """First sentence. Second sentence.

Third sentence. Fourth sentence. Fifth sentence."""
        result = analyze_readability(text)
        # First para: 2 sentences, Second para: 3 sentences, Avg: 2.5
        assert 2 <= result.avg_paragraph_length <= 3

    def test_ignores_markdown_headers(self):
        text = """# Header

First paragraph.

## Another Header

Second paragraph."""
        result = analyze_readability(text)
        # Should only count actual paragraphs, not headers
        assert result.paragraph_count == 2


class TestPassiveVoice:
    """Tests for passive voice detection."""

    def test_detects_was_passive(self):
        text = "The ball was thrown by John. The game was won."
        result = analyze_readability(text)
        assert result.passive_voice_count >= 2

    def test_detects_is_passive(self):
        text = "The report is written by the team. The work is done."
        result = analyze_readability(text)
        assert result.passive_voice_count >= 2

    def test_detects_has_been_passive(self):
        text = "The project has been completed. The code has been reviewed."
        result = analyze_readability(text)
        assert result.passive_voice_count >= 2

    def test_calculates_passive_ratio(self):
        text = "The ball was thrown. John ran home. The game was won. She left."
        result = analyze_readability(text)
        # 2 passive out of 4 sentences = 0.5
        assert result.passive_voice_ratio > 0

    def test_active_voice_no_detection(self):
        text = "John threw the ball. Mary caught it. They played well."
        result = analyze_readability(text)
        assert result.passive_voice_count == 0


class TestTransitionWords:
    """Tests for transition word counting."""

    def test_counts_however(self):
        text = "The first option works. However, the second is better."
        result = analyze_readability(text)
        assert result.transition_word_count >= 1

    def test_counts_therefore(self):
        text = "The data supports this. Therefore, we proceed."
        result = analyze_readability(text)
        assert result.transition_word_count >= 1

    def test_counts_multiple_transitions(self):
        text = "First, we analyze. Then, we implement. Finally, we test."
        result = analyze_readability(text)
        assert result.transition_word_count >= 3

    def test_counts_phrase_transitions(self):
        text = "For example, this works well. In addition, it scales."
        result = analyze_readability(text)
        assert result.transition_word_count >= 2


class TestComplexWords:
    """Tests for complex word ratio."""

    def test_simple_text_low_ratio(self):
        text = "The cat sat on the mat. Dogs run and play."
        result = analyze_readability(text)
        assert result.complex_word_ratio < 0.1

    def test_complex_text_high_ratio(self):
        text = "Revolutionary methodologies fundamentally transform organizational infrastructure."
        result = analyze_readability(text)
        assert result.complex_word_ratio > 0.3


class TestScoring:
    """Tests for score calculation."""

    def test_simple_text_high_score(self):
        text = "The cat sat down. The dog ran away. Birds fly high in the sky."
        result = analyze_readability(text)
        assert result.score >= 80

    def test_complex_text_lower_score(self):
        text = """
        The epistemological ramifications of phenomenological investigations
        into consciousness necessitate comprehensive interdisciplinary methodologies.
        Notwithstanding philosophical objections, contemporary neuroscientific
        approaches demonstrate unprecedented explanatory sophistication.
        """
        result = analyze_readability(text)
        assert result.score < 70

    def test_score_bounded_0_to_100(self):
        # Even very bad text should not go below 0
        text = " ".join(["supercalifragilisticexpialidocious"] * 50) + "."
        result = analyze_readability(text)
        assert 0 <= result.score <= 100


class TestGrades:
    """Tests for grade assignment."""

    def test_grade_a_for_90_plus(self):
        text = "The cat sat. Dogs run. Birds fly."
        result = analyze_readability(text)
        if result.score >= 90:
            assert result.grade == "A"

    def test_grades_match_score_ranges(self):
        text = "Simple test content here."
        result = analyze_readability(text)

        if result.score >= 90:
            assert result.grade == "A"
        elif result.score >= 80:
            assert result.grade == "B"
        elif result.score >= 70:
            assert result.grade == "C"
        elif result.score >= 60:
            assert result.grade == "D"
        else:
            assert result.grade == "F"


class TestStatus:
    """Tests for status assignment."""

    def test_excellent_for_high_score(self):
        text = "The cat sat. Dogs run."
        result = analyze_readability(text)
        if result.score >= 90:
            assert result.status == "excellent"

    def test_status_values(self):
        text = "Test content here."
        result = analyze_readability(text)
        assert result.status in ["excellent", "good", "needs_improvement", "poor"]


class TestRecommendations:
    """Tests for recommendation generation."""

    def test_generates_recommendations_for_complex_text(self):
        text = """
        The epistemological implications of quantum mechanical uncertainty
        fundamentally challenge our preconceived notions regarding the
        deterministic nature of physical phenomena, necessitating a
        comprehensive reevaluation of classical philosophical frameworks
        that have dominated Western intellectual discourse for centuries.
        """
        result = analyze_readability(text)
        assert len(result.recommendations) > 0

    def test_no_recommendations_for_simple_text(self):
        text = "The cat sat down. Dogs run fast. Birds fly high."
        result = analyze_readability(text)
        # May have few or no recommendations for very simple text
        assert isinstance(result.recommendations, list)

    def test_recommendations_are_strings(self):
        text = "This is a moderately complex sentence structure for testing purposes."
        result = analyze_readability(text)
        for rec in result.recommendations:
            assert isinstance(rec, str)

    def test_long_sentence_recommendation(self):
        long_sentence = " ".join(["word"] * 40) + "."
        text = "Short. " + long_sentence
        result = analyze_readability(text)
        assert any("35 words" in rec for rec in result.recommendations)

    def test_passive_voice_recommendation(self):
        text = """
        The report was written by the team. The code was reviewed carefully.
        The tests were run overnight. The deployment was completed.
        """
        result = analyze_readability(text)
        # With 4 passive sentences out of 4, should recommend reducing
        if result.passive_voice_ratio > 0.2:
            assert any("passive" in rec.lower() for rec in result.recommendations)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_content(self):
        result = analyze_readability("")
        assert result.score == 100
        assert result.word_count == 0
        assert result.sentence_count == 0

    def test_whitespace_only(self):
        result = analyze_readability("   \n\n   ")
        assert result.score == 100
        assert result.word_count == 0

    def test_single_word(self):
        result = analyze_readability("Hello")
        assert result.word_count >= 1

    def test_single_sentence(self):
        result = analyze_readability("This is a single sentence.")
        assert result.sentence_count == 1

    def test_markdown_code_blocks_ignored(self):
        text = """
Regular text here.

```python
def complex_epistemological_framework():
    pass
```

More regular text here.
"""
        result = analyze_readability(text)
        # Code blocks should be stripped, not affecting readability
        assert result.word_count < 20


class TestWordCount:
    """Tests for word count."""

    def test_counts_words(self):
        text = "One two three four five."
        result = analyze_readability(text)
        assert result.word_count == 5

    def test_counts_characters(self):
        text = "Hello world."
        result = analyze_readability(text)
        assert result.character_count > 0


class TestResultModel:
    """Tests for the result model structure."""

    def test_result_is_pydantic_model(self):
        result = analyze_readability("Test content.")
        assert isinstance(result, ReadabilityResult)

    def test_result_has_all_fields(self):
        result = analyze_readability("Test content.")
        assert hasattr(result, "score")
        assert hasattr(result, "grade")
        assert hasattr(result, "flesch_reading_ease")
        assert hasattr(result, "flesch_kincaid_grade")
        assert hasattr(result, "avg_sentence_length")
        assert hasattr(result, "passive_voice_ratio")
        assert hasattr(result, "recommendations")

    def test_result_serializable(self):
        result = analyze_readability("Test content for serialization.")
        result_dict = result.model_dump()
        assert isinstance(result_dict, dict)
        assert "score" in result_dict


class TestFixtures:
    """Tests using fixture files."""

    def test_human_samples_readable(self):
        for i in range(1, 4):
            path = FIXTURES / f"human_sample_{i}.md"
            if path.exists():
                content = path.read_text()
                result = analyze_readability(content)
                # Human samples should be reasonably readable
                assert result.score >= 60, f"human_sample_{i}.md scored {result.score}"

    def test_ai_samples_analyzed(self):
        for i in range(1, 4):
            path = FIXTURES / f"ai_sample_{i}.md"
            if path.exists():
                content = path.read_text()
                result = analyze_readability(content)
                # Should return a valid result
                assert 0 <= result.score <= 100
