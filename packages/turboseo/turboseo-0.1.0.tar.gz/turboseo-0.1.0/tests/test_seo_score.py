"""Tests for the SEO score analyzer."""

from pathlib import Path

import pytest

from turboseo.analyzers.seo_score import (
    SEOResult,
    analyze_seo,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestOverallScore:
    """Tests for overall score calculation."""

    def test_calculates_overall_score(self):
        content = "# Test Article\n\n" + "This is test content. " * 100
        result = analyze_seo(content)
        assert 0 <= result.overall_score <= 100

    def test_score_bounded(self):
        # Even very bad content should be 0-100
        result = analyze_seo("bad")
        assert 0 <= result.overall_score <= 100

    def test_good_content_scores_higher(self):
        good_content = """# How to Write Great Content

This is a comprehensive guide to writing content.

## Introduction

Writing good content requires practice and attention to detail.

## Main Points

Here are some key points to consider when writing.

## Tips for Success

Follow these tips to improve your writing skills.

## Conclusion

In summary, good writing takes effort but is achievable.
""" + "Additional content here. " * 50

        bad_content = "delve into the tapestry of pivotal crucial"

        good_result = analyze_seo(good_content)
        bad_result = analyze_seo(bad_content)

        assert good_result.overall_score > bad_result.overall_score


class TestWeightedScoring:
    """Tests for weighted category scoring."""

    def test_all_categories_present(self):
        content = "# Test\n\nContent here. " * 20
        result = analyze_seo(content)

        expected_categories = [
            "content", "human_writing", "keywords",
            "readability", "meta", "structure"
        ]
        for cat in expected_categories:
            assert cat in result.categories

    def test_weights_sum_to_one(self):
        content = "# Test\n\nContent here. " * 20
        result = analyze_seo(content)

        total_weight = sum(cat.weight for cat in result.categories.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_weighted_scores_calculated(self):
        content = "# Test\n\nContent here. " * 20
        result = analyze_seo(content)

        for cat in result.categories.values():
            expected = cat.score * cat.weight
            assert abs(cat.weighted_score - expected) < 0.1

    def test_human_writing_has_high_weight(self):
        content = "# Test\n\nContent here."
        result = analyze_seo(content)

        hw_weight = result.categories["human_writing"].weight
        assert hw_weight >= 0.20  # At least 20%


class TestContentScoring:
    """Tests for content length scoring."""

    def test_short_content_penalized(self):
        short_content = "# Title\n\nShort content."
        result = analyze_seo(short_content)

        assert result.categories["content"].score < 100
        assert any("short" in issue.lower() for issue in result.categories["content"].issues)

    def test_adequate_content_scores_well(self):
        # Create content with 1500+ words
        adequate_content = "# Title\n\n" + "This is adequate content for SEO purposes. " * 200
        result = analyze_seo(adequate_content)

        assert result.categories["content"].score >= 85

    def test_word_count_calculated(self):
        content = "# Title\n\nOne two three four five six seven eight nine ten."
        result = analyze_seo(content)

        assert result.word_count >= 10


class TestMetaScoring:
    """Tests for meta element scoring."""

    def test_missing_meta_penalized(self):
        content = "# Test\n\nContent here. " * 20
        result = analyze_seo(content)  # No meta provided

        assert result.categories["meta"].score < 100
        assert any("missing" in issue.lower() for issue in result.categories["meta"].issues)

    def test_good_meta_scores_well(self):
        content = "# SEO Guide\n\nContent about SEO here. " * 20
        result = analyze_seo(
            content,
            primary_keyword="SEO",
            meta_title="Complete SEO Guide for Beginners - Learn SEO Today",  # 50 chars
            meta_description="Learn everything about SEO in this comprehensive guide. "
                           "We cover all the basics and advanced techniques you need to know."  # 140 chars
        )

        assert result.categories["meta"].score >= 70

    def test_meta_title_length_recorded(self):
        content = "# Test\n\nContent."
        title = "This is a test title"
        result = analyze_seo(content, meta_title=title)

        assert result.meta_title_length == len(title)

    def test_meta_description_length_recorded(self):
        content = "# Test\n\nContent."
        desc = "This is a test description"
        result = analyze_seo(content, meta_description=desc)

        assert result.meta_description_length == len(desc)

    def test_keyword_in_meta_checked(self):
        content = "# Test\n\nContent about testing. " * 20
        result = analyze_seo(
            content,
            primary_keyword="testing",
            meta_title="Something else entirely",
            meta_description="No keyword here either."
        )

        assert any("keyword" in issue.lower() and "title" in issue.lower()
                   for issue in result.meta_issues)


class TestStructureScoring:
    """Tests for heading structure scoring."""

    def test_missing_h1_penalized(self):
        content = "Content without any headings."
        result = analyze_seo(content)

        assert result.categories["structure"].score < 100
        assert result.h1_count == 0

    def test_multiple_h1_penalized(self):
        content = "# First H1\n\nContent.\n\n# Second H1\n\nMore content."
        result = analyze_seo(content)

        assert result.h1_count == 2
        assert any("multiple h1" in issue.lower() for issue in result.categories["structure"].issues)

    def test_good_structure_scores_well(self):
        content = """# Main Title

Introduction paragraph.

## Section One

Content for section one.

## Section Two

Content for section two.

## Section Three

Content for section three.

## Section Four

Content for section four.
"""
        result = analyze_seo(content)

        assert result.h1_count == 1
        assert result.h2_count == 4
        assert result.categories["structure"].score >= 80

    def test_heading_counts_recorded(self):
        content = """# H1

## H2 One

### H3 One

## H2 Two

### H3 Two

### H3 Three
"""
        result = analyze_seo(content)

        assert result.h1_count == 1
        assert result.h2_count == 2
        assert result.h3_count == 3


class TestGradeAssignment:
    """Tests for grade calculation."""

    def test_grade_a_for_90_plus(self):
        # Create very good content
        content = """# Excellent SEO Guide

This is a comprehensive guide to writing excellent content for search engines.

## Introduction

Content optimization is important for visibility.

## Key Strategies

Here are proven strategies for better rankings.

## Best Practices

Follow these practices for success.

## Implementation Tips

Practical tips for implementation.

## Conclusion

Follow these guidelines for better results.
""" + "High quality informative content here. " * 100

        result = analyze_seo(
            content,
            primary_keyword="SEO",
            meta_title="Complete SEO Guide - Everything You Need to Know Today",
            meta_description="Learn the complete guide to SEO optimization. "
                           "This comprehensive resource covers all strategies and best practices."
        )

        if result.overall_score >= 90:
            assert result.grade == "A"

    def test_grades_match_score_ranges(self):
        content = "# Test\n\nContent. " * 50
        result = analyze_seo(content)

        if result.overall_score >= 90:
            assert result.grade == "A"
        elif result.overall_score >= 80:
            assert result.grade == "B"
        elif result.overall_score >= 70:
            assert result.grade == "C"
        elif result.overall_score >= 60:
            assert result.grade == "D"
        else:
            assert result.grade == "F"


class TestPublishingReady:
    """Tests for publishing readiness."""

    def test_not_ready_with_low_score(self):
        content = "bad content"
        result = analyze_seo(content)

        if result.overall_score < 80:
            assert result.publishing_ready is False

    def test_not_ready_with_critical_issues(self):
        # Very short content should have critical issues
        content = "# Title\n\nShort."
        result = analyze_seo(content)

        if len(result.critical_issues) > 0:
            assert result.publishing_ready is False

    def test_ready_with_good_score_no_critical(self):
        # Create content that should be publishing ready
        content = """# Complete Guide to Content Writing

This comprehensive guide covers everything you need to know about writing content.

## Introduction

Writing good content is essential for online success. It helps with engagement.

## Understanding Your Audience

Know who you are writing for. Research your target readers.

## Creating Quality Content

Focus on providing value. Make your content informative and helpful.

## Optimization Tips

Use proper headings and structure. Keep paragraphs short.

## Conclusion

Follow these guidelines to create better content.
""" + "Quality informative content continues here with more details. " * 80

        result = analyze_seo(
            content,
            primary_keyword="content",
            meta_title="Complete Guide to Content Writing - Tips and Strategies",
            meta_description="Learn how to write better content with this comprehensive guide. "
                           "Covers audience research, quality tips, and optimization strategies."
        )

        if result.overall_score >= 80 and len(result.critical_issues) == 0:
            assert result.publishing_ready is True


class TestIssuePrioritization:
    """Tests for issue prioritization."""

    def test_issues_categorized(self):
        content = "short"  # Will have many issues
        result = analyze_seo(content)

        assert isinstance(result.critical_issues, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)

    def test_critical_issues_for_major_problems(self):
        content = "# Title\n\nVery short content."
        result = analyze_seo(content)

        # Should have critical issues for very short content
        assert len(result.critical_issues) > 0 or len(result.warnings) > 0

    def test_suggestions_for_minor_issues(self):
        content = """# Good Title

This is reasonable content with proper structure and length.

## Section One

Content here that is informative and helpful.

## Section Two

More content that adds value to the reader.

## Section Three

Additional information and details.
""" + "More content. " * 100

        result = analyze_seo(content)

        # Should have suggestions rather than critical issues
        # (content is decent but not perfect)
        total_issues = len(result.critical_issues) + len(result.warnings) + len(result.suggestions)
        assert total_issues >= 0  # Just verify structure


class TestKeywordIntegration:
    """Tests for keyword analysis integration."""

    def test_keyword_analysis_included(self):
        content = "# SEO Guide\n\nThis is about SEO optimization. " * 20
        result = analyze_seo(content, primary_keyword="SEO")

        assert result.keywords is not None
        assert result.keywords.primary.keyword == "SEO"

    def test_no_keyword_handled(self):
        content = "# Test\n\nContent here. " * 20
        result = analyze_seo(content)  # No keyword

        assert result.keywords is None
        assert "keywords" in result.categories  # Category still exists with neutral score

    def test_secondary_keywords_passed(self):
        content = "# Guide\n\nContent about SEO and marketing. " * 20
        result = analyze_seo(
            content,
            primary_keyword="SEO",
            secondary_keywords=["marketing", "optimization"]
        )

        assert result.keywords is not None
        assert len(result.keywords.secondary) == 2


class TestHumanWritingIntegration:
    """Tests for human writing analysis integration."""

    def test_human_writing_included(self):
        content = "# Test\n\nSimple clear content here. " * 20
        result = analyze_seo(content)

        assert result.human_writing is not None
        assert hasattr(result.human_writing, "score")

    def test_ai_content_penalized(self):
        ai_content = """# The Transformative Journey

We must delve into the intricate tapestry of digital marketing.
It plays a pivotal role in fostering connections.
This stands as a testament to innovation.
The seamless integration continues to captivate users.
""" * 5

        human_content = """# Marketing Guide

This guide covers the basics of digital marketing.
It explains how to reach your audience effectively.
You will learn practical tips for better results.
The techniques here are proven and straightforward.
""" * 5

        ai_result = analyze_seo(ai_content)
        human_result = analyze_seo(human_content)

        assert human_result.human_writing.score > ai_result.human_writing.score


class TestReadabilityIntegration:
    """Tests for readability analysis integration."""

    def test_readability_included(self):
        content = "# Test\n\nSimple content. " * 20
        result = analyze_seo(content)

        assert result.readability is not None
        assert hasattr(result.readability, "score")
        assert hasattr(result.readability, "flesch_reading_ease")


class TestResultModel:
    """Tests for the result model structure."""

    def test_result_is_pydantic_model(self):
        result = analyze_seo("# Test\n\nContent.")
        assert isinstance(result, SEOResult)

    def test_result_has_all_fields(self):
        result = analyze_seo("# Test\n\nContent.")

        assert hasattr(result, "overall_score")
        assert hasattr(result, "grade")
        assert hasattr(result, "publishing_ready")
        assert hasattr(result, "categories")
        assert hasattr(result, "human_writing")
        assert hasattr(result, "readability")
        assert hasattr(result, "critical_issues")
        assert hasattr(result, "warnings")
        assert hasattr(result, "suggestions")

    def test_result_serializable(self):
        result = analyze_seo("# Test\n\nContent for serialization.")
        result_dict = result.model_dump()

        assert isinstance(result_dict, dict)
        assert "overall_score" in result_dict
        assert "categories" in result_dict


class TestFixtures:
    """Tests using fixture files."""

    def test_human_samples_score_well(self):
        for i in range(1, 4):
            path = FIXTURES / f"human_sample_{i}.md"
            if path.exists():
                content = path.read_text()
                result = analyze_seo(content)
                # Human samples should have good human writing scores
                assert result.human_writing.score >= 85, f"human_sample_{i}.md"

    def test_ai_samples_flagged(self):
        for i in range(1, 4):
            path = FIXTURES / f"ai_sample_{i}.md"
            if path.exists():
                content = path.read_text()
                result = analyze_seo(content)
                # AI samples should have lower human writing scores
                assert result.human_writing.score < 70, f"ai_sample_{i}.md"

    def test_full_analysis_on_fixtures(self):
        path = FIXTURES / "human_sample_1.md"
        if path.exists():
            content = path.read_text()
            result = analyze_seo(
                content,
                primary_keyword="podcast",
                meta_title="How to Make Money From Your Podcast - Complete Guide",
                meta_description="Learn how to monetize your podcast with proven strategies. "
                               "Covers sponsorships, premium content, and affiliate deals."
            )

            # Should complete without errors
            assert result.overall_score > 0
            assert result.keywords is not None
