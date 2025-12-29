"""
Unit tests for MarkdownFlow basic functionality
"""

import pytest

from markdown_flow import MarkdownFlow, ProcessMode
from markdown_flow.enums import BlockType


class TestMarkdownFlowConstruction:
    """Test MarkdownFlow construction and basic properties."""

    def test_new_markdownflow(self):
        """Test creating new MarkdownFlow instance."""
        document = "Test document"
        mf = MarkdownFlow(document, llm_provider=None)

        assert mf is not None
        assert mf.document == document

    def test_get_all_blocks(self):
        """Test getting all blocks."""
        document = "Block 1\n---\nBlock 2\n---\nBlock 3"
        mf = MarkdownFlow(document, llm_provider=None)

        blocks = mf.get_all_blocks()
        assert len(blocks) == 3
        assert blocks[0].content.strip() == "Block 1"
        assert blocks[1].content.strip() == "Block 2"
        assert blocks[2].content.strip() == "Block 3"

    def test_get_block(self):
        """Test getting single block by index."""
        document = "Block 1\n---\nBlock 2"
        mf = MarkdownFlow(document, llm_provider=None)

        block = mf.get_block(0)
        assert block.content.strip() == "Block 1"
        assert block.index == 0

        block = mf.get_block(1)
        assert block.content.strip() == "Block 2"
        assert block.index == 1

    def test_get_block_out_of_range(self):
        """Test getting block with invalid index."""
        document = "Block 1"
        mf = MarkdownFlow(document, llm_provider=None)

        with pytest.raises(Exception):
            mf.get_block(10)

    def test_block_count(self):
        """Test block count."""
        document = "A\n---\nB\n---\nC\n---\nD"
        mf = MarkdownFlow(document, llm_provider=None)

        assert mf.block_count == 4


class TestVariableExtraction:
    """Test variable extraction functionality."""

    def test_extract_variables(self):
        """Test extracting variables from document."""
        document = "Hello {{name}}, you are {{age}} years old"
        mf = MarkdownFlow(document, llm_provider=None)

        variables = mf.extract_variables()
        assert "name" in variables
        assert "age" in variables

    def test_extract_variables_multiple_blocks(self):
        """Test extracting variables from multiple blocks."""
        document = "Hello {{name}}\n---\nYou are {{age}} years old\n---\nLevel: ?[%{{level}} A|B]"
        mf = MarkdownFlow(document, llm_provider=None)

        variables = mf.extract_variables()
        assert "name" in variables
        assert "age" in variables
        assert "level" in variables


class TestBlockTypeDetection:
    """Test block type detection."""

    def test_content_block(self):
        """Test content block detection."""
        document = "This is regular content"
        mf = MarkdownFlow(document, llm_provider=None)

        blocks = mf.get_all_blocks()
        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.CONTENT

    def test_interaction_block(self):
        """Test interaction block detection."""
        document = "?[%{{name}} ...What is your name?]"
        mf = MarkdownFlow(document, llm_provider=None)

        blocks = mf.get_all_blocks()
        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.INTERACTION

    def test_preserved_content_block(self):
        """Test preserved content block detection."""
        document = "===Preserved content==="
        mf = MarkdownFlow(document, llm_provider=None)

        blocks = mf.get_all_blocks()
        assert len(blocks) == 1
        assert blocks[0].block_type == BlockType.PRESERVED_CONTENT

    def test_mixed_block_types(self):
        """Test document with mixed block types."""
        document = "Content\n---\n?[%{{var}} A|B]\n---\n===Preserved==="
        mf = MarkdownFlow(document, llm_provider=None)

        blocks = mf.get_all_blocks()
        assert len(blocks) == 3
        assert blocks[0].block_type == BlockType.CONTENT
        assert blocks[1].block_type == BlockType.INTERACTION
        assert blocks[2].block_type == BlockType.PRESERVED_CONTENT


class TestInstanceLevelConfig:
    """Test instance-level model configuration."""

    def test_set_model(self):
        """Test setting model name."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Test chainable API
        result = mf.set_model("gpt-4")
        assert result is mf  # Should return self
        assert mf.get_model() == "gpt-4"

    def test_set_temperature(self):
        """Test setting temperature."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Test chainable API
        result = mf.set_temperature(0.9)
        assert result is mf  # Should return self
        assert mf.get_temperature() == 0.9

    def test_chainable_api(self):
        """Test chaining set_model and set_temperature."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        mf.set_model("claude-3").set_temperature(0.5)
        assert mf.get_model() == "claude-3"
        assert mf.get_temperature() == 0.5

    def test_get_model_default(self):
        """Test getting model when not set."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        assert mf.get_model() is None

    def test_get_temperature_default(self):
        """Test getting temperature when not set."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        assert mf.get_temperature() is None


class TestPromptConfiguration:
    """Test prompt configuration."""

    def test_set_base_system_prompt(self):
        """Test setting base_system prompt."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        custom_prompt = "You are a helpful assistant"
        mf.set_prompt("base_system", custom_prompt)
        # No direct getter, but should not raise error

    def test_set_document_prompt(self):
        """Test setting document prompt."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        custom_prompt = "Custom document instructions"
        mf.set_prompt("document", custom_prompt)
        # No direct getter, but should not raise error

    def test_set_invalid_prompt_type(self):
        """Test setting invalid prompt type."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        with pytest.raises(ValueError):
            mf.set_prompt("invalid_type", "some value")

    def test_reset_base_system_prompt(self):
        """Test resetting base_system prompt to default."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Set custom prompt
        mf.set_prompt("base_system", "Custom")

        # Reset to default
        mf.set_prompt("base_system", None)
        # Should not raise error


class TestContextTruncation:
    """Test context truncation functionality."""

    def test_truncate_context_default(self):
        """Test context truncation with default max length."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Create context with 150 messages (default max is 100)
        context = [{"role": "user", "content": f"Message {i}"} for i in range(150)]

        # Truncation is internal, but we can test that it doesn't raise error
        # The actual truncation happens in _truncate_context which is private


class TestTextValidationToggle:
    """Test text validation toggle functionality."""

    def test_set_text_validation_enabled(self):
        """Test setting text validation enabled."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Test setting to True
        result = mf.set_text_validation_enabled(True)
        assert result is mf  # Should return self for chaining
        assert mf.is_text_validation_enabled() is True

        # Test setting to False
        mf.set_text_validation_enabled(False)
        assert mf.is_text_validation_enabled() is False

    def test_is_text_validation_enabled_default(self):
        """Test default value of text validation (should be False)."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Default should be False (disabled)
        assert mf.is_text_validation_enabled() is False

    def test_text_validation_enabled_after_enabling(self):
        """Test querying text validation status after enabling."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Enable validation
        mf.set_text_validation_enabled(True)
        assert mf.is_text_validation_enabled() is True

        # Disable again
        mf.set_text_validation_enabled(False)
        assert mf.is_text_validation_enabled() is False

    def test_text_validation_chainable(self):
        """Test chainable API for text validation."""
        document = "Test"
        mf = MarkdownFlow(document, llm_provider=None)

        # Test chaining with other methods
        result = mf.set_text_validation_enabled(True).set_model("gpt-4")
        assert result is mf

        # Verify both settings took effect
        assert mf.is_text_validation_enabled() is True
        assert mf.get_model() == "gpt-4"

        # Test reverse chaining
        mf2 = MarkdownFlow("Test2", llm_provider=None)
        mf2.set_model("deepseek-chat").set_text_validation_enabled(False).set_temperature(0.5)

        assert mf2.is_text_validation_enabled() is False
        assert mf2.get_model() == "deepseek-chat"
        assert mf2.get_temperature() == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
