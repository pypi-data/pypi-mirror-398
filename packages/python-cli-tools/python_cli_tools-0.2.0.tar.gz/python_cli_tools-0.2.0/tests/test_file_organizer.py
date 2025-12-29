"""
Comprehensive test suite for the File Organizer application.

This module tests:
- Directory validation in FileOrganizer.__init__
- File organization by extension
- Handling of files without extensions
- Handling of uppercase extensions
- Handling of multi-dot filenames
- Ignoring nested directories
- Idempotent behavior (running organize() twice)
- CLI behavior and argument parsing

All filesystem operations use temporary directories to ensure isolation.
"""

import os
import shutil
import tempfile
import argparse
import pytest
from unittest.mock import patch

from file_organizer.file_organizer import FileOrganizer


# ============================================================
# Helper
# ============================================================


def create_temp_files(base_dir, files):
    """Create dummy files inside a temporary directory."""
    for f in files:
        with open(os.path.join(base_dir, f), "w") as fp:
            fp.write("dummy content")


# ============================================================
# Constructor tests
# ============================================================


def test_invalid_directory():
    """Ensure FileOrganizer raises ValueError for invalid directory paths."""
    with pytest.raises(ValueError):
        FileOrganizer("not_a_real_dir")


# ============================================================
# Core organize() tests
# ============================================================


def test_organize_creates_folders_and_moves_files():
    """Test that files are moved into extension-based folders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["doc1.txt", "image1.jpg", "archive1.zip", "noext"]
        create_temp_files(tmpdir, files)

        organizer = FileOrganizer(tmpdir)
        organizer.organize()

        # Check that folders were created
        assert os.path.isdir(os.path.join(tmpdir, "txt"))
        assert os.path.isdir(os.path.join(tmpdir, "jpg"))
        assert os.path.isdir(os.path.join(tmpdir, "zip"))
        assert os.path.isdir(os.path.join(tmpdir, "no_extension"))

        # Check that files were moved
        for f in files:
            ext = os.path.splitext(f)[1].lower().strip(".")
            if not ext:
                ext = "no_extension"
            target_path = os.path.join(tmpdir, ext, f)
            assert os.path.isfile(target_path)


def test_no_files_in_directory():
    """Ensure no folders are created when directory is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        organizer = FileOrganizer(tmpdir)
        organizer.organize()
        assert len(os.listdir(tmpdir)) == 0


def test_uppercase_extensions():
    """Ensure uppercase extensions are normalized to lowercase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["A.TXT", "B.JPG", "C.ZIP"]
        create_temp_files(tmpdir, files)

        organizer = FileOrganizer(tmpdir)
        organizer.organize()

        assert os.path.isfile(os.path.join(tmpdir, "txt", "A.TXT"))
        assert os.path.isfile(os.path.join(tmpdir, "jpg", "B.JPG"))
        assert os.path.isfile(os.path.join(tmpdir, "zip", "C.ZIP"))


def test_multiple_dots_extension():
    """Ensure files with multiple dots use the last extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["archive.tar.gz"]
        create_temp_files(tmpdir, files)

        organizer = FileOrganizer(tmpdir)
        organizer.organize()

        assert os.path.isfile(os.path.join(tmpdir, "gz", "archive.tar.gz"))


def test_dotfile_no_extension():
    """Ensure dotfiles (e.g., .env) are treated as no_extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = [".env"]
        create_temp_files(tmpdir, files)

        organizer = FileOrganizer(tmpdir)
        organizer.organize()

        assert os.path.isfile(os.path.join(tmpdir, "no_extension", ".env"))


def test_nested_directories_are_ignored():
    """Ensure nested directories are not modified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "nested"))
        create_temp_files(os.path.join(tmpdir, "nested"), ["inside.txt"])
        create_temp_files(tmpdir, ["root.txt"])

        organizer = FileOrganizer(tmpdir)
        organizer.organize()

        # root file moved
        assert os.path.isfile(os.path.join(tmpdir, "txt", "root.txt"))

        # nested file untouched
        assert os.path.isfile(os.path.join(tmpdir, "nested", "inside.txt"))


def test_reorganize_is_idempotent():
    """Ensure running organize() twice does not break structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = ["a.txt", "b.txt"]
        create_temp_files(tmpdir, files)

        organizer = FileOrganizer(tmpdir)
        organizer.organize()
        organizer.organize()  # run twice

        txt_dir = os.path.join(tmpdir, "txt")
        assert os.path.isdir(txt_dir)
        assert len(os.listdir(txt_dir)) == 2


# ============================================================
# CLI tests
# ============================================================


def test_cli_invocation(capsys):
    """Test CLI invocation with a valid directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        create_temp_files(tmpdir, ["a.txt"])

        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(directory=tmpdir),
        ):
            from file_organizer.file_organizer import main

            main()

        captured = capsys.readouterr()
        assert "Moved:" in captured.out
