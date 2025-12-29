"""
Tests for HTML Comment Utilities

测试 HTML 注释工具函数
"""

import pytest

from markdown_flow.parser.html_comment_utils import (
    is_html_comment_end,
    is_html_comment_start,
    remove_inline_comment,
)


class TestIsHTMLCommentStart:
    """测试 HTML 注释开始检测"""

    def test_single_line_comment_standard(self):
        """测试标准单行注释"""
        info, is_single = is_html_comment_start("<!-- 这是单行注释 -->")
        assert info is not None
        assert is_single is True

    def test_single_line_comment_with_prefix(self):
        """测试单行注释带前缀内容"""
        info, is_single = is_html_comment_start("前缀文本 <!-- 注释 --> 后缀文本")
        assert info is not None
        assert is_single is True

    def test_empty_comment(self):
        """测试空注释"""
        info, is_single = is_html_comment_start("<!---->")
        assert info is not None
        assert is_single is True

    def test_comment_with_spaces(self):
        """测试注释带空格"""
        info, is_single = is_html_comment_start("<!--  内容  -->")
        assert info is not None
        assert is_single is True

    def test_multi_line_comment_start_standard(self):
        """测试标准多行注释开始"""
        info, is_single = is_html_comment_start("<!--")
        assert info is not None
        assert is_single is False

    def test_multi_line_comment_start_with_content(self):
        """测试多行注释开始带内容"""
        info, is_single = is_html_comment_start("<!-- 这是多行注释开始")
        assert info is not None
        assert is_single is False

    def test_multi_line_comment_start_with_prefix(self):
        """测试多行注释开始带前缀"""
        info, is_single = is_html_comment_start("前缀 <!-- 注释开始")
        assert info is not None
        assert is_single is False

    def test_no_comment_normal_text(self):
        """测试普通文本"""
        info, is_single = is_html_comment_start("这是普通文本")
        assert info is None
        assert is_single is False

    def test_no_comment_arrow(self):
        """测试包含箭头但不是注释"""
        info, is_single = is_html_comment_start("a < b && c --> d")
        assert info is None
        assert is_single is False

    def test_no_comment_empty_line(self):
        """测试空行"""
        info, is_single = is_html_comment_start("")
        assert info is None
        assert is_single is False

    def test_no_comment_whitespace(self):
        """测试仅空格"""
        info, is_single = is_html_comment_start("   ")
        assert info is None
        assert is_single is False


class TestIsHTMLCommentEnd:
    """测试 HTML 注释结束检测"""

    def test_standard_end_marker(self):
        """测试标准结束标记"""
        assert is_html_comment_end("-->") is True

    def test_end_marker_with_prefix(self):
        """测试结束标记带前缀内容"""
        assert is_html_comment_end("注释内容 -->") is True

    def test_end_marker_with_suffix(self):
        """测试结束标记带后缀内容"""
        assert is_html_comment_end("--> 后续内容") is True

    def test_end_marker_with_spaces(self):
        """测试结束标记带空格"""
        assert is_html_comment_end("  -->  ") is True

    def test_no_end_marker(self):
        """测试不包含结束标记"""
        assert is_html_comment_end("普通文本") is False

    def test_arrow_not_end_marker(self):
        """测试包含箭头但不是结束标记"""
        assert is_html_comment_end("a -> b") is False

    def test_empty_line(self):
        """测试空行"""
        assert is_html_comment_end("") is False


class TestRemoveInlineComment:
    """测试移除行内注释"""

    def test_only_comment(self):
        """测试仅注释"""
        result = remove_inline_comment("<!-- 这是注释 -->")
        assert result == ""

    def test_prefix_and_comment(self):
        """测试前缀+注释"""
        result = remove_inline_comment("===标题=== <!-- 注释 -->")
        assert result == "===标题=== "

    def test_prefix_comment_suffix(self):
        """测试前缀+注释+后缀"""
        result = remove_inline_comment("前缀 <!-- 注释 --> 后缀")
        assert result == "前缀  后缀"

    def test_no_comment(self):
        """测试无注释"""
        result = remove_inline_comment("普通文本")
        assert result == "普通文本"

    def test_empty_comment(self):
        """测试空注释"""
        result = remove_inline_comment("文本<!---->更多")
        assert result == "文本更多"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
