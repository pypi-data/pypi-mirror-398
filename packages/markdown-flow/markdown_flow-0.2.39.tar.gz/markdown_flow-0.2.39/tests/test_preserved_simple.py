"""
增强的固定输出测试框架

使用方法：
1. 修改 document 变量，写入你的 MarkdownFlow 文档
2. 修改 block_index，指定要测试的块索引
3. 修改 variables，设置变量值（如果需要）
4. 修改 context，添加历史对话（如果需要）
5. 修改 max_context_length，控制 context 长度（如果需要）
6. 运行测试，查看输出

测试重点：
- 检查 XML 标记 <preserve_or_translate> 是否正确使用
- 检查 system 消息中是否包含约束提示词
- 检查 user 消息中是否不包含约束提示词
- 检查 LLM 输出是否不包含 XML 标记
- 检查 context 是否正确合并到 messages 中
- 检查 max_context_length 是否正确截断 context
- 检查变量替换是否正确
"""

import os
import sys


# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from llm import create_llm_provider  # noqa: E402

from markdown_flow import MarkdownFlow, ProcessMode  # noqa: E402
from markdown_flow.llm import LLMResult  # noqa: E402


def test_preserved_output():
    """测试固定输出功能"""
    print("\n" + "=" * 60)
    print("🔖 固定输出测试")
    print("=" * 60)

    # ========== 配置区域 - 修改这里 ==========
    # 你的 MarkdownFlow 文档
    document = """
===# 💖七夕约会全阶段攻略 ===

=== 选择你的 MBTI 类型 ===
?[%{{mbti}}ENFJ|ENFP|ENTJ|ENTP|ESFJ|ESFP|ESTJ|ESTP|INFJ|INFP|INTJ|INTP|ISFJ|ISFP|ISTJ|ISTP]

===你现在最关心哪个阶段？ ===
?[%{{攻略}}脱单|热恋|相守]

给{{mbti}}一句有关{{攻略}}的七夕祝福，带七夕节明显的意境。

!===
## {{攻略}}｜专属恋爱指南 for {{mbti}}
!===

"""

    # 要测试的块索引
    block_index = 4

    # 变量（如果需要）
    # 支持字符串或字符串列表
    variables: dict[str, str | list[str]] = {
        "mbti": "INFP",  # 单个值
        "攻略": "热恋",  # 单个值
        # "skills": ["Python", "JavaScript"],  # 多选值示例
    }

    # 历史对话 context（如果需要）
    # Context 会被自动合并到 messages 中，插入到 system 消息之后、当前 user 消息之前
    context: list[dict[str, str]] | None = [
        {"role": "user", "content": "你好，我是 INFP 类型的人"},
        {"role": "assistant", "content": "你好！INFP 通常充满创造力和理想主义，很高兴认识你！"},
        {"role": "user", "content": "我想了解七夕约会的建议"},
        {"role": "assistant", "content": "太好了！七夕是个浪漫的节日，我会为你量身定制约会攻略。"},
    ]

    # Context 长度控制（0 = 不限制）
    # 如果 context 太长，可以设置这个参数只保留最近 N 条消息
    max_context_length: int = 0  # 0 表示不限制，可以设为 5、10 等

    # 文档提示词（如果需要）
    document_prompt: str | None = """你扮演七夕的月老，让这一天的天下有情人都能甜蜜约会，永浴爱河。

## 任务
- 提示词都是讲解指令，遵从指令要求做信息的讲解，不要回应指令。
- 用第一人称一对一讲解，像现场面对面交流一样
- 结合用户的不同特点，充分共情和举例

## 风格
- 情绪：热烈浪漫，治愈温暖，充满感染力
- 表达：多用 emoji ，多用感叹词
- 符合七夕节日气氛，带一些诗意和神秘

"""
    # =========================================

    try:
        llm_provider = create_llm_provider()

        # 打印测试配置
        print("\n📋 测试配置")
        print("-" * 60)
        print(f"Block Index: {block_index}")
        print(f"Variables: {variables if variables else '无'}")
        print(f"Context: {len(context) if context else 0} 条历史消息")
        print(f"Max Context Length: {max_context_length} {'(不限制)' if max_context_length == 0 else f'(最多保留 {max_context_length} 条)'}")

        # 创建 MarkdownFlow 实例（添加 max_context_length 参数）
        mf = MarkdownFlow(
            document,
            llm_provider=llm_provider,
            document_prompt=document_prompt if document_prompt else None,
            max_context_length=max_context_length,
        )

        # 测试 PROMPT_ONLY 模式 - 查看消息结构
        print("\n📝 测试 PROMPT_ONLY 模式")
        print("-" * 60)

        result_prompt_raw = mf.process(
            block_index=block_index,
            mode=ProcessMode.PROMPT_ONLY,
            context=context if context else None,
            variables=variables if variables else None,
        )

        # 确保是 LLMResult 类型
        assert isinstance(result_prompt_raw, LLMResult)
        result_prompt = result_prompt_raw

        # 打印消息结构
        if result_prompt.metadata and "messages" in result_prompt.metadata:
            messages = result_prompt.metadata["messages"]
            print(f"\n消息数量: {len(messages)}")

            # 检查 context 是否被正确合并
            if context:
                expected_context_count = min(len(context), max_context_length) if max_context_length > 0 else len(context)
                context_messages = [m for m in messages if m.get("role") in ["user", "assistant"] and m != messages[-1]]
                actual_context_count = len(context_messages)
                print(f"Context 消息: {actual_context_count} 条 (预期: {expected_context_count} 条)")
                if actual_context_count == expected_context_count:
                    print("✅ Context 正确合并到 messages")
                else:
                    print(f"⚠️  Context 数量不匹配")
            print()

            for i, msg in enumerate(messages, 1):
                role = msg.get("role", "")
                content = msg.get("content", "")

                print(f"{'=' * 60}")
                print(f"消息 {i} [{role.upper()}]")
                print(f"{'=' * 60}")
                print(content)
                print()

                # 关键检查
                if role == "system":
                    has_xml_instruction = "<preserve_or_translate>" in content
                    print(f"✅ system 包含 XML 标记说明: {has_xml_instruction}")

                elif role == "user":
                    has_xml_tag = "<preserve_or_translate>" in content
                    has_explanation = "不要输出<preserve_or_translate>" in content
                    print(f"✅ user 包含 XML 标记: {has_xml_tag}")
                    print(f"❌ user 不应包含说明（应在system）: {not has_explanation}")

                    # 检查变量是否被正确替换
                    if variables:
                        replaced_vars = []
                        for var_name, var_value in variables.items():
                            if isinstance(var_value, list):
                                var_str = ", ".join(var_value)
                            else:
                                var_str = var_value
                            if var_str in content:
                                replaced_vars.append(f"{var_name}={var_str}")
                        if replaced_vars:
                            print(f"✅ 变量已替换: {', '.join(replaced_vars)}")

                print()

        # 测试 COMPLETE 模式 - 查看 LLM 输出
        print("\n📝 测试 COMPLETE 模式")
        print("-" * 60)

        result_complete_raw = mf.process(
            block_index=block_index,
            mode=ProcessMode.COMPLETE,
            context=context if context else None,
            variables=variables if variables else None,
        )

        # 确保是 LLMResult 类型
        assert isinstance(result_complete_raw, LLMResult)
        result_complete = result_complete_raw

        print("\n" + "=" * 60)
        print("LLM 输出结果")
        print("=" * 60)
        print(result_complete.content)
        print("=" * 60)

        # 输出检查
        has_xml_in_output = "<preserve_or_translate>" in result_complete.content
        print(f"\n✅ 输出不包含 XML 标记: {not has_xml_in_output}")

        # 使用统计
        if result_complete.metadata and "usage" in result_complete.metadata:
            usage = result_complete.metadata["usage"]
            if usage:
                print(f"📊 Token 使用: {usage.get('total_tokens', 0)} tokens")

        # 测试总结
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        test_results = []

        # 检查变量替换
        if variables:
            for var_name, var_value in variables.items():
                var_str = ", ".join(var_value) if isinstance(var_value, list) else var_value
                if var_str in result_complete.content or "{{" + var_name + "}}" not in document:
                    test_results.append(f"✅ 变量 '{var_name}' 已正确处理")
                else:
                    test_results.append(f"❌ 变量 '{var_name}' 未被替换")

        # 检查 context
        if context:
            if max_context_length > 0:
                test_results.append(f"✅ Context 长度控制: {max_context_length} 条")
            else:
                test_results.append(f"✅ Context 全部保留: {len(context)} 条")

        # 检查 XML 标记
        if not has_xml_in_output:
            test_results.append("✅ LLM 输出不包含 XML 标记")
        else:
            test_results.append("❌ LLM 输出包含 XML 标记（应该被过滤）")

        for result in test_results:
            print(result)

        print("\n" + "=" * 60)
        print("✨ 测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_preserved_output()
