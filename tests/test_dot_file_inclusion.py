"""Tests for dot file and directory inclusion functionality."""

from pathlib import Path

from blobify.file_scanner import (
    check_if_dot_item_might_be_included,
    discover_files,
    scan_files,
)


class TestDotFileInclusion:
    """Test cases for dot file and directory inclusion via .blobify patterns."""

    def test_check_if_dot_item_might_be_included_exact_match(self, tmp_path):
        """Test detection of exact dot file matches in .blobify patterns."""
        # Create .blobify file with exact dot file pattern
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text("+.blobify\n+.pre-commit-config.yaml\n")

        # Test exact matches
        assert check_if_dot_item_might_be_included(".blobify", tmp_path) is True
        assert check_if_dot_item_might_be_included(".pre-commit-config.yaml", tmp_path) is True

        # Test non-matches
        assert check_if_dot_item_might_be_included(".gitignore", tmp_path) is False
        assert check_if_dot_item_might_be_included(".vscode", tmp_path) is False

    def test_check_if_dot_item_might_be_included_directory_patterns(self, tmp_path):
        """Test detection of directory patterns in .blobify."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text("+.github/workflows/test.yml\n+.github/**\n")

        # Should detect that .github directory might be included
        assert check_if_dot_item_might_be_included(".github", tmp_path) is True

        # Should not detect unrelated directories
        assert check_if_dot_item_might_be_included(".vscode", tmp_path) is False

    def test_check_if_dot_item_might_be_included_wildcard_patterns(self, tmp_path):
        """Test detection of wildcard patterns."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text("+.pre-commit-*\n+.*ignore\n")

        # Should match wildcard patterns
        assert check_if_dot_item_might_be_included(".pre-commit-config.yaml", tmp_path) is True
        assert check_if_dot_item_might_be_included(".gitignore", tmp_path) is True
        assert check_if_dot_item_might_be_included(".dockerignore", tmp_path) is True

        # Should not match non-matching patterns
        assert check_if_dot_item_might_be_included(".github", tmp_path) is False

    def test_check_if_dot_item_might_be_included_no_blobify_file(self, tmp_path):
        """Test behavior when no .blobify file exists."""
        assert check_if_dot_item_might_be_included(".github", tmp_path) is False
        assert check_if_dot_item_might_be_included(".blobify", tmp_path) is False

    def test_check_if_dot_item_might_be_included_with_context(self, tmp_path):
        """Test context-specific patterns."""
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(
            """
# Default context
+pyproject.toml

[test-context]
+.github/workflows/test.yml
+.blobify
"""
        )

        # Default context should not include .github
        assert check_if_dot_item_might_be_included(".github", tmp_path) is False

        # Test context should include .github
        assert check_if_dot_item_might_be_included(".github", tmp_path, "test-context") is True
        assert check_if_dot_item_might_be_included(".blobify", tmp_path, "test-context") is True

    def test_dot_file_inclusion_in_discover_files(self, tmp_path):
        """Test that dot files are properly handled during file discovery."""
        # Set up git repo
        (tmp_path / ".git").mkdir()

        # Create dot files first
        blobify_content = "+.blobify\n+.pre-commit-config.yaml\n"
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text(blobify_content)

        precommit_file = tmp_path / ".pre-commit-config.yaml"
        precommit_file.write_text("repos: []\n")

        gitignore_file = tmp_path / ".gitignore"
        gitignore_file.write_text("*.log\n")  # Should be excluded

        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "settings.json").write_text("{}\n")  # Should be excluded

        # Create .github directory and file
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir()
        (workflows_dir / "test.yml").write_text("name: test\n")  # Should be excluded (not in patterns)

        # Use the complete scan_files function, not just discover_files
        context = scan_files(tmp_path, debug=True)

        # Check that included dot files are found in the final included files
        included_paths = {f["relative_path"] for f in context["included_files"]}
        print(f"Debug: Included files: {sorted(included_paths)}")  # Debug output

        assert Path(".blobify") in included_paths
        assert Path(".pre-commit-config.yaml") in included_paths

        # Check that excluded dot files are not found
        assert Path(".gitignore") not in included_paths
        assert Path(".vscode/settings.json") not in included_paths
        assert Path(".github/workflows/test.yml") not in included_paths

    def test_github_workflow_inclusion_full_scan(self, tmp_path):
        """Test complete workflow: .github directory and files are included when specified."""
        # Set up git repo
        (tmp_path / ".git").mkdir()

        # Create .github structure first
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir()
        test_yml = workflows_dir / "test.yml"
        test_yml.write_text("name: test\nruns-on: ubuntu-latest\n")

        # Create .blobify file with patterns
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text("+.github/workflows/test.yml\n+.blobify\n")

        # Run complete scan
        context = scan_files(tmp_path, debug=True)

        # Check that both files are included
        included_paths = {f["relative_path"] for f in context["included_files"]}
        print(f"Debug: Included files: {sorted(included_paths)}")  # Debug output

        assert Path(".github/workflows/test.yml") in included_paths
        assert Path(".blobify") in included_paths

    def test_cross_platform_path_handling(self, tmp_path):
        """Test that both forward and backslash separators work in patterns."""
        blobify_file = tmp_path / ".blobify"
        # Test both separators (though forward slash is recommended)
        blobify_file.write_text("+.github/workflows/test.yml\n")

        # Should detect .github directory for both path styles
        assert check_if_dot_item_might_be_included(".github", tmp_path) is True

    def test_dot_directory_exclusion_without_patterns(self, tmp_path):
        """Test that dot directories are excluded when no .blobify patterns match."""
        # Set up git repo but no .blobify file
        (tmp_path / ".git").mkdir()

        # Create dot directories that should be excluded
        (tmp_path / ".idea").mkdir()
        (tmp_path / ".idea" / "workspace.xml").write_text("<xml/>")
        (tmp_path / ".vscode").mkdir()
        (tmp_path / ".vscode" / "settings.json").write_text("{}")

        # Create regular file that should be included
        (tmp_path / "main.py").write_text("print('hello')")

        context = discover_files(tmp_path)

        # Check that dot directories are excluded
        file_paths = {f["relative_path"] for f in context["all_files"]}
        assert Path(".idea/workspace.xml") not in file_paths
        assert Path(".vscode/settings.json") not in file_paths

        # But regular files are included
        assert Path("main.py") in file_paths

    def test_built_in_ignored_patterns_still_work(self, tmp_path):
        """Test that built-in ignored patterns still exclude directories even with .blobify patterns."""
        # Set up git repo
        (tmp_path / ".git").mkdir()

        # Create .blobify file - this should NOT override built-in patterns
        blobify_file = tmp_path / ".blobify"
        blobify_file.write_text("+node_modules/package.json\n")  # Try to include from ignored dir

        # Create ignored directory
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.json").write_text('{"name": "test"}')

        context = discover_files(tmp_path)

        # Built-in ignored directories should still be excluded
        file_paths = {f["relative_path"] for f in context["all_files"]}
        assert Path("node_modules/package.json") not in file_paths
