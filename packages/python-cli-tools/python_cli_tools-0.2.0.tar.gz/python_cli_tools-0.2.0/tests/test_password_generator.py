"""
Comprehensive test suite for the Password Generator application.

This module tests:
- PasswordGenerator class behavior (length, character sets, edge cases)
- CLI argument parsing and output generation
- Deterministic behavior via mocking random.choice
"""

import argparse
import pytest
from unittest.mock import patch

from password_generator.password_generator import PasswordGenerator


# ============================================================
# PasswordGenerator class tests
# ============================================================


def test_default_password_length():
    """Ensure the default password length is 12 characters."""
    gen = PasswordGenerator()
    pwd = gen.generate()
    assert len(pwd) == 12


def test_custom_length():
    """Ensure custom password length is respected."""
    gen = PasswordGenerator(length=20)
    pwd = gen.generate()
    assert len(pwd) == 20


def test_no_digits():
    """Ensure digits are excluded when use_digits=False."""
    gen = PasswordGenerator(use_digits=False)
    pwd = gen.generate()
    assert all(ch not in "0123456789" for ch in pwd)


def test_no_specials():
    """Ensure special characters are excluded when use_specials=False."""
    gen = PasswordGenerator(use_specials=False)
    pwd = gen.generate()
    specials = "!@#$%^&*()-_=+[]{};:,.<>?/"
    assert all(ch not in specials for ch in pwd)


def test_letters_only():
    """Ensure password contains only letters when digits and specials are disabled."""
    gen = PasswordGenerator(use_digits=False, use_specials=False)
    pwd = gen.generate()
    assert all(ch.isalpha() for ch in pwd)


def test_digits_only():
    """Ensure password contains only digits when letters and specials are disabled."""
    gen = PasswordGenerator(use_specials=False)
    gen.use_digits = True
    gen.use_specials = False
    gen.length = 10

    # Override letters to empty to force digits-only
    with patch("string.ascii_letters", ""):
        pwd = gen.generate()
        assert all(ch.isdigit() for ch in pwd)


def test_min_length():
    """Ensure generator supports minimum length of 1."""
    gen = PasswordGenerator(length=1)
    pwd = gen.generate()
    assert len(pwd) == 1


def test_generate_deterministic_with_mock():
    """Ensure deterministic output when random.choice is mocked."""
    with patch("random.choice", return_value="X"):
        gen = PasswordGenerator(length=5)
        pwd = gen.generate()
        assert pwd == "XXXXX"


# ============================================================
# CLI tests
# ============================================================


def test_cli_default_length(capsys):
    """Test CLI with default settings."""
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(length=12, no_digits=False, no_specials=False),
        ),
        patch(
            "password_generator.password_generator.PasswordGenerator.generate",
            return_value="ABC123!@#XYZ",
        ),
    ):
        from password_generator.password_generator import main

        main()
        captured = capsys.readouterr()
        assert "ABC123!@#XYZ" in captured.out


def test_cli_no_digits(capsys):
    """Test CLI when --no-digits flag is used."""
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(length=8, no_digits=True, no_specials=False),
        ),
        patch(
            "password_generator.password_generator.PasswordGenerator.generate",
            return_value="Ab!Cd!Ef",
        ),
    ):
        from password_generator.password_generator import main

        main()
        captured = capsys.readouterr()
        assert "Ab!Cd!Ef" in captured.out


def test_cli_no_specials(capsys):
    """Test CLI when --no-specials flag is used."""
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(length=8, no_digits=False, no_specials=True),
        ),
        patch(
            "password_generator.password_generator.PasswordGenerator.generate",
            return_value="Ab12Cd34",
        ),
    ):
        from password_generator.password_generator import main

        main()
        captured = capsys.readouterr()
        assert "Ab12Cd34" in captured.out


def test_cli_custom_length(capsys):
    """Test CLI with custom length argument."""
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(length=5, no_digits=False, no_specials=False),
        ),
        patch(
            "password_generator.password_generator.PasswordGenerator.generate", return_value="ABCDE"
        ),
    ):
        from password_generator.password_generator import main

        main()
        captured = capsys.readouterr()
        assert "ABCDE" in captured.out
