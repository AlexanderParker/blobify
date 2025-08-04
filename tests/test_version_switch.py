"""Tests for the --version/-v command line switch."""

from unittest.mock import patch

from blobify.main import __version__, main


class TestVersionSwitch:
    """Test cases for the --version/-v command line option."""

    def test_version_long_flag(self, capsys):
        """Test --version flag shows version and exits."""
        with patch("sys.argv", ["bfy", "--version"]):
            main()

        captured = capsys.readouterr()
        assert "blobify " + __version__ in captured.out
        # Should not process any files or show other output
        assert "Processed" not in captured.err
        assert "# Blobify Text File Index" not in captured.out

    def test_version_short_flag(self, capsys):
        """Test -v flag shows version and exits."""
        with patch("sys.argv", ["bfy", "-v"]):
            main()

        captured = capsys.readouterr()
        assert "blobify " + __version__ in captured.out
        # Should not process any files or show other output
        assert "Processed" not in captured.err
        assert "# Blobify Text File Index" not in captured.out

    def test_version_with_directory_ignored(self, tmp_path, capsys):
        """Test that --version ignores directory argument and other flags."""
        # Create test files that would normally be processed
        (tmp_path / "test.py").write_text("print('should not be processed')")

        with patch("sys.argv", ["bfy", str(tmp_path), "--version", "--debug=true"]):
            main()

        captured = capsys.readouterr()
        assert "blobify " + __version__ in captured.out
        # Should not process files despite directory being provided
        assert "print('should not be processed')" not in captured.out
        assert "Processed" not in captured.err

    def test_version_takes_precedence_over_other_flags(self, tmp_path, capsys):
        """Test that --version takes precedence over other operations."""
        # Create git repo with .blobify
        (tmp_path / ".git").mkdir()
        (tmp_path / ".blobify").write_text(
            """
[test-context]
+*.py
"""
        )
        (tmp_path / "test.py").write_text("print('test')")

        # Test with context flag
        with patch("sys.argv", ["bfy", str(tmp_path), "-x", "test-context", "--version"]):
            main()

        captured = capsys.readouterr()
        assert "blobify " + __version__ in captured.out
        assert "Available contexts:" not in captured.out
        assert "print('test')" not in captured.out

        # Test with list patterns
        capsys.readouterr()  # Clear previous output
        with patch("sys.argv", ["bfy", "--list-patterns=ignored", "--version"]):
            main()

        captured = capsys.readouterr()
        assert "blobify " + __version__ in captured.out
        assert "Built-in ignored patterns:" not in captured.out

    def test_version_output_format(self, capsys):
        """Test that version output has correct format."""
        with patch("sys.argv", ["bfy", "--version"]):
            main()

        captured = capsys.readouterr()
        # Should be simple format: "blobify <version>"
        lines = captured.out.strip().split("\n")
        assert len(lines) == 1
        assert lines[0] == "blobify " + __version__

    def test_version_exits_cleanly(self, capsys):
        """Test that --version exits without errors."""
        # Should not raise any exceptions
        with patch("sys.argv", ["bfy", "--version"]):
            main()

        captured = capsys.readouterr()
        assert "blobify " + __version__ in captured.out
        # Should not show any error messages
        assert "Error:" not in captured.err
