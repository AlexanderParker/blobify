"""Tests for the --list-patterns=ignored feature."""

from unittest.mock import patch

from blobify.main import list_ignored_patterns, main


class TestListIgnoredFeature:
    """Test cases for the --list-patterns=ignored command line option."""

    def test_list_ignored_patterns_option(self, capsys):
        """Test --list-patterns=ignored option."""
        with patch("sys.argv", ["bfy", "--list-patterns=ignored"]):
            main()

        captured = capsys.readouterr()
        assert "Built-in ignored patterns:" in captured.out
        assert "=" * 30 in captured.out
        assert ".git" in captured.out
        assert "node_modules" in captured.out
        assert "__pycache__" in captured.out

    def test_list_ignored_patterns_categories(self, capsys):
        """Test that patterns are properly categorised."""
        with patch("sys.argv", ["bfy", "--list-patterns=ignored"]):
            main()

        captured = capsys.readouterr()
        output = captured.out

        # Check dot folders section
        assert "Dot folders:" in output
        assert ".git" in output
        assert ".vscode" in output
        assert ".idea" in output

        # Check package manager section
        assert "Package manager directories:" in output
        assert "node_modules" in output
        assert "vendor" in output

        # Check Python section
        assert "Python environments & cache:" in output
        assert "__pycache__" in output
        assert ".venv" in output

        # Check build directories
        assert "Build directories:" in output
        assert "build" in output
        assert "dist" in output

        # Check security directories
        assert "Security & certificate directories:" in output
        assert "keys" in output
        assert ".ssh" in output

    def test_list_ignored_patterns_exits_early(self, tmp_path, capsys):
        """Test that --list-patterns=ignored exits without processing files."""
        # Create test files that would normally be processed
        (tmp_path / "test.py").write_text("print('should not be processed')")

        # Test that the --list-patterns=ignored flag works and doesn't process files
        with patch("sys.argv", ["bfy", str(tmp_path), "--list-patterns=ignored"]):
            main()

        # Verify that the list was printed (which means the function worked)
        captured = capsys.readouterr()
        assert "Built-in ignored patterns:" in captured.out

        # The key test: verify that the content of our test file doesn't appear
        # in the output, which means files weren't processed
        assert "print('should not be processed')" not in captured.out

    def test_list_ignored_patterns_with_other_flags_ignored(self, capsys):
        """Test that other flags are ignored when --list-patterns=ignored is used."""
        with patch("sys.argv", ["bfy", "--list-patterns=ignored", "--debug=true", "--copy-to-clipboard=true"]):
            main()

        captured = capsys.readouterr()
        # Should still show ignored patterns, other flags should be ignored
        assert "Built-in ignored patterns:" in captured.out
        assert "Dot folders:" in captured.out

    def test_list_ignored_patterns_function_output(self, capsys):
        """Test the list_ignored_patterns function directly."""
        list_ignored_patterns()

        captured = capsys.readouterr()
        output = captured.out

        # Check main structure
        assert "Built-in ignored patterns:" in output
        assert "=" * 30 in output

        # Check all expected categories are present
        expected_categories = [
            "Dot folders:",
            "Package manager directories:",
            "Python environments & cache:",
            "Build directories:",
            "Security & certificate directories:",
            "Other patterns:",
        ]

        for category in expected_categories:
            assert category in output

        # Check some specific patterns are present
        expected_patterns = [
            ".git",
            ".vscode",
            ".idea",  # dot folders
            "node_modules",
            "vendor",  # package managers
            "__pycache__",
            ".venv",  # python
            "build",
            "dist",  # build dirs
            "keys",
            ".ssh",  # security
            "package-lock.json",  # other
        ]

        for pattern in expected_patterns:
            assert pattern in output

    def test_list_ignored_patterns_function_sorted_output(self, capsys):
        """Test that patterns within categories are sorted."""
        list_ignored_patterns()

        captured = capsys.readouterr()
        output = captured.out

        # Find the dot folders section and check if it's sorted
        lines = output.split("\n")
        dot_folder_start = None
        dot_folder_patterns = []

        for i, line in enumerate(lines):
            if "Dot folders:" in line:
                dot_folder_start = i
            elif dot_folder_start and line.startswith("  "):
                pattern = line.strip()
                if pattern:  # Skip empty lines
                    dot_folder_patterns.append(pattern)
            elif dot_folder_start and not line.startswith("  ") and line.strip():
                # We've reached the next category
                break

        # Check that the patterns are sorted
        if dot_folder_patterns:
            assert dot_folder_patterns == sorted(dot_folder_patterns)

    def test_list_ignored_patterns_no_directory_needed(self, capsys):
        """Test that --list-patterns=ignored works without specifying a directory."""
        with patch("sys.argv", ["bfy", "--list-patterns=ignored"]):
            main()

        captured = capsys.readouterr()
        assert "Built-in ignored patterns:" in captured.out
        # Should not get directory error
        assert "directory argument is required" not in captured.err

    def test_list_ignored_patterns_comprehensive_coverage(self, capsys):
        """Test that all patterns from get_built_in_ignored_patterns are shown."""
        from blobify.file_scanner import get_built_in_ignored_patterns

        # Get actual patterns from the function
        actual_patterns = get_built_in_ignored_patterns()

        # Run list command
        with patch("sys.argv", ["bfy", "--list-patterns=ignored"]):
            main()

        captured = capsys.readouterr()
        output = captured.out

        # Check that every pattern appears in the output
        for pattern in actual_patterns:
            assert pattern in output, f"Pattern '{pattern}' not found in output"
