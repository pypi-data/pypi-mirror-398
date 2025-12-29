"""
Test cases for output.py parser module

Tests priority rules and whitespace preservation for === and !=== formats.
"""

import os
import sys

# Add project path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    print("Warning: pytest not found, running tests without pytest framework")

from markdown_flow.constants import OUTPUT_INSTRUCTION_PREFIX, OUTPUT_INSTRUCTION_SUFFIX  # noqa: E402
from markdown_flow.parser.output import process_output_instructions  # noqa: E402


class TestProcessOutputInstructionsInlineExclamationFormat:
    """Test inline exclamation format: !===content!==="""

    def test_scenario_a_compact_format(self):
        """Scenario A: Compact format - !===固定内容!==="""
        input_text = "!===固定内容!==="
        expected_contains = f"{OUTPUT_INSTRUCTION_PREFIX}固定内容{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected_contains in result

    def test_scenario_b_format_with_spaces(self):
        """Scenario B: Format with spaces - !=== 固定内容 !==="""
        input_text = "!=== 固定内容 !==="
        expected_contains = f"{OUTPUT_INSTRUCTION_PREFIX} 固定内容 {OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected_contains in result

    def test_scenario_c_inline_mixed_content(self):
        """Scenario C: Inline mixed content - 前面文字 !===固定内容!=== 后面文字"""
        input_text = "前面文字 !===固定内容!=== 后面文字"
        expected_contains = f"{OUTPUT_INSTRUCTION_PREFIX}固定内容{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected_contains in result
        assert "前面文字" in result
        assert "后面文字" in result

    def test_scenario_d_multiline_fence_format(self):
        """Scenario D: Multiline fence format"""
        input_text = """!===
固定内容
!==="""
        expected_contains = f"{OUTPUT_INSTRUCTION_PREFIX}固定内容{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected_contains in result

    def test_multiple_inline_exclamation_preserves_on_same_line(self):
        """Multiple inline exclamation preserves on same line"""
        input_text = "开头 !===第一段!=== 中间 !===第二段!=== 结尾"
        expected_first = f"{OUTPUT_INSTRUCTION_PREFIX}第一段{OUTPUT_INSTRUCTION_SUFFIX}"
        expected_second = f"{OUTPUT_INSTRUCTION_PREFIX}第二段{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected_first in result
        assert expected_second in result
        assert "开头" in result
        assert "中间" in result
        assert "结尾" in result

    def test_nested_equals_inside_exclamation(self):
        """Nested === inside !===...!=== - content with === symbols should be preserved as-is"""
        input_text = "!===内容===包含===符号!==="
        expected_contains = f"{OUTPUT_INSTRUCTION_PREFIX}内容===包含===符号{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        # The entire content including === symbols should be preserved
        assert expected_contains in result
        # Should not create nested tags
        assert result.count(OUTPUT_INSTRUCTION_PREFIX) == 1
        assert result.count(OUTPUT_INSTRUCTION_SUFFIX) == 1


class TestProcessOutputInstructionsPriorityRules:
    """Test priority rules between different formats"""

    # Note: Removed test_priority_exclamation_over_equals because mixing !===...!=== and ===...=== on the same line
    # is not a supported pattern. Each line should use only one format to avoid ambiguity.

    def test_multiline_exclamation_should_not_process_internal_equals(self):
        """Priority: multiline !===...!=== should not process internal ==="""
        input_text = """!===
外层固定
===内层不处理===
!==="""
        result_outer = f"{OUTPUT_INSTRUCTION_PREFIX}外层固定\n===内层不处理==={OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert result_outer in result

    def test_mixed_inline_exclamation_and_multiline_fence(self):
        """Mixed: inline exclamation + multiline fence"""
        input_text = """!===单行内容!===

!===
多行
内容
!==="""
        result_inline = f"{OUTPUT_INSTRUCTION_PREFIX}单行内容{OUTPUT_INSTRUCTION_SUFFIX}"
        result_multiline = f"{OUTPUT_INSTRUCTION_PREFIX}多行\n内容{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert result_inline in result
        assert result_multiline in result


class TestProcessOutputInstructionsPreserveSpaces:
    """Test whitespace preservation"""

    def test_leading_and_trailing_spaces_in_exclamation(self):
        """Leading and trailing spaces in !===...!==="""
        input_text = "!===  前后空格  !==="
        # Should preserve all spaces
        expected = f"{OUTPUT_INSTRUCTION_PREFIX}  前后空格  {OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected in result

    def test_tab_and_newline_characters(self):
        """Tab and newline characters"""
        input_text = "!===\t制表符\t!==="
        expected = f"{OUTPUT_INSTRUCTION_PREFIX}\t制表符\t{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected in result


class TestProcessOutputInstructionsHistoricalFormat:
    """Test historical ===...=== format (Priority 3)"""

    def test_inline_format(self):
        """Inline format: ===content==="""
        input_text = "===固定内容==="
        expected = f"{OUTPUT_INSTRUCTION_PREFIX}固定内容{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected in result

    def test_inline_with_spaces(self):
        """Inline with spaces: === content ==="""
        input_text = "=== 固定内容 ==="
        expected = f"{OUTPUT_INSTRUCTION_PREFIX}固定内容{OUTPUT_INSTRUCTION_SUFFIX}"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is True
        assert expected in result


class TestProcessOutputInstructionsNoPreservedContent:
    """Test content without preserved markers"""

    def test_no_preserved_content(self):
        """No preserved content"""
        input_text = "这是普通文本，没有保留标记"

        result, has_preserve = process_output_instructions(input_text)

        assert has_preserve is False
        assert result == input_text


def run_all_tests():
    """Run all test classes"""
    test_classes = [
        TestProcessOutputInstructionsInlineExclamationFormat,
        TestProcessOutputInstructionsPriorityRules,
        TestProcessOutputInstructionsPreserveSpaces,
        TestProcessOutputInstructionsHistoricalFormat,
        TestProcessOutputInstructionsNoPreservedContent,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n{'=' * 60}")
        print(f"Running {test_class.__name__}")
        print('=' * 60)

        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]

        for method_name in test_methods:
            total_tests += 1
            test_instance = test_class()
            method = getattr(test_instance, method_name)

            try:
                method()
                passed_tests += 1
                print(f"✅ {method_name}")
            except AssertionError as e:
                failed_tests.append((test_class.__name__, method_name, str(e)))
                print(f"❌ {method_name}: {e}")
            except Exception as e:
                failed_tests.append((test_class.__name__, method_name, str(e)))
                print(f"💥 {method_name}: {e}")

    # Summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print('=' * 60)
    print(f"Total: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for class_name, method_name, error in failed_tests:
            print(f"  - {class_name}.{method_name}: {error}")

    return len(failed_tests) == 0


if __name__ == "__main__":
    if HAS_PYTEST:
        pytest.main([__file__, "-v"])
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
