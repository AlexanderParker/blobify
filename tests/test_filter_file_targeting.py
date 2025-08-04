"""Tests for file-targeted filter functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

from blobify.content_processor import filter_content_lines, parse_named_filters
from blobify.main import main


class TestFileTargetedFilters:
    """Test cases for file-targeted filter functionality."""

    def test_parse_named_filters_with_file_patterns(self):
        """Test parsing filters with file patterns."""
        filter_args = [
            '"py-functions","^def","*.py"',
            '"js-functions","^function","*.js"',
            '"all-imports","^import","*"',
            '"css-selectors","^\\..*","*.css"',
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "py-functions": ("^def", "*.py"),
            "js-functions": ("^function", "*.js"),
            "all-imports": ("^import", "*"),
            "css-selectors": ("^\\..*", "*.css"),
        }

        assert filters == expected_filters
        assert names == ["py-functions", "js-functions", "all-imports", "css-selectors"]

    def test_parse_named_filters_mixed_with_and_without_file_patterns(self):
        """Test parsing mix of filters with and without file patterns."""
        filter_args = [
            '"py-functions","^def","*.py"',
            '"all-classes","^class"',
            '"js-errors","catch","*.js"',
        ]  # No file pattern
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "py-functions": ("^def", "*.py"),
            "all-classes": ("^class", "*"),  # Default to all files
            "js-errors": ("catch", "*.js"),
        }

        assert filters == expected_filters
        assert names == ["py-functions", "all-classes", "js-errors"]

    def test_parse_named_filters_fallback_with_colons_in_regex(self):
        """Test parsing filters with colons in regex patterns."""
        filter_args = [
            '"urls","https?://\\S+","*.md"',  # URL pattern with colon
            '"times","\\d{2}:\\d{2}","*.log"',  # Time pattern with colons
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {"urls": ("https?://\\S+", "*.md"), "times": ("\\d{2}:\\d{2}", "*.log")}

        assert filters == expected_filters

    def test_filter_content_lines_with_file_pattern_match(self):
        """Test filtering content when file pattern matches."""
        content = "def hello():\n    print('world')\nclass MyClass:\n    pass"
        filters = {"functions": ("^def", "*.py")}
        file_path = Path("test.py")

        result = filter_content_lines(content, filters, file_path)
        assert result == "def hello():"

    def test_filter_content_lines_with_file_pattern_no_match(self):
        """Test filtering content when file pattern doesn't match."""
        content = "def hello():\n    print('world')\nclass MyClass:\n    pass"
        filters = {"functions": ("^def", "*.py")}
        file_path = Path("test.js")  # Doesn't match *.py

        result = filter_content_lines(content, filters, file_path)
        assert result == ""  # No filters applied, so no matches

    def test_filter_content_lines_multiple_filters_different_files(self):
        """Test multiple filters targeting different file types."""
        content = "def hello():\nfunction greet() {\nclass MyClass:\nconst x = 1;"
        filters = {
            "py-functions": ("^def", "*.py"),
            "js-functions": ("^function", "*.js"),
            "py-classes": ("^class", "*.py"),
        }

        # Test Python file
        py_result = filter_content_lines(content, filters, Path("test.py"))
        assert py_result == "def hello():\nclass MyClass:"

        # Test JavaScript file
        js_result = filter_content_lines(content, filters, Path("test.js"))
        assert js_result == "function greet() {"

    def test_filter_content_lines_wildcard_file_pattern(self):
        """Test filtering with wildcard file pattern applies to all files."""
        content = "import os\nimport sys\nfrom pathlib import Path"
        filters = {"imports": ("^(import|from)", "*")}

        result = filter_content_lines(content, filters, Path("any_file.xyz"))
        assert "import os" in result
        assert "import sys" in result
        assert "from pathlib import Path" in result

    def test_filter_content_lines_complex_file_patterns(self):
        """Test filtering with complex file patterns."""
        content = "SELECT * FROM users;\nINSERT INTO table;\nUPDATE users SET;"
        filters = {"queries": ("^(SELECT|INSERT)", "migrations/*.sql"), "updates": ("^UPDATE", "*.sql")}

        # Test file matching migrations pattern
        migration_result = filter_content_lines(content, filters, Path("migrations/001_init.sql"))
        assert "SELECT * FROM users;" in migration_result
        assert "INSERT INTO table;" in migration_result
        assert "UPDATE users SET;" in migration_result  # Both filters apply

        # Test file matching only *.sql pattern
        sql_result = filter_content_lines(content, filters, Path("query.sql"))
        assert "SELECT * FROM users;" not in sql_result  # queries filter doesn't apply
        assert "INSERT INTO table;" not in sql_result
        assert "UPDATE users SET;" in sql_result  # Only updates filter applies

    def test_filter_content_lines_no_file_path_applies_all(self):
        """Test that when no file path is provided, all filters apply."""
        content = "def hello():\nfunction greet() {\nclass MyClass:"
        filters = {
            "py-functions": ("^def", "*.py"),
            "js-functions": ("^function", "*.js"),
            "classes": ("^class", "*.py"),
        }

        # No file path provided - should apply all filters
        result = filter_content_lines(content, filters, None)
        assert "def hello():" in result
        assert "function greet() {" in result
        assert "class MyClass:" in result


class TestFileTargetedFiltersIntegration:
    """Integration tests for file-targeted filters with main blobify functionality."""

    def setup_multi_language_project(self, tmp_path):
        """Create a multi-language test project."""
        # Create git repository
        (tmp_path / ".git").mkdir(exist_ok=True)

        # Create .blobify to explicitly include SQL files (since they're security extensions)
        (tmp_path / ".blobify").write_text(
            """
+*.py
+*.js
+*.css
+migrations/*.sql
+*.sql
"""
        )

        # Python files
        (tmp_path / "app.py").write_text(
            """def main():
    print("Hello from Python")
    return True

class Application:
    def __init__(self):
        pass

import os
import sys
"""
        )

        (tmp_path / "models.py").write_text(
            """class User:
    def __init__(self, name):
        self.name = name

def create_user(name):
    return User(name)
"""
        )

        # JavaScript files
        (tmp_path / "app.js").write_text(
            """function main() {
    console.log("Hello from JavaScript");
    return true;
}

class Application {
    constructor() {}
}

const API_URL = "https://api.example.com";
"""
        )

        # CSS files
        (tmp_path / "styles.css").write_text(
            """.header {
    background: blue;
}

#main-content {
    padding: 20px;
}

.button:hover {
    color: red;
}
"""
        )

        # SQL migration
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        (migrations_dir / "001_init.sql").write_text(
            """CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

INSERT INTO users (name) VALUES ('admin');
SELECT * FROM users WHERE name = 'admin';
"""
        )

        return tmp_path

    def test_python_specific_filters(self, tmp_path):
        """Test filters that only target Python files."""
        self.setup_multi_language_project(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"py-functions","^def","*.py"',
                "--filter",
                '"py-classes","^class","*.py"',
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should show filters in header with file patterns
        assert "py-functions: ^def (files: *.py)" in content
        assert "py-classes: ^class (files: *.py)" in content

        # Should include Python functions and classes
        assert "def main():" in content
        assert "def create_user(name):" in content
        assert "class Application:" in content
        assert "class User:" in content

        # Should NOT include JavaScript functions/classes or other content
        assert "function main() {" not in content
        assert "console.log" not in content
        assert ".header {" not in content
        assert "CREATE TABLE" not in content

    def test_javascript_specific_filters(self, tmp_path):
        """Test filters that only target JavaScript files."""
        self.setup_multi_language_project(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"js-functions","^function","*.js"',
                "--filter",
                '"js-classes","^class","*.js"',
                "--filter",
                '"js-constants","^const","*.js"',
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include JavaScript content
        assert "function main() {" in content
        assert "class Application {" in content
        assert "const API_URL" in content

        # Should NOT include Python content
        assert "def main():" not in content
        assert "import os" not in content
        assert "class User:" not in content

    def test_css_selector_filters(self, tmp_path):
        """Test filters targeting CSS selectors."""
        self.setup_multi_language_project(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"css-selectors","^[.#]","*.css"',
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include CSS selectors
        assert ".header {" in content
        assert "#main-content {" in content
        assert ".button:hover {" in content

        # Should NOT include other content
        assert "def main():" not in content
        assert "function main() {" not in content

    def test_migration_sql_filters(self, tmp_path):
        """Test filters targeting SQL in migration files."""
        self.setup_multi_language_project(tmp_path)

        # Debug: Check what files were actually created
        print(f"Debug - Files created: {[str(p.relative_to(tmp_path)) for p in tmp_path.rglob('*') if p.is_file()]}")

        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"sql-ddl","^(CREATE|ALTER)","migrations/*.sql"',
                "--filter",
                '"sql-dml","^(INSERT|SELECT)","migrations/*.sql"',
                "--debug=true",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Debug: Print what was actually generated
        print(f"Debug - Generated content preview: {content[:1000]}...")

        # Should include SQL statements from migration files
        assert "CREATE TABLE users" in content
        assert "INSERT INTO users" in content
        assert "SELECT * FROM users" in content

        # Should NOT include other content
        assert "def main():" not in content
        assert "function main() {" not in content

    def test_cross_language_analysis(self, tmp_path):
        """Test combining filters across different languages."""
        self.setup_multi_language_project(tmp_path)
        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"backend-functions","^def","*.py"',
                "--filter",
                '"frontend-functions","^function","*.js"',
                "--filter",
                '"styles","^[.#]","*.css"',
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should include content from all targeted file types
        assert "def main():" in content  # Python
        assert "function main() {" in content  # JavaScript
        assert ".header {" in content  # CSS

        # Should show all filters in header
        assert "backend-functions: ^def (files: *.py)" in content
        assert "frontend-functions: ^function (files: *.js)" in content
        assert "styles: ^[.#] (files: *.css)" in content

    def test_file_pattern_with_directory_paths(self, tmp_path):
        """Test file patterns that include directory paths."""
        self.setup_multi_language_project(tmp_path)

        # Create additional SQL file outside migrations
        (tmp_path / "query.sql").write_text("SELECT COUNT(*) FROM users;")

        # Debug: Check what files exist
        print(f"Debug - All files: {[str(p.relative_to(tmp_path)) for p in tmp_path.rglob('*') if p.is_file()]}")

        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"migration-sql","^(CREATE|INSERT)","migrations/*.sql"',
                "--filter",
                '"all-sql","^SELECT","*.sql"',
                "--debug=true",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Debug: Print what was actually generated
        print(f"Debug - Generated content preview: {content[:1000]}...")

        # Migration-specific filter should only apply to files in migrations/
        assert "CREATE TABLE users" in content  # From migrations/001_init.sql
        assert "INSERT INTO users" in content  # From migrations/001_init.sql

        # All-sql filter should apply to both migration and regular SQL files
        assert "SELECT * FROM users" in content  # From migrations/001_init.sql
        assert "SELECT COUNT(*) FROM users;" in content  # From query.sql

    def test_filter_exclusion_by_file_pattern(self, tmp_path):
        """Test that files excluded by filter patterns show correct status."""
        self.setup_multi_language_project(tmp_path)

        # Debug: Check what files exist
        all_files = [str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file()]
        print(f"Debug - All files: {all_files}")

        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            [
                "bfy",
                str(tmp_path),
                "--filter",
                '"py-only","^def","*.py"',
                "--debug=true",
                "--output-filename",
                str(output_file),
            ],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Debug: Print what was actually generated
        print(f"Debug - Generated content preview: {content[:1500]}...")

        # Python files should have content
        assert "app.py" in content
        assert "models.py" in content
        assert "def main():" in content

        # Based on the debug output, files that don't match filters show:
        # "[Content excluded - no lines matched filters]" in the content section
        # So check for this pattern instead
        assert "[Content excluded - no lines matched filters]" in content

    def test_blobify_config_with_file_targeted_filters(self, tmp_path):
        """Test file-targeted filters in .blobify configuration."""

        self.setup_multi_language_project(tmp_path)

        # Create custom .blobify with file-targeted filters (overwrite the one from setup)
        (tmp_path / ".blobify").write_text(
            """
@filter="py-functions","^def","*.py"
@filter="js-functions","^function","*.js"
@filter="css-selectors","^[.#]","*.css"
+*.py
+*.js
+*.css
"""
        )

        output_file = tmp_path / "output.txt"

        with patch("sys.argv", ["bfy", str(tmp_path), "--output-filename", str(output_file)]):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should apply all default filters with file targeting
        assert "py-functions: ^def (files: *.py)" in content
        assert "js-functions: ^function (files: *.js)" in content
        assert "css-selectors: ^[.#] (files: *.css)" in content

        # Should include targeted content from each file type
        assert "def main():" in content
        assert "function main() {" in content
        assert ".header {" in content

    def test_command_line_override_with_file_patterns(self, tmp_path):
        """Test command line filters with file patterns override .blobify defaults."""

        self.setup_multi_language_project(tmp_path)

        # Create .blobify with default filter (overwrite the one from setup)
        (tmp_path / ".blobify").write_text(
            """
@filter="all-functions","^(def|function)"
+*.py
+*.js
"""
        )

        output_file = tmp_path / "output.txt"

        with patch(
            "sys.argv",
            ["bfy", str(tmp_path), "--filter", '"py-only","^def","*.py"', "--output-filename", str(output_file)],
        ):
            main()

        content = output_file.read_text(encoding="utf-8")

        # Should have both default and command line filters
        assert "all-functions: ^(def|function)" in content  # Default filter (no file restriction)
        assert "py-only: ^def (files: *.py)" in content  # Command line filter

        # Default filter should match functions in both Python and JavaScript
        # Command line filter should only match Python functions
        assert "def main():" in content  # Matches both filters
        assert "function main() {" in content  # Matches only default filter


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
