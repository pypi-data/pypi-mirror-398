"""
Unit tests for parser.interaction module
"""

import pytest

from markdown_flow.parser import InteractionParser, InteractionType, extract_interaction_question


class TestInteractionParser:
    """Test InteractionParser functionality."""

    def test_text_only_interaction(self):
        """Test ?[%{{var}}...question] format."""
        parser = InteractionParser()
        result = parser.parse("?[%{{nickname}} ...What is your nickname?]")

        assert result["type"] == InteractionType.TEXT_ONLY
        assert result["variable"] == "nickname"
        assert result["question"] == "What is your nickname?"
        assert result.get("is_multi_select") == False

    def test_buttons_only_interaction(self):
        """Test ?[%{{var}} A|B] format."""
        parser = InteractionParser()
        result = parser.parse("?[%{{level}} Beginner|Intermediate|Expert]")

        assert result["type"] == InteractionType.BUTTONS_ONLY
        assert result["variable"] == "level"
        assert len(result["buttons"]) == 3
        assert result["buttons"][0]["display"] == "Beginner"
        assert result.get("is_multi_select") == False

    def test_buttons_with_text_interaction(self):
        """Test ?[%{{var}} A|B|...question] format."""
        parser = InteractionParser()
        result = parser.parse("?[%{{choice}} Yes|No|...Please specify your choice]")

        assert result["type"] == InteractionType.BUTTONS_WITH_TEXT
        assert result["variable"] == "choice"
        assert len(result["buttons"]) == 2
        assert result["question"] == "Please specify your choice"
        assert result.get("is_multi_select") == False

    def test_buttons_multi_select_interaction(self):
        """Test ?[%{{var}} A||B||C] format."""
        parser = InteractionParser()
        result = parser.parse("?[%{{skills}} Python||JavaScript||Go]")

        assert result["type"] == InteractionType.BUTTONS_MULTI_SELECT
        assert result["variable"] == "skills"
        assert len(result["buttons"]) == 3
        assert result.get("is_multi_select") == True

    def test_buttons_multi_with_text_interaction(self):
        """Test ?[%{{var}} A||B||...question] format."""
        parser = InteractionParser()
        result = parser.parse("?[%{{frameworks}} React||Vue||...Other frameworks]")

        assert result["type"] == InteractionType.BUTTONS_MULTI_WITH_TEXT
        assert result["variable"] == "frameworks"
        assert len(result["buttons"]) == 2
        assert result["question"] == "Other frameworks"
        assert result.get("is_multi_select") == True

    def test_non_assignment_button(self):
        """Test ?[Continue|Cancel] format."""
        parser = InteractionParser()
        result = parser.parse("?[Continue|Cancel]")

        assert result["type"] == InteractionType.NON_ASSIGNMENT_BUTTON
        assert len(result["buttons"]) == 2
        assert result["buttons"][0]["display"] == "Continue"

    def test_button_value_separation(self):
        """Test Button//value format."""
        parser = InteractionParser()
        result = parser.parse("?[%{{choice}} Yes//1|No//0]")

        assert result["type"] == InteractionType.BUTTONS_ONLY
        assert result["buttons"][0]["display"] == "Yes"
        assert result["buttons"][0]["value"] == "1"
        assert result["buttons"][1]["display"] == "No"
        assert result["buttons"][1]["value"] == "0"

    def test_invalid_format(self):
        """Test invalid interaction format."""
        parser = InteractionParser()
        result = parser.parse("invalid format")

        assert "error" in result
        assert result["type"] is None


class TestExtractInteractionQuestion:
    """Test extract_interaction_question functionality."""

    def test_extract_question_with_ellipsis(self):
        """Test extracting question from ?[...question] format."""
        content = "?[%{{name}} ...What is your name?]"
        question = extract_interaction_question(content)
        assert question == "What is your name?"

    def test_extract_question_with_buttons(self):
        """Test extracting question from buttons+text format."""
        content = "?[%{{choice}} A|B|...Please choose]"
        question = extract_interaction_question(content)
        assert question == "Please choose"

    def test_no_question(self):
        """Test content without question."""
        content = "?[%{{level}} Beginner|Expert]"
        question = extract_interaction_question(content)
        assert question is None

    def test_invalid_format(self):
        """Test invalid format."""
        content = "Plain text without interaction"
        question = extract_interaction_question(content)
        assert question is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
