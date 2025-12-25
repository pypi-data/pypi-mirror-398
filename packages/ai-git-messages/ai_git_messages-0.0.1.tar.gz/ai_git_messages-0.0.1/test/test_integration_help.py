#!/usr/bin/env python3

"""
Integration test for ai-git-messages --help functionality.

This test ensures we're testing the local package code, not any
installed version elsewhere on the system.
"""

import sys
import pytest
from io import StringIO

# Import from the local package (conftest.py adds src/ to sys.path)
from ai_git_messages.ai_git_messages import main


def test_help_flag_produces_output(monkeypatch, capsys):
    """
    Test that running with --help produces help output.

    Verifies:
    - The --help flag is recognized
    - Help text is printed to stdout/stderr
    - The program exits cleanly (SystemExit with code 0)
    """
    # Set up sys.argv to simulate running: ai-git-messages --help
    monkeypatch.setattr(sys, 'argv', ['ai-git-messages', '--help'])

    # --help causes argparse to call sys.exit(0), so we expect SystemExit
    with pytest.raises(SystemExit) as exc_info:
        main()

    # Verify it exits with code 0 (success)
    assert exc_info.value.code == 0, "Expected --help to exit with code 0"

    # Capture the output
    captured = capsys.readouterr()

    # Help text goes to stdout by default with argparse
    help_output = captured.out + captured.err

    # Verify that help text contains expected content
    assert len(help_output) > 0, "Expected --help to produce output"
    assert 'usage:' in help_output.lower(), "Expected help text to contain 'usage:'"

    # Verify it mentions the program name or key arguments
    assert any(keyword in help_output.lower() for keyword in [
        'ai-git-messages',
        'ollama',
        'cursor',
        'claude',
        'pr-description',
        'branch-off-main'
    ]), "Expected help text to mention key program features"


def test_help_short_flag_produces_output(monkeypatch, capsys):
    """
    Test that running with -h also produces help output.
    """
    # Set up sys.argv to simulate running: ai-git-messages -h
    monkeypatch.setattr(sys, 'argv', ['ai-git-messages', '-h'])

    # -h also causes argparse to call sys.exit(0)
    with pytest.raises(SystemExit) as exc_info:
        main()

    # Verify it exits with code 0 (success)
    assert exc_info.value.code == 0, "Expected -h to exit with code 0"

    # Capture the output
    captured = capsys.readouterr()
    help_output = captured.out + captured.err

    # Verify output is not empty
    assert len(help_output) > 0, "Expected -h to produce output"
    assert 'usage:' in help_output.lower(), "Expected help text to contain 'usage:'"


def test_version_flag_produces_output(monkeypatch, capsys):
    """
    Test that running with --version produces version output.
    """
    # Set up sys.argv to simulate running: ai-git-messages --version
    monkeypatch.setattr(sys, 'argv', ['ai-git-messages', '--version'])

    # --version causes argparse to call sys.exit(0)
    with pytest.raises(SystemExit) as exc_info:
        main()

    # Verify it exits with code 0 (success)
    assert exc_info.value.code == 0, "Expected --version to exit with code 0"

    # Capture the output
    captured = capsys.readouterr()
    version_output = captured.out + captured.err

    # Verify output contains version information
    assert len(version_output) > 0, "Expected --version to produce output"
    assert 'ai-git-messages' in version_output.lower(), "Expected version output to mention package name"

    # Check that it contains something that looks like a version
    # (could be "0.0.1.dev0+d20251223" or "unknown (not installed)")
    assert any(indicator in version_output.lower() for indicator in [
        '0.', '1.', '2.', 'unknown', 'dev'
    ]), "Expected version output to contain version information"


def test_version_short_flag_produces_output(monkeypatch, capsys):
    """
    Test that running with -V also produces version output.
    """
    # Set up sys.argv to simulate running: ai-git-messages -V
    monkeypatch.setattr(sys, 'argv', ['ai-git-messages', '-V'])

    # -V also causes argparse to call sys.exit(0)
    with pytest.raises(SystemExit) as exc_info:
        main()

    # Verify it exits with code 0 (success)
    assert exc_info.value.code == 0, "Expected -V to exit with code 0"

    # Capture the output
    captured = capsys.readouterr()
    version_output = captured.out + captured.err

    # Verify output is not empty
    assert len(version_output) > 0, "Expected -V to produce output"
    assert 'ai-git-messages' in version_output.lower(), "Expected version output to mention package name"
