"""
Tests for Code Block Preprocessor

测试代码块预处理器功能，确保代码块内的 MarkdownFlow 语法不被解析。
"""

import pytest

from markdown_flow.parser import CodeBlockPreprocessor


class TestCodeBlockPreprocessor:
    """测试代码块预处理器基本功能"""

    def test_extract_single_code_block(self):
        """测试提取单个代码块"""
        preprocessor = CodeBlockPreprocessor()
        document = """普通内容

```python
print('hello')
```

其他内容"""

        processed = preprocessor.extract_code_blocks(document)

        # 验证代码块被替换为占位符
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "```python" not in processed
        assert "print('hello')" not in processed
        assert "普通内容" in processed
        assert "其他内容" in processed

        # 验证可以还原
        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document

    def test_extract_multiple_code_blocks(self):
        """测试提取多个代码块"""
        preprocessor = CodeBlockPreprocessor()
        document = """# 标题

```javascript
console.log('test');
```

中间内容

```python
print('hello')
```

结尾"""

        processed = preprocessor.extract_code_blocks(document)

        # 验证两个代码块都被替换
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "__MDFLOW_CODE_BLOCK_2__" in processed
        assert "```javascript" not in processed
        assert "```python" not in processed

        # 验证可以还原
        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document

    def test_code_block_with_tildes(self):
        """测试波浪线围栏代码块"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容

~~~markdown
示例代码
~~~

结尾"""

        processed = preprocessor.extract_code_blocks(document)
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "~~~markdown" not in processed

        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document

    def test_nested_fence_markers_in_code(self):
        """测试代码块内包含嵌套的围栏标记"""
        preprocessor = CodeBlockPreprocessor()
        document = """说明文档

```markdown
这是一个示例：
```python
print('nested')
```
```

结束"""

        processed = preprocessor.extract_code_blocks(document)

        # 外层代码块应该被提取
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "```markdown" not in processed

        # 还原后应该完整
        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document

    def test_unclosed_code_block(self):
        """测试未闭合的代码块（保持原样）"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容

```python
print('hello')

未闭合"""

        processed = preprocessor.extract_code_blocks(document)

        # 未闭合的代码块应该保持原样
        assert "```python" in processed
        assert "print('hello')" in processed
        assert "__MDFLOW_CODE_BLOCK" not in processed

    def test_code_block_with_indent(self):
        """测试带缩进的代码块（≤3 空格）"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容

   ```python
   print('indented')
   ```

结束"""

        processed = preprocessor.extract_code_blocks(document)
        assert "__MDFLOW_CODE_BLOCK_1__" in processed

        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document

    def test_ignore_over_indented_fence(self):
        """测试超过 3 个空格缩进的围栏（不算代码块）"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容

    ```python
    print('too indented')
    ```

结束"""

        processed = preprocessor.extract_code_blocks(document)

        # 超过 3 空格缩进的不算代码块，保持原样
        assert "```python" in processed
        assert "__MDFLOW_CODE_BLOCK" not in processed

    def test_reset_preprocessor(self):
        """测试重置预处理器"""
        preprocessor = CodeBlockPreprocessor()

        # 第一次处理
        doc1 = "```\ntest1\n```"
        preprocessor.extract_code_blocks(doc1)
        assert preprocessor.counter == 1
        assert len(preprocessor.code_blocks) == 1

        # 重置
        preprocessor.reset()
        assert preprocessor.counter == 0
        assert len(preprocessor.code_blocks) == 0

        # 第二次处理
        doc2 = "```\ntest2\n```"
        processed = preprocessor.extract_code_blocks(doc2)
        assert "__MDFLOW_CODE_BLOCK_1__" in processed  # 从 1 开始


class TestCodeBlockWithMarkdownFlowSyntax:
    """测试代码块内包含 MarkdownFlow 语法的情况"""

    def test_ignore_interaction_in_code_block(self):
        """测试忽略代码块内的交互语法"""
        preprocessor = CodeBlockPreprocessor()
        document = """说明

```markdown
?[%{{choice}} A|B|C]
```

正常内容"""

        processed = preprocessor.extract_code_blocks(document)

        # 交互语法在代码块内，应该被提取
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "?[%{{choice}}" not in processed

        # 还原后应该包含交互语法
        restored = preprocessor.restore_code_blocks(processed)
        assert "?[%{{choice}} A|B|C]" in restored

    def test_ignore_preserved_content_in_code_block(self):
        """测试忽略代码块内的保留内容语法"""
        preprocessor = CodeBlockPreprocessor()
        document = """!===
```markdown
!===
内部内容
!===
```
!==="""

        processed = preprocessor.extract_code_blocks(document)

        # 代码块被提取
        assert "__MDFLOW_CODE_BLOCK_1__" in processed

        # 外层的 !===  仍然存在
        lines = processed.split("\n")
        assert lines[0] == "!==="
        assert lines[2] == "!==="

        # 还原应该正确
        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document

    def test_ignore_separator_in_code_block(self):
        """测试忽略代码块内的分隔符"""
        preprocessor = CodeBlockPreprocessor()
        document = """第一部分

```markdown
---
这是代码块内的分隔符
---
```

第二部分"""

        processed = preprocessor.extract_code_blocks(document)

        # 代码块被提取
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "这是代码块内的分隔符" not in processed

        # 还原后正确
        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document


class TestCodeBlockInPreservedContent:
    """测试保留内容块中包含代码块的情况"""

    def test_code_block_inside_preserved_content(self):
        """测试保留内容块中的代码块被正确提取"""
        preprocessor = CodeBlockPreprocessor()
        document = """!===
这里讲解 markdownflow 的语法支持

```markdown
!===
如果是多行固定输出可以这样来表示
!===
```

说明完毕
!==="""

        processed = preprocessor.extract_code_blocks(document)

        # 代码块应该被提取
        assert "__MDFLOW_CODE_BLOCK_1__" in processed

        # 外层保留内容标记应该保留
        assert processed.startswith("!===")
        assert processed.endswith("!===")

        # 还原后完整
        restored = preprocessor.restore_code_blocks(processed)
        assert restored == document


class TestHTMLCommentExtraction:
    """测试 HTML 注释提取功能"""

    def test_extract_single_line_comment_full_line(self):
        """测试提取完整行的单行注释"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容1
<!-- 这是单行注释 -->
内容2"""

        processed = preprocessor.extract_code_blocks(document)

        # 单行注释应该被移除（整行）
        assert "<!-- 这是单行注释 -->" not in processed
        assert "内容1" in processed
        assert "内容2" in processed
        assert "__MDFLOW_HTML_COMMENT" not in processed  # 单行注释不存储

    def test_extract_inline_comment(self):
        """测试提取行内注释（保留其他内容）"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容1
===标题=== <!-- 在此处写注释 -->
内容2"""

        processed = preprocessor.extract_code_blocks(document)

        # 注释部分被移除，标题保留
        assert "<!-- 在此处写注释 -->" not in processed
        assert "===标题===" in processed
        assert "内容1" in processed
        assert "内容2" in processed

    def test_extract_multiline_comment(self):
        """测试提取多行注释"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容1
<!--
这是多行注释
包含多行内容
-->
内容2"""

        processed = preprocessor.extract_code_blocks(document)

        # 多行注释应该被占位符替换
        assert "__MDFLOW_HTML_COMMENT_1__" in processed
        assert "这是多行注释" not in processed
        assert "包含多行内容" not in processed
        assert "内容1" in processed
        assert "内容2" in processed

        # 验证注释被存储
        assert len(preprocessor.get_html_comments()) == 1

    def test_html_comment_with_code_blocks(self):
        """测试注释与代码块混合"""
        preprocessor = CodeBlockPreprocessor()
        document = """# 教程
<!-- 单行注释 -->
```go
// 代码中的注释
fmt.Println("hello")
```
<!--
多行注释
包含: ?[test]
-->
正常内容"""

        processed = preprocessor.extract_code_blocks(document)

        # 单行注释被移除（不在 processed 中）
        assert "<!-- 单行注释 -->" not in processed

        # 代码块被占位符替换
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "```go" not in processed

        # 多行注释被占位符替换
        assert "__MDFLOW_HTML_COMMENT_2__" in processed
        assert "多行注释" not in processed

        # 正常内容保留
        assert "# 教程" in processed
        assert "正常内容" in processed

    def test_code_block_priority_over_comment(self):
        """测试代码块优先于注释"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容
```markdown
<!-- 代码块内的注释 -->
?[test]
```
结束"""

        processed = preprocessor.extract_code_blocks(document)

        # 整个代码块被提取（包括内部的注释）
        assert "__MDFLOW_CODE_BLOCK_1__" in processed
        assert "<!-- 代码块内的注释 -->" not in processed

        # 注释不应该被单独提取
        assert "__MDFLOW_HTML_COMMENT" not in processed
        assert len(preprocessor.get_html_comments()) == 0

        # 还原后代码块内容完整
        restored = preprocessor.restore_code_blocks(processed)
        assert "<!-- 代码块内的注释 -->" in restored

    def test_unclosed_comment(self):
        """测试未闭合的注释（保持原样）"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容
<!--
未闭合的注释
仍在继续"""

        processed = preprocessor.extract_code_blocks(document)

        # 未闭合的注释应该保持原样
        assert "<!--" in processed
        assert "未闭合的注释" in processed
        assert "__MDFLOW_HTML_COMMENT" not in processed

    def test_restore_code_blocks_with_comments(self):
        """测试完整还原（代码块+注释）"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容
<!--
注释内容
-->
```python
code
```
结束"""

        processed = preprocessor.extract_code_blocks(document)
        restored = preprocessor.restore_code_blocks(processed)

        # 完整还原应该与原文档相同
        assert restored == document

    def test_restore_code_blocks_only(self):
        """测试仅还原代码块"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容
<!--
注释内容
-->
```python
code
```
结束"""

        processed = preprocessor.extract_code_blocks(document)
        restored = preprocessor.restore_code_blocks_only(processed)

        # 代码块应该被还原
        assert "```python" in restored
        assert "code" in restored

        # 注释占位符应该保留
        assert "__MDFLOW_HTML_COMMENT_1__" in restored
        assert "注释内容" not in restored

    def test_remove_html_comment_placeholders(self):
        """测试移除 HTML 注释占位符"""
        preprocessor = CodeBlockPreprocessor()
        document = """内容1
<!--
注释
-->
内容2"""

        processed = preprocessor.extract_code_blocks(document)
        cleaned = preprocessor.remove_html_comment_placeholders(processed)

        # 注释占位符应该被移除
        assert "__MDFLOW_HTML_COMMENT" not in cleaned
        assert "内容1" in cleaned
        assert "内容2" in cleaned

    def test_reset_with_html_comments(self):
        """测试重置预处理器（包含注释）"""
        preprocessor = CodeBlockPreprocessor()

        # 处理包含注释和代码块的文档
        doc = """<!--comment-->
```
code
```"""
        preprocessor.extract_code_blocks(doc)

        assert preprocessor.counter == 2
        assert len(preprocessor.get_html_comments()) == 1
        assert len(preprocessor.get_code_blocks()) == 1

        # 重置
        preprocessor.reset()
        assert preprocessor.counter == 0
        assert len(preprocessor.get_html_comments()) == 0
        assert len(preprocessor.get_code_blocks()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
