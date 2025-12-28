"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner
from icon_gen.cli import main


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Generate icons from Iconify' in result.output


def test_cli_basic_generation():
    """Test basic icon generation via CLI."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ['mdi:github', '--size', '64'])
        assert result.exit_code == 0
        assert 'Success' in result.output