"""
TurboSEO CLI

Command-line interface for TurboSEO content analysis.
"""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import turboseo
from turboseo.analyzers.keywords import analyze_keywords
from turboseo.analyzers.readability import analyze_readability
from turboseo.analyzers.seo_score import analyze_seo
from turboseo.analyzers.writing_standards import analyze_writing_standards

console = Console()


@click.group()
@click.version_option(version=turboseo.__version__, prog_name="turboseo")
def cli():
    """TurboSEO - SEO content toolkit that writes human, not AI."""
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Use stricter thresholds")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def check(file: str, strict: bool, output_json: bool):
    """Check content for AI writing patterns."""
    content = Path(file).read_text()
    result = analyze_writing_standards(content, strict=strict)

    if output_json:
        console.print(json.dumps(result.model_dump(), indent=2))
        return

    # Score and grade panel
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "orange1", "F": "red"}
    grade_color = grade_colors.get(result.grade, "white")

    console.print(
        Panel(
            f"[bold {grade_color}]Grade: {result.grade}[/] | "
            f"Score: {result.score}/100 | "
            f"Words: {result.word_count}",
            title="Human Writing Check",
        )
    )

    if not result.issues:
        console.print("[green]No AI writing patterns detected.[/green]")
        return

    # Issues table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Line", style="dim", width=6)
    table.add_column("Category", width=12)
    table.add_column("Issue", width=30)
    table.add_column("Suggestion", width=40)

    severity_colors = {"high": "red", "medium": "yellow", "low": "dim"}

    for issue in result.issues:
        color = severity_colors.get(issue.severity, "white")
        table.add_row(
            str(issue.line),
            f"[{color}]{issue.category}[/]",
            issue.text[:30],
            issue.suggestion[:40] if len(issue.suggestion) > 40 else issue.suggestion,
        )

    console.print(table)

    # Summary
    if result.summary:
        summary_parts = [f"{cat}: {count}" for cat, count in result.summary.items()]
        console.print(f"\n[dim]Summary: {', '.join(summary_parts)}[/dim]")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--keyword", "-k", help="Primary keyword")
@click.option("--secondary", "-s", multiple=True, help="Secondary keywords")
@click.option("--title", help="Meta title")
@click.option("--description", help="Meta description")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def analyze(
    file: str,
    keyword: str | None,
    secondary: tuple,
    title: str | None,
    description: str | None,
    output_json: bool,
):
    """Full SEO analysis of content."""
    content = Path(file).read_text()
    result = analyze_seo(
        content,
        primary_keyword=keyword,
        secondary_keywords=list(secondary) if secondary else None,
        meta_title=title,
        meta_description=description,
    )

    if output_json:
        console.print(json.dumps(result.model_dump(), indent=2))
        return

    # Grade colors
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "orange1", "F": "red"}
    grade_color = grade_colors.get(result.grade, "white")

    # Header panel
    ready_indicator = "[green]✓ Ready[/]" if result.publishing_ready else "[red]✗ Not Ready[/]"
    console.print(
        Panel(
            f"[bold {grade_color}]Grade: {result.grade}[/] | "
            f"Score: {result.overall_score}/100 | "
            f"Publishing: {ready_indicator}",
            title="SEO Analysis",
        )
    )

    # Category scores table
    cat_table = Table(show_header=True, header_style="bold", title="Category Breakdown")
    cat_table.add_column("Category", width=20)
    cat_table.add_column("Score", width=10)
    cat_table.add_column("Weight", width=10)
    cat_table.add_column("Weighted", width=10)

    category_order = ["human_writing", "keywords", "content", "readability", "meta", "structure"]
    category_labels = {
        "human_writing": "Human Writing",
        "keywords": "Keywords",
        "content": "Content",
        "readability": "Readability",
        "meta": "Meta Tags",
        "structure": "Structure",
    }

    for cat_key in category_order:
        if cat_key in result.categories:
            cat = result.categories[cat_key]
            score_color = "green" if cat.score >= 80 else "yellow" if cat.score >= 60 else "red"
            cat_table.add_row(
                category_labels.get(cat_key, cat_key),
                f"[{score_color}]{cat.score}[/]",
                f"{cat.weight:.0%}",
                f"{cat.weighted_score:.1f}",
            )

    console.print(cat_table)

    # Structure info
    console.print(
        f"\n[dim]Content: {result.word_count} words | "
        f"H1: {result.h1_count} | H2: {result.h2_count} | H3: {result.h3_count}[/dim]"
    )

    # Critical issues
    if result.critical_issues:
        console.print("\n[bold red]Critical Issues:[/bold red]")
        for issue in result.critical_issues:
            console.print(f"  [red]✗[/red] {issue}")

    # Warnings
    if result.warnings:
        console.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]![/yellow] {warning}")

    # Suggestions (limit to top 5)
    if result.suggestions:
        console.print("\n[bold]Suggestions:[/bold]")
        for suggestion in result.suggestions[:5]:
            console.print(f"  [dim]•[/dim] {suggestion}")
        if len(result.suggestions) > 5:
            console.print(f"  [dim]... and {len(result.suggestions) - 5} more[/dim]")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def readability(file: str, output_json: bool):
    """Analyze content readability."""
    content = Path(file).read_text()
    result = analyze_readability(content)

    if output_json:
        console.print(json.dumps(result.model_dump(), indent=2))
        return

    # Score and grade panel
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "orange1", "F": "red"}
    grade_color = grade_colors.get(result.grade, "white")
    status_colors = {"excellent": "green", "good": "blue", "needs_improvement": "yellow", "poor": "red"}
    status_color = status_colors.get(result.status, "white")

    console.print(
        Panel(
            f"[bold {grade_color}]Grade: {result.grade}[/] | "
            f"Score: {result.score}/100 | "
            f"Status: [{status_color}]{result.status.replace('_', ' ').title()}[/]",
            title="Readability Analysis",
        )
    )

    # Metrics table
    metrics_table = Table(show_header=True, header_style="bold", title="Core Metrics")
    metrics_table.add_column("Metric", width=25)
    metrics_table.add_column("Value", width=10)
    metrics_table.add_column("Target", width=15)

    # Color code Flesch Reading Ease
    fre = result.flesch_reading_ease
    fre_color = "green" if 60 <= fre <= 70 else "yellow" if 50 <= fre <= 80 else "red"
    metrics_table.add_row("Flesch Reading Ease", f"[{fre_color}]{fre}[/]", "60-70")

    # Color code grade level
    gl = result.flesch_kincaid_grade
    gl_color = "green" if 8 <= gl <= 10 else "yellow" if 6 <= gl <= 12 else "red"
    metrics_table.add_row("Flesch-Kincaid Grade", f"[{gl_color}]{gl}[/]", "8-10")

    metrics_table.add_row("Gunning Fog Index", str(result.gunning_fog), "-")
    metrics_table.add_row("SMOG Index", str(result.smog_index), "-")

    console.print(metrics_table)

    # Structure table
    struct_table = Table(show_header=True, header_style="bold", title="Structure")
    struct_table.add_column("Metric", width=25)
    struct_table.add_column("Value", width=10)
    struct_table.add_column("Target", width=15)

    asl = result.avg_sentence_length
    asl_color = "green" if asl <= 20 else "yellow" if asl <= 25 else "red"
    struct_table.add_row("Avg Sentence Length", f"[{asl_color}]{asl} words[/]", "15-20 words")

    struct_table.add_row("Avg Paragraph Length", f"{result.avg_paragraph_length} sentences", "2-4 sentences")
    struct_table.add_row("Total Sentences", str(result.sentence_count), "-")
    struct_table.add_row("Total Words", str(result.word_count), "-")

    if result.very_long_sentence_count > 0:
        struct_table.add_row(
            "Very Long Sentences (>35w)",
            f"[red]{result.very_long_sentence_count}[/]",
            "0"
        )
    elif result.long_sentence_count > 0:
        struct_table.add_row(
            "Long Sentences (>25w)",
            f"[yellow]{result.long_sentence_count}[/]",
            "Few"
        )

    console.print(struct_table)

    # Complexity table
    if result.passive_voice_count > 0 or result.transition_word_count > 0:
        complex_table = Table(show_header=True, header_style="bold", title="Complexity")
        complex_table.add_column("Metric", width=25)
        complex_table.add_column("Value", width=15)
        complex_table.add_column("Target", width=15)

        pv_pct = result.passive_voice_ratio * 100
        pv_color = "green" if pv_pct < 15 else "yellow" if pv_pct <= 20 else "red"
        complex_table.add_row(
            "Passive Voice",
            f"[{pv_color}]{pv_pct:.0f}% ({result.passive_voice_count})[/]",
            "<20%"
        )

        complex_table.add_row(
            "Complex Words (3+ syl)",
            f"{result.complex_word_ratio * 100:.0f}%",
            "-"
        )
        complex_table.add_row("Transition Words", str(result.transition_word_count), "Several")

        console.print(complex_table)

    # Recommendations
    if result.recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in result.recommendations:
            console.print(f"  [yellow]•[/yellow] {rec}")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--keyword", "-k", required=True, help="Primary keyword")
@click.option("--secondary", "-s", multiple=True, help="Secondary keywords")
@click.option("--target-density", "-d", default=1.5, help="Target density %")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def keywords(
    file: str, keyword: str, secondary: tuple, target_density: float, output_json: bool
):
    """Analyze keyword usage."""
    content = Path(file).read_text()
    result = analyze_keywords(
        content,
        primary_keyword=keyword,
        secondary_keywords=list(secondary) if secondary else None,
        target_density=target_density,
    )

    if output_json:
        console.print(json.dumps(result.model_dump(), indent=2))
        return

    # Status colors
    status_colors = {
        "optimal": "green",
        "slightly_low": "yellow",
        "slightly_high": "yellow",
        "too_low": "red",
        "too_high": "red",
    }
    risk_colors = {"none": "green", "low": "yellow", "medium": "orange1", "high": "red"}

    # Header panel
    p = result.primary
    status_color = status_colors.get(p.status, "white")
    risk_color = risk_colors.get(result.stuffing_risk.level, "white")

    console.print(
        Panel(
            f"[bold]Keyword:[/bold] {p.keyword} | "
            f"Density: [{status_color}]{p.density:.1f}%[/] (target: {p.target_density}%) | "
            f"Status: [{status_color}]{p.status.replace('_', ' ').title()}[/] | "
            f"Stuffing Risk: [{risk_color}]{result.stuffing_risk.level.title()}[/]",
            title="Keyword Analysis",
        )
    )

    # Placements table
    pl = p.placements
    place_table = Table(show_header=True, header_style="bold", title="Critical Placements")
    place_table.add_column("Location", width=20)
    place_table.add_column("Status", width=15)

    place_table.add_row(
        "H1 (Title)",
        "[green]✓ Found[/]" if pl.in_h1 else "[red]✗ Missing[/]"
    )
    place_table.add_row(
        "First 100 Words",
        "[green]✓ Found[/]" if pl.in_first_100_words else "[red]✗ Missing[/]"
    )
    place_table.add_row(
        "Conclusion",
        "[green]✓ Found[/]" if pl.in_conclusion else "[red]✗ Missing[/]"
    )
    if pl.h2_count > 0:
        h2_status = f"{pl.h2_with_keyword}/{pl.h2_count} H2s"
        h2_color = "green" if pl.h2_with_keyword >= 2 else "yellow" if pl.h2_with_keyword >= 1 else "red"
        place_table.add_row("H2 Headings", f"[{h2_color}]{h2_status}[/]")

    console.print(place_table)

    # Distribution table (if there are sections)
    if result.distribution:
        dist_table = Table(show_header=True, header_style="bold", title="Section Distribution")
        dist_table.add_column("Section", width=25)
        dist_table.add_column("Words", width=8)
        dist_table.add_column("Count", width=8)
        dist_table.add_column("Density", width=10)

        for section in result.distribution:
            density_color = "green" if section.density <= 3 else "yellow" if section.density <= 5 else "red"
            dist_table.add_row(
                section.section_name[:25],
                str(section.word_count),
                str(section.keyword_count),
                f"[{density_color}]{section.density:.1f}%[/]"
            )

        console.print(dist_table)

    # Secondary keywords (if any)
    if result.secondary:
        sec_table = Table(show_header=True, header_style="bold", title="Secondary Keywords")
        sec_table.add_column("Keyword", width=20)
        sec_table.add_column("Count", width=8)
        sec_table.add_column("Density", width=10)
        sec_table.add_column("Status", width=15)

        for s in result.secondary:
            s_color = status_colors.get(s.status, "white")
            sec_table.add_row(
                s.keyword,
                str(s.exact_matches),
                f"{s.density:.1f}%",
                f"[{s_color}]{s.status.replace('_', ' ').title()}[/]"
            )

        console.print(sec_table)

    # Stuffing warnings
    if result.stuffing_risk.warnings:
        console.print("\n[bold red]Stuffing Warnings:[/bold red]")
        for warning in result.stuffing_risk.warnings:
            console.print(f"  [red]⚠[/red] {warning}")

    # Recommendations
    if result.recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in result.recommendations:
            console.print(f"  [yellow]•[/yellow] {rec}")


if __name__ == "__main__":
    cli()
