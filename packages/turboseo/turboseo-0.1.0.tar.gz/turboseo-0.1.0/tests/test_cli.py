"""Tests for TurboSEO CLI."""

from click.testing import CliRunner

from turboseo.cli.main import cli


def test_cli_version():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help():
    """Test help output."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "TurboSEO" in result.output
    assert "check" in result.output
    assert "analyze" in result.output
