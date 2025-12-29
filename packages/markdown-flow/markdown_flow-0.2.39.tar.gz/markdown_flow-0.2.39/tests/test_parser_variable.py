"""
Unit tests for parser.variable module
"""

import pytest

from markdown_flow.parser import extract_variables_from_text, replace_variables_in_text


class TestExtractVariables:
    """Test variable extraction functionality."""

    def test_extract_brace_variables(self):
        """Test extracting {{variable}} format."""
        text = "Hello {{name}}, you are {{age}} years old"
        variables = extract_variables_from_text(text)
        assert "name" in variables
        assert "age" in variables
        assert len(variables) == 2

    def test_extract_percent_variables(self):
        """Test extracting %{{variable}} format."""
        text = "?[%{{level}} Beginner|Expert]"
        variables = extract_variables_from_text(text)
        assert "level" in variables
        assert len(variables) == 1

    def test_extract_mixed_variables(self):
        """Test extracting both formats."""
        text = "Hello {{name}}! Choose: ?[%{{level}} A|B]"
        variables = extract_variables_from_text(text)
        assert "name" in variables
        assert "level" in variables
        assert len(variables) == 2

    def test_extract_no_variables(self):
        """Test text with no variables."""
        text = "Plain text without variables"
        variables = extract_variables_from_text(text)
        assert len(variables) == 0

    def test_extract_duplicate_variables(self):
        """Test that duplicates are deduplicated."""
        text = "{{name}} and {{name}} and %{{name}}"
        variables = extract_variables_from_text(text)
        assert variables == ["name"]


class TestReplaceVariables:
    """Test variable replacement functionality."""

    def test_replace_simple_variable(self):
        """Test simple variable replacement."""
        text = "Hello {{name}}!"
        variables = {"name": "John"}
        result = replace_variables_in_text(text, variables)
        assert result == 'Hello """John"""!'

    def test_replace_multiple_variables(self):
        """Test multiple variable replacement."""
        text = "Hello {{name}}, you are {{age}} years old"
        variables = {"name": "John", "age": 25}
        result = replace_variables_in_text(text, variables)
        assert result == 'Hello """John""", you are """25""" years old'

    def test_preserve_percent_variables(self):
        """Test that %{{variable}} format is preserved."""
        text = "Hello {{name}}! Choose: ?[%{{level}} A|B]"
        variables = {"name": "John", "level": "Beginner"}
        result = replace_variables_in_text(text, variables)
        assert '"""John"""' in result
        assert "%{{level}}" in result  # Should be preserved

    def test_replace_list_values(self):
        """Test replacing variables with list values."""
        text = "Skills: {{skills}}"
        variables = {"skills": ["Python", "JavaScript", "Go"]}
        result = replace_variables_in_text(text, variables)
        assert result == 'Skills: """Python, JavaScript, Go"""'

    def test_replace_undefined_variable(self):
        """Test that undefined variables get 'UNKNOWN'."""
        text = "Hello {{name}}!"
        variables = {}
        result = replace_variables_in_text(text, variables)
        assert result == 'Hello """UNKNOWN"""!'

    def test_replace_empty_value(self):
        """Test that empty values get 'UNKNOWN'."""
        text = "Hello {{name}}!"
        variables = {"name": ""}
        result = replace_variables_in_text(text, variables)
        assert result == 'Hello """UNKNOWN"""!'

    def test_replace_none_value(self):
        """Test that None values get 'UNKNOWN'."""
        text = "Hello {{name}}!"
        variables = {"name": None}
        result = replace_variables_in_text(text, variables)
        assert result == 'Hello """UNKNOWN"""!'

    def test_replace_empty_list(self):
        """Test that empty list gets 'UNKNOWN'."""
        text = "Skills: {{skills}}"
        variables = {"skills": []}
        result = replace_variables_in_text(text, variables)
        assert result == 'Skills: """UNKNOWN"""'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
