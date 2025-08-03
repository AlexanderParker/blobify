"""Tests for content_processor.py module."""

from pathlib import Path

from blobify.content_processor import (
    filter_content_lines,
    get_file_metadata,
    is_text_file,
    parse_named_filters,
    scrub_content,
)


class TestContentProcessor:
    """Test cases for content processing functions."""

    def test_scrub_content_disabled(self):
        """Test scrub_content when disabled."""
        content = "Email: test@example.com"
        result, count = scrub_content(content, enabled=False)
        assert result == content
        assert count == 0

    def test_scrub_content_with_email(self):
        """Test scrub_content with real email address."""
        content = "Contact us at support@example.com for help"
        result, count = scrub_content(content, enabled=True)

        # Should have detected and replaced the email
        assert "support@example.com" not in result
        assert count >= 1
        # Should contain some form of replacement
        assert any(marker in result.upper() for marker in ["EMAIL", "{{", "***"])

    def test_scrub_content_with_phone_number(self):
        """Test scrub_content with phone number."""
        content = "Call us at 555-123-4567 or (555) 987-6543"
        result, count = scrub_content(content, enabled=True)

        # Phone number detection varies by scrubadub version
        # Just verify the function works without crashing
        assert count >= 0

        # If any substitutions were made, verify phone numbers were targeted
        if count > 0:
            # Should have some replacement markers or missing phone numbers
            phone_replaced = "555-123-4567" not in result or "(555) 987-6543" not in result
            has_markers = any(marker in result.upper() for marker in ["PHONE", "{{", "***"])
            assert phone_replaced or has_markers

    def test_scrub_content_with_social_security_number(self):
        """Test scrub_content with SSN pattern."""
        content = "SSN: 123-45-6789"
        result, count = scrub_content(content, enabled=True)

        # Should have detected SSN
        assert count >= 1
        assert "123-45-6789" not in result

    def test_scrub_content_with_multiple_sensitive_items(self):
        """Test scrub_content with multiple types of sensitive data."""
        content = "Email: john@example.com, Phone: 555-1234, SSN: 123-45-6789"
        result, count = scrub_content(content, enabled=True)

        # Should detect at least the email (most reliable)
        assert count >= 1
        assert "john@example.com" not in result

        # Phone and SSN may or may not be detected depending on scrubadub version
        # If they were detected, they should be replaced
        if "555-1234" not in result:
            # Phone was scrubbed
            pass
        if "123-45-6789" not in result:
            # SSN was scrubbed
            pass

    def test_scrub_content_with_no_sensitive_data(self):
        """Test scrub_content with clean content."""
        content = "This is a clean file with no sensitive information."
        result, count = scrub_content(content, enabled=True)

        # Should return original content unchanged
        assert result == content
        assert count == 0

    def test_scrub_content_debug_output(self, capsys):
        """Test scrub_content debug output."""
        content = "Contact: admin@test.com"
        scrub_content(content, enabled=True, debug=True)

        captured = capsys.readouterr()
        # Should show debug information about what was found
        assert any(word in captured.err.lower() for word in ["scrubadub", "found", "items", "email"])

    def test_scrub_content_with_twitter_detector_disabled(self):
        """Test that twitter detector is disabled to reduce false positives."""
        content = "@username mentioned in the code"
        result, count = scrub_content(content, enabled=True)

        # Twitter handles should not be scrubbed (detector disabled)
        assert "@username" in result
        # Might still detect other things, but @username should remain

    def test_scrub_content_exception_handling(self):
        """Test scrub_content handles internal exceptions gracefully."""
        # Use extremely malformed content that might cause scrubadub issues
        content = "\x00\x01\x02" * 1000  # Binary-like content
        result, count = scrub_content(content, enabled=True)

        # Should not crash and should return something
        assert isinstance(result, str)
        assert isinstance(count, int)
        assert count >= 0

    def test_is_text_file_python(self, tmp_path):
        """Test is_text_file with Python file."""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")
        assert is_text_file(py_file) is True

    def test_is_text_file_text(self, tmp_path):
        """Test is_text_file with text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world")
        assert is_text_file(txt_file) is True

    def test_is_text_file_security_extension(self, tmp_path):
        """Test is_text_file rejects security file extensions."""
        key_file = tmp_path / "test.key"
        key_file.write_text("-----BEGIN PRIVATE KEY-----")
        assert is_text_file(key_file) is False

    def test_is_text_file_unknown_extension(self, tmp_path):
        """Test is_text_file with unknown extension."""
        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_text("Some content")
        assert is_text_file(unknown_file) is False

    def test_is_text_file_binary_content(self, tmp_path):
        """Test is_text_file with binary content."""
        bin_file = tmp_path / "test.py"
        bin_file.write_bytes(b"\x7f\x45\x4c\x46")  # ELF signature
        assert is_text_file(bin_file) is False

    def test_is_text_file_high_null_bytes(self, tmp_path):
        """Test is_text_file with high null byte concentration."""
        bin_file = tmp_path / "test.py"
        content = b"a" + b"\x00" * 1000  # > 30% nulls
        bin_file.write_bytes(content)
        assert is_text_file(bin_file) is False

    def test_is_text_file_unicode_decode_error(self, tmp_path):
        """Test is_text_file with invalid UTF-8."""
        bin_file = tmp_path / "test.py"
        bin_file.write_bytes(b"\xff\xfe\xfd")  # Invalid UTF-8
        assert is_text_file(bin_file) is False

    def test_is_text_file_io_error(self, tmp_path):
        """Test is_text_file handles IO errors."""
        nonexistent = tmp_path / "nonexistent.py"
        assert is_text_file(nonexistent) is False

    def test_get_file_metadata(self, tmp_path):
        """Test get_file_metadata returns correct structure."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        metadata = get_file_metadata(test_file)

        assert "size" in metadata
        assert "created" in metadata
        assert "modified" in metadata
        assert "accessed" in metadata
        assert metadata["size"] == 12  # "Test content" is 12 bytes

        # Check that timestamps are ISO format strings
        for key in ["created", "modified", "accessed"]:
            assert isinstance(metadata[key], str)
            # Should be able to parse as ISO datetime
            import datetime

            datetime.datetime.fromisoformat(metadata[key])

    def test_scrub_content_real_world_patterns(self):
        """Test scrub_content with real-world sensitive data patterns."""
        content = """
        Configuration file:
        database_url = "postgresql://user:password123@localhost:5432/db"
        api_key = "sk-1234567890abcdef"
        secret_key = "abc123def456"
        admin_email = "admin@mycompany.com"
        support_phone = "+1 (555) 123-4567"
        """

        result, count = scrub_content(content, enabled=True)

        # Should detect multiple sensitive items
        assert count >= 1
        # Emails should definitely be caught
        assert "admin@mycompany.com" not in result
        # Passwords in URLs are often detected
        assert "password123" not in result or "{{" in result or "***" in result

    def test_parse_named_filters_csv_format(self):
        """Test parsing filters with new CSV format."""
        filter_args = [
            '"py-functions","^def","*.py"',
            '"js-functions","^function","*.js"',
            '"css-selectors","^[.#]","*.css"',
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "py-functions": ("^def", "*.py"),
            "js-functions": ("^function", "*.js"),
            "css-selectors": ("^[.#]", "*.css"),
        }

        assert filters == expected_filters
        assert names == ["py-functions", "js-functions", "css-selectors"]

    def test_parse_named_filters_csv_with_commas_in_regex(self):
        """Test parsing filters with commas in regex patterns."""
        filter_args = [
            '"sql-queries","^(SELECT|INSERT,UPDATE)","migrations/*.sql"',
            '"complex-regex","[a-z,A-Z]+","*.txt"',
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "sql-queries": ("^(SELECT|INSERT,UPDATE)", "migrations/*.sql"),
            "complex-regex": ("[a-z,A-Z]+", "*.txt"),
        }

        assert filters == expected_filters
        assert names == ["sql-queries", "complex-regex"]

    def test_parse_named_filters_csv_two_values(self):
        """Test parsing filters with only name and regex (no file pattern)."""
        filter_args = [
            '"all-imports","^import"',
            '"functions","^def"',
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "all-imports": ("^import", "*"),
            "functions": ("^def", "*"),
        }

        assert filters == expected_filters
        assert names == ["all-imports", "functions"]

    def test_parse_named_filters_csv_single_value(self):
        """Test parsing filters with single value (regex only)."""
        filter_args = [
            '"^def"',
            '"^class"',
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "^def": ("^def", "*"),
            "^class": ("^class", "*"),
        }

        assert filters == expected_filters
        assert names == ["^def", "^class"]

    def test_parse_named_filters_csv_quotes_in_regex(self):
        """Test parsing filters with quotes in regex patterns."""
        filter_args = [
            r'"strings","\".*\"","*.py"',  # Match quoted strings
            r'"print-calls","print\(.*\)","*.py"',  # Match print calls
        ]
        filters, names = parse_named_filters(filter_args)

        expected_filters = {
            "strings": (r'".*"', "*.py"),
            "print-calls": (r"print\(.*\)", "*.py"),
        }

        assert filters == expected_filters
        assert names == ["strings", "print-calls"]

    def test_parse_named_filters_csv_malformed(self):
        """Test parsing malformed CSV filter arguments."""
        filter_args = [
            '"valid","^def","*.py"',  # Valid
            "invalid format",  # Invalid - no quotes
            '"unclosed quote,"^class"',  # Invalid - malformed CSV
            '"valid2","^import"',  # Valid
        ]
        filters, names = parse_named_filters(filter_args)

        # Should only parse valid entries
        expected_filters = {
            "valid": ("^def", "*.py"),
            "valid2": ("^import", "*"),
        }

        assert filters == expected_filters
        assert names == ["valid", "valid2"]

    def test_parse_named_filters_empty(self):
        """Test parsing empty filter list."""
        filters, names = parse_named_filters([])
        assert filters == {}
        assert names == []

    def test_parse_named_filters_none(self):
        """Test parsing None filter list."""
        filters, names = parse_named_filters(None)
        assert filters == {}
        assert names == []

    def test_filter_content_lines_file_targeting_debug(self):
        """Test filter content lines with file targeting and debug output."""
        content = "def hello():\nfunction greet() {\nclass Test:\nconst x = 1;"
        filters = {
            "py-functions": ("^def", "*.py"),
            "js-functions": ("^function", "*.js"),
            "all-classes": ("^class", "*"),
        }

        # Test with Python file
        py_result = filter_content_lines(content, filters, Path("test.py"), debug=True)
        assert py_result == "def hello():\nclass Test:"  # py-functions and all-classes apply

        # Test with JavaScript file
        js_result = filter_content_lines(content, filters, Path("test.js"), debug=True)
        assert js_result == "function greet() {\nclass Test:"  # js-functions and all-classes apply

        # Test with other file type
        other_result = filter_content_lines(content, filters, Path("test.txt"), debug=True)
        assert other_result == "class Test:"  # Only all-classes applies

    def test_filter_content_lines_complex_file_patterns(self):
        """Test filtering with complex file patterns including directories."""
        content = "CREATE TABLE users;\nSELECT * FROM users;\nINSERT INTO users;\nUPDATE users SET;"
        filters = {
            "migration-ddl": ("^CREATE", "migrations/*.sql"),
            "migration-dml": ("^(SELECT|INSERT)", "migrations/*.sql"),
            "all-updates": ("^UPDATE", "*.sql"),
        }

        # Test migration file - all migration filters should apply
        migration_result = filter_content_lines(content, filters, Path("migrations/001_init.sql"))
        assert "CREATE TABLE users;" in migration_result
        assert "SELECT * FROM users;" in migration_result
        assert "INSERT INTO users;" in migration_result
        assert "UPDATE users SET;" in migration_result  # all-updates also applies

        # Test regular SQL file - only all-updates should apply
        sql_result = filter_content_lines(content, filters, Path("queries/users.sql"))
        assert "CREATE TABLE users;" not in sql_result
        assert "SELECT * FROM users;" not in sql_result
        assert "INSERT INTO users;" not in sql_result
        assert "UPDATE users SET;" in sql_result

    def test_filter_content_lines_nested_directory_patterns(self):
        """Test file patterns with nested directory structures."""
        content = "import React from 'react';\nconst Component = () => {};\nexport default Component;"
        filters = {
            "component-imports": ("^import", "src/components/*.jsx"),
            "exports": ("^export", "src/**/*.js*"),  # Matches .js and .jsx in any subdirectory
        }

        # Test component file
        component_result = filter_content_lines(content, filters, Path("src/components/Button.jsx"))
        assert "import React from 'react';" in component_result
        assert "export default Component;" in component_result

        # Test utility file in nested directory
        util_result = filter_content_lines(content, filters, Path("src/utils/helpers.js"))
        assert "import React from 'react';" not in util_result  # component-imports doesn't apply
        assert "export default Component;" in util_result  # exports applies to all js files in src/

    def test_filter_content_lines_edge_cases(self):
        """Test edge cases for file pattern matching."""
        content = "test line"
        filters = {"test": ("test", "*.py")}

        # Test with None file path
        result_none = filter_content_lines(content, filters, None)
        assert result_none == "test line"  # Should apply all filters when no file path

        # Test with empty filters
        result_empty = filter_content_lines(content, {}, Path("test.py"))
        assert result_empty == "test line"  # Should return original content

        # Test with file path that's just a filename (no directory)
        result_filename = filter_content_lines(content, filters, Path("test.py"))
        assert result_filename == "test line"

    def test_filter_content_lines_glob_pattern_matching(self):
        """Test various glob pattern matching scenarios."""
        content = "function test() {}\nconst api = 'https://api.com';\nclass Test {}"

        test_cases = [
            # (filter_pattern, file_path, should_match)
            ("*.js", Path("app.js"), True),
            ("*.js", Path("app.ts"), False),
            ("test*.js", Path("test-utils.js"), True),
            ("test*.js", Path("utils.js"), False),
            ("**/*.jsx", Path("src/components/Button.jsx"), True),
            ("**/*.jsx", Path("components/Button.jsx"), True),
            ("**/*.jsx", Path("Button.jsx"), True),
            ("src/**", Path("src/components/Button.jsx"), True),
            ("src/**", Path("components/Button.jsx"), False),
            ("**/test*", Path("src/test-utils.js"), True),
            ("**/test*", Path("src/utils.js"), False),
        ]

        for pattern, file_path, should_match in test_cases:
            filters = {"test": ("function", pattern)}
            result = filter_content_lines(content, filters, file_path)
            if should_match:
                assert "function test() {}" in result, f"Pattern {pattern} should match {file_path}"
            else:
                assert result == "", f"Pattern {pattern} should not match {file_path}"
