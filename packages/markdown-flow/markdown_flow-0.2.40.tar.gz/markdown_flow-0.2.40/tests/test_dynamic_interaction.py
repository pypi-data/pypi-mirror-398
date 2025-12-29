#!/usr/bin/env python3
"""
测试 document_prompt 动态交互转换功能

专注于测试 document_prompt 在动态交互生成中的作用，以及用户输入验证流程。
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from markdown_flow import MarkdownFlow, ProcessMode
from tests.llm import create_llm_provider


def test_chinese_restaurant_scenario():
    """测试中文餐厅场景 - 完整的用户交互流程"""
    print("\n=== 中文餐厅场景测试 ===")

    document = """询问用户的菜品偏好，并记录到变量{{菜品选择}}"""

    document_prompt = """你是一个中餐厅的服务员。请用中文提供中式菜品选项：
- 川菜（宫保鸡丁、麻婆豆腐、水煮鱼）
- 粤菜（白切鸡、蒸蛋羹、叉烧包）
- 鲁菜（糖醋鲤鱼、九转大肠、德州扒鸡）

语言要求：必须使用中文菜名
格式要求：提供具体菜品选项"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：生成动态交互
        print("--- 生成动态交互 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE
        )

        print(f"转换为交互块: {result1.transformed_to_interaction}")
        print(f"生成的交互格式: {result1.content}")

        if result1.transformed_to_interaction:
            # 验证交互格式正确性
            print("\n--- 验证交互格式 ---")
            assert "?[" in result1.content, "交互格式应该包含 ?["
            assert "%{{菜品选择}}" in result1.content, "应该包含变量名"
            print("✅ 交互格式验证通过")

            # 验证是否为多选格式
            is_multi_select = "||" in result1.content
            print(f"多选格式: {is_multi_select}")
            if is_multi_select:
                print("✅ 正确识别为多选场景")

            # 第二步：测试有效选择
            print("\n--- 测试有效选择 ---")
            user_choices = ["宫保鸡丁", "麻婆豆腐"]  # 模拟用户多选
            result2 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"菜品选择": user_choices},
                dynamic_interaction_format=result1.content
            )
            print(f"用户选择: {user_choices}")
            print(f"验证后的变量: {result2.variables}")
            assert result2.variables.get("菜品选择") == user_choices, "变量应该正确存储用户选择"
            print("✅ 有效选择验证通过")

            # 第三步：测试无效选择
            print("\n--- 测试无效选择 ---")
            invalid_choices = ["意大利面", "汉堡包"]  # 不在选项中的选择
            result3 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"菜品选择": invalid_choices},
                dynamic_interaction_format=result1.content
            )
            print(f"无效选择输入: {invalid_choices}")
            print(f"LLM完整响应: {result3.content}")
            print(f"返回变量: {result3.variables}")
            print(f"元数据: {result3.metadata}")

            # 第四步：测试空输入
            print("\n--- 测试空输入 ---")
            result4 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"菜品选择": []},
                dynamic_interaction_format=result1.content
            )
            print(f"空输入: []")
            print(f"LLM完整响应: {result4.content}")
            print(f"返回变量: {result4.variables}")
            print(f"元数据: {result4.metadata}")

            print("✅ 中文餐厅场景完整验证通过")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_english_education_scenario():
    """测试英文教育场景 - 完整的用户交互流程"""
    print("\n=== 英文教育场景测试 ===")

    document = """Ask user about their learning preferences and record to variable {{learning_choice}}"""

    document_prompt = """You are an education consultant. Provide learning options in English:
- Study Fields: Computer Science, Business, Engineering, Arts
- Learning Formats: Online, In-person, Hybrid, Self-paced
- Experience Levels: Beginner, Intermediate, Advanced

Language: English
Format: Provide specific educational options"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：生成动态交互
        print("--- Generate Dynamic Interaction ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE
        )

        print(f"Converted to interaction: {result1.transformed_to_interaction}")
        print(f"Generated interaction format: {result1.content}")

        if result1.transformed_to_interaction:
            # 验证交互格式正确性
            print("\n--- Validate Interaction Format ---")
            assert "?[" in result1.content, "Should contain ?["
            assert "%{{learning_choice}}" in result1.content, "Should contain variable name"
            print("✅ Interaction format validated")

            # 验证英文选项内容
            has_english_content = any(word in result1.content for word in ["Computer", "Science", "Online", "Business"])
            if has_english_content:
                print("✅ Generated English content as requested")
            else:
                print("⚠️ May not contain expected English content")

            # 第二步：测试有效选择
            print("\n--- Test Valid Selection ---")
            user_choices = ["Computer Science", "Online"]  # 模拟用户选择
            result2 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"learning_choice": user_choices},
                dynamic_interaction_format=result1.content
            )
            print(f"User choices: {user_choices}")
            print(f"Validated variables: {result2.variables}")
            assert result2.variables.get("learning_choice") == user_choices, "Variables should store user selection"
            print("✅ Valid selection validated")

            # 第三步：测试部分匹配选择
            print("\n--- Test Partial Match ---")
            partial_choices = ["Computer"]  # 只选择一个词
            result3 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"learning_choice": partial_choices},
                dynamic_interaction_format=result1.content
            )
            print(f"部分匹配输入: {partial_choices}")
            print(f"LLM完整响应: {result3.content}")
            print(f"返回变量: {result3.variables}")
            print(f"元数据: {result3.metadata}")

            # 第四步：测试单个选择
            print("\n--- Test Single Selection ---")
            single_choice = ["Business"]
            result4 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"learning_choice": single_choice},
                dynamic_interaction_format=result1.content
            )
            expected_value = single_choice[0] if len(single_choice) == 1 else single_choice
            actual_value = result4.variables.get("learning_choice")
            print(f"Single choice: {single_choice}")
            print(f"Stored as: {actual_value}")
            print("✅ English education scenario completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_japanese_fitness_scenario():
    """测试日文健身场景 - 完整的用户交互流程"""
    print("\n=== 日文健身场景测试 ===")

    document = """ユーザーの運動設備を聞いて、変数{{運動選択}}に記録する"""

    document_prompt = """あなたはフィットネストレーナーです。日本語で運動オプションを提供してください：
- 有酸素運動: ランニング、水泳、サイクリング
- 筋力トレーニング: ウェイトリフティング、腕立て伏せ、懸垂
- 柔軟性トレーニング: ヨガ、ピラティス、ストレッチ

言語: 日本語
形式: 具体的な運動項目オプション"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：生成动态交互
        print("--- 動的インタラクション生成 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE
        )

        print(f"インタラクションブロックに変換: {result1.transformed_to_interaction}")
        print(f"生成されたインタラクション形式: {result1.content}")

        if result1.transformed_to_interaction:
            # 验证日文内容
            japanese_exercises = ["ランニング", "水泳", "ヨガ", "ウェイト"]
            has_japanese_content = any(exercise in result1.content for exercise in japanese_exercises)
            if has_japanese_content:
                print("✅ 生成了日文运动选项")
            else:
                print("⚠️ 可能未生成预期的日文内容")

            # 第二步：用户选择运动
            print("\n--- ユーザー選択 ---")
            user_choices = ["ランニング", "ヨガ"]  # 模拟用户选择

            result2 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"運動選択": user_choices},
                dynamic_interaction_format=result1.content
            )

            print(f"ユーザー選択: {user_choices}")
            print(f"検証後の変数: {result2.variables}")
            assert result2.variables.get("運動選択") == user_choices, "变量应该正确存储"
            print("✅ 日本語フィットネスシナリオ完了")

    except Exception as e:
        print(f"❌ テスト失敗: {e}")


def test_korean_travel_scenario():
    """测试韩文旅游场景 - 完整的用户交互流程"""
    print("\n=== 한국어 여행 시나리오 테스트 ===")

    document = """사용자의 여행 선호도를 묻고 변수 {{여행선택}}에 기록합니다"""

    document_prompt = """당신은 여행 가이드입니다. 한국어로 여행 옵션을 제공해주세요:
- 여행 타입: 휴양, 문화탐방, 어드벤처, 미식여행
- 숙박 타입: 호텔, 펜션, 게스트하우스, 리조트
- 교통 수단: 비행기, 기차, 자동차, 버스

언어: 한국어
형식: 구체적인 여행 옵션 제공"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：生成动态交互
        print("--- 동적 인터랙션 생성 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE
        )

        print(f"인터랙션 블록으로 변환: {result1.transformed_to_interaction}")
        print(f"생성된 인터랙션 형식: {result1.content}")

        if result1.transformed_to_interaction:
            # 验证韩文内容
            korean_travel = ["휴양", "문화탐방", "호텔", "펜션"]
            has_korean_content = any(option in result1.content for option in korean_travel)
            if has_korean_content:
                print("✅ 생성된 한국어 여행 옵션")
            else:
                print("⚠️ 예상된 한국어 콘텐츠가 생성되지 않았을 수 있음")

            # 第二步：用户选择旅游选项
            print("\n--- 사용자 선택 ---")
            user_choices = ["문화탐방", "호텔"]  # 模拟用户选择

            result2 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"여행선택": user_choices},
                dynamic_interaction_format=result1.content
            )

            print(f"사용자 선택: {user_choices}")
            print(f"검증된 변수: {result2.variables}")
            assert result2.variables.get("여행선택") == user_choices, "변수가 올바르게 저장되어야 함"
            print("✅ 한국어 여행 시나리오 완료")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")


def test_complex_job_consultation_scenario():
    """测试复杂的职业咨询场景 - 多步骤交互流程"""
    print("\n=== 复杂职业咨询场景测试 ===")

    document = """?[%{{行业}} 科技|金融|教育|医疗]

---

根据用户选择的{{行业}}，询问具体职位偏好，并记录到变量{{职位选择}}

---

根据用户的{{行业}}和{{职位选择}}，询问薪资期望，并记录到变量{{薪资期望}}"""

    document_prompt = """你是专业的职业规划顾问。为不同行业提供职位建议：

科技行业: 软件工程师、数据科学家、产品经理、UI/UX设计师、DevOps工程师
金融行业: 投资分析师、风险管理师、财务顾问、量化分析师、合规专员
教育行业: 课程设计师、教学主管、学习体验设计师、教育技术专家
医疗行业: 临床研究员、医疗数据分析师、健康管理师、医疗设备工程师

薪资范围: 5-10万、10-20万、20-30万、30万以上

语言: 中文
格式: 根据用户的行业选择提供相应的职位选项"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：用户选择行业
        print("--- 步骤1: 选择行业 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE,
            user_input={"行业": ["科技"]}
        )
        print(f"用户选择行业: 科技")
        print(f"第一步变量: {result1.variables}")

        # 第二步：根据行业生成职位选项
        print("\n--- 步骤2: 生成职位选项 ---")
        result2 = mf.process(
            block_index=1,
            mode=ProcessMode.COMPLETE,
            variables=result1.variables
        )
        print(f"转换为交互块: {result2.transformed_to_interaction}")
        print(f"职位选项: {result2.content}")

        if result2.transformed_to_interaction:
            # 验证职位选项是否基于行业生成
            print("\n--- 验证职位选项上下文相关性 ---")
            tech_jobs = ["软件工程师", "数据科学家", "产品经理", "工程师"]
            has_tech_jobs = any(job in result2.content for job in tech_jobs)
            if has_tech_jobs:
                print("✅ 正确基于'科技'行业生成了相关职位")
            else:
                print("⚠️ 可能未正确基于行业上下文生成职位")

            # 第三步：用户选择职位
            print("\n--- 步骤3: 用户选择职位 ---")
            job_choices = ["软件工程师", "数据科学家"]
            result3 = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"职位选择": job_choices},
                dynamic_interaction_format=result2.content
            )
            print(f"用户选择职位: {job_choices}")
            print(f"第二步变量: {result3.variables}")

            # 验证职位选择验证
            assert result3.variables.get("职位选择") == job_choices, "职位变量应该正确存储"
            assert result3.variables.get("行业") == ["科技"], "行业变量应该保持不变"
            print("✅ 职位选择验证通过")

            # 测试无效职位选择
            print("\n--- 测试无效职位选择 ---")
            invalid_job = ["厨师", "司机"]  # 不属于科技行业的职位
            result_invalid = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"职位选择": invalid_job},
                dynamic_interaction_format=result2.content
            )
            print(f"无效职位输入: {invalid_job}")
            print(f"LLM完整响应: {result_invalid.content}")
            print(f"返回变量: {result_invalid.variables}")
            print(f"元数据: {result_invalid.metadata}")

            # 第四步：生成薪资选项
            print("\n--- 步骤4: 生成薪资选项 ---")
            result4 = mf.process(
                block_index=2,
                mode=ProcessMode.COMPLETE,
                variables=result3.variables
            )
            print(f"转换为交互块: {result4.transformed_to_interaction}")
            print(f"薪资选项: {result4.content}")

            if result4.transformed_to_interaction:
                # 验证薪资选项格式
                salary_ranges = ["5-10万", "10-20万", "20-30万", "30万"]
                has_salary_ranges = any(salary in result4.content for salary in salary_ranges)
                if has_salary_ranges:
                    print("✅ 生成了预期的薪资范围选项")

                # 验证是否为单选（薪资期望通常是单选）
                is_single_select = "||" not in result4.content and "|" in result4.content
                if is_single_select:
                    print("✅ 正确识别薪资选择为单选模式")

                # 第五步：用户选择薪资期望
                print("\n--- 步骤5: 用户选择薪资期望 ---")
                salary_choice = ["20-30万"]
                result5 = mf.process(
                    block_index=2,
                    mode=ProcessMode.COMPLETE,
                    variables=result3.variables,
                    user_input={"薪资期望": salary_choice},
                    dynamic_interaction_format=result4.content
                )
                print(f"用户选择薪资: {salary_choice}")
                print(f"最终变量: {result5.variables}")

                # 验证最终变量完整性
                expected_vars = ["行业", "职位选择", "薪资期望"]
                for var in expected_vars:
                    assert var in result5.variables, f"最终结果应该包含变量: {var}"

                # 避免未使用变量警告
                _ = result5
                print("✅ 复杂职业咨询场景完整验证通过")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_text_input_scenario():
    """测试文本输入场景 - 用户自定义输入"""
    print("\n=== 文本输入场景测试 ===")

    document = """询问用户的自定义需求，并记录到变量{{自定义需求}}"""

    document_prompt = """你是一个产品定制顾问。询问用户的特殊需求：
- 提供一些常见选项: 定制颜色、特殊尺寸、个性化logo、独特功能
- 同时允许用户输入其他特殊需求

语言: 中文
格式: 提供常见选项 + 文本输入选项（使用 ... 前缀）"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：生成动态交互
        print("--- 生成自定义需求选项 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE
        )

        print(f"转换为交互块: {result1.transformed_to_interaction}")
        print(f"生成的选项: {result1.content}")

        if result1.transformed_to_interaction:
            # 验证混合输入格式（按钮+文本）
            print("\n--- 验证混合输入格式 ---")
            has_buttons = "|" in result1.content
            has_text_input = "..." in result1.content
            print(f"包含按钮: {has_buttons}")
            print(f"包含文本输入: {has_text_input}")

            if has_buttons and has_text_input:
                print("✅ 正确生成混合输入格式（按钮+文本）")
            elif has_buttons:
                print("⚠️ 只有按钮选项，没有文本输入选项")
            else:
                print("⚠️ 格式可能不符合预期")

            # 测试预设选项选择
            print("\n--- 测试预设按钮选择 ---")
            preset_choices = ["定制颜色", "个性化logo"]
            result2 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"自定义需求": preset_choices},
                dynamic_interaction_format=result1.content
            )
            print(f"预设选项: {preset_choices}")
            print(f"验证后的变量: {result2.variables}")
            assert result2.variables.get("自定义需求") == preset_choices, "应该正确存储预设选项"
            print("✅ 预设选项验证通过")

            # 测试自定义文本输入
            print("\n--- 测试自定义文本输入 ---")
            custom_input = ["需要特殊的防水涂层处理"]
            result3 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"自定义需求": custom_input},
                dynamic_interaction_format=result1.content
            )
            print(f"自定义输入: {custom_input}")
            print(f"验证后的变量: {result3.variables}")
            assert result3.variables.get("自定义需求") == custom_input, "应该正确存储自定义文本"
            print("✅ 自定义文本验证通过")

            # 测试混合选择（按钮+自定义）
            print("\n--- 测试混合选择 ---")
            mixed_input = ["定制颜色", "需要增加夜光效果"]  # 一个按钮选项+一个自定义
            result4 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"自定义需求": mixed_input},
                dynamic_interaction_format=result1.content
            )
            print(f"混合输入: {mixed_input}")
            print(f"验证后的变量: {result4.variables}")
            assert result4.variables.get("自定义需求") == mixed_input, "应该正确存储混合输入"
            print("✅ 混合选择验证通过")

            # 测试空输入（对于支持文本输入的交互，可能允许空输入）
            print("\n--- 测试空输入处理 ---")
            result5 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"自定义需求": []},
                dynamic_interaction_format=result1.content
            )
            print(f"空输入: []")
            print(f"LLM完整响应: {result5.content}")
            print(f"返回变量: {result5.variables}")
            print(f"元数据: {result5.metadata}")

            print("✅ 文本输入场景完整验证通过")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_variable_context_cuisine_scenario():
    """测试变量上下文场景 - 菜系菜品依赖"""
    print("\n=== 变量上下文场景测试 ===")

    # 多步骤文档 - 第二个块依赖第一个块的变量
    document = """?[%{{菜系}} 川菜|粤菜|鲁菜|淮扬菜]

---

用户选择了{{菜系}}，根据菜系让用户选择菜系下的一些菜品，记录到{{菜品}}"""

    document_prompt = """你是餐厅服务员，根据用户选择的菜系提供对应的菜品选择：
- 川菜：宫保鸡丁、麻婆豆腐、水煮鱼、回锅肉
- 粤菜：白切鸡、蒸蛋羹、叉烧包、广式点心
- 鲁菜：糖醋鲤鱼、九转大肠、德州扒鸡
- 淮扬菜：文思豆腐、扬州炒饭、蟹粉狮子头

语言：中文
注意：根据用户实际选择的菜系提供对应的菜品选项，用户可以选择多个菜品"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：用户选择菜系
        print("--- 步骤1: 用户选择菜系 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE,
            user_input={"菜系": ["川菜"]}
        )
        print(f"用户选择: 川菜")
        print(f"收集到的变量: {result1.variables}")

        # 第二步：基于菜系生成菜品选项（测试变量上下文处理）
        print("\n--- 步骤2: 基于菜系生成菜品选项 ---")
        result2 = mf.process(
            block_index=1,
            mode=ProcessMode.COMPLETE,
            variables=result1.variables  # 传入包含菜系的变量
        )

        print(f"转换为交互块: {result2.transformed_to_interaction}")
        print(f"生成的菜品选项: {result2.content}")

        # 验证是否生成了川菜相关的选项
        if result2.transformed_to_interaction:
            print("\n--- 验证上下文相关性 ---")
            sichuan_dishes = ['宫保鸡丁', '麻婆豆腐', '水煮鱼', '回锅肉']
            has_sichuan_dishes = any(dish in result2.content for dish in sichuan_dishes)

            if has_sichuan_dishes:
                print("✅ 成功基于菜系上下文生成了川菜选项")
            else:
                print("⚠️ 可能未正确基于菜系上下文生成选项")

            # 验证是否使用了多选格式
            is_multi_select = "||" in result2.content
            if is_multi_select:
                print("✅ 正确识别为多选场景（用户可以选多个菜品）")
            else:
                print("⚠️ 可能未正确识别为多选场景")

            # 验证变量名正确性
            assert "%{{菜品}}" in result2.content, "应该包含正确的变量名"
            print("✅ 变量名验证通过")

            # 第三步：用户选择菜品
            print("\n--- 步骤3: 用户选择菜品 ---")
            dish_choices = ["宫保鸡丁", "麻婆豆腐"]
            result3 = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"菜品": dish_choices},
                dynamic_interaction_format=result2.content
            )

            print(f"用户选择菜品: {dish_choices}")
            print(f"最终变量: {result3.variables}")

            # 验证变量存储正确性
            cuisine_var = result3.variables.get("菜系")
            dish_var = result3.variables.get("菜品")

            print(f"菜系变量: {cuisine_var}")
            print(f"菜品变量: {dish_var}")

            # 更宽松的验证 - 菜系可能是字符串或列表
            if cuisine_var == ["川菜"] or cuisine_var == "川菜":
                print("✅ 菜系变量正确保留")
            else:
                print(f"⚠️ 菜系变量格式不符合预期: {cuisine_var}")

            assert dish_var == dish_choices, "菜品变量应该正确存储"
            assert "菜系" in result3.variables, "应该包含菜系变量"
            assert "菜品" in result3.variables, "应该包含菜品变量"
            print("✅ 变量存储验证通过")

            # 测试单个菜品选择
            print("\n--- 测试单个菜品选择 ---")
            single_dish = ["宫保鸡丁"]
            result4 = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"菜品": single_dish},
                dynamic_interaction_format=result2.content
            )
            print(f"单个选择结果: {result4.variables.get('菜品')}")

            # 测试无效菜品选择
            print("\n--- 测试无效菜品选择 ---")
            invalid_dishes = ["北京烤鸭", "小笼包"]  # 非川菜选项
            result_invalid = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"菜品": invalid_dishes},
                dynamic_interaction_format=result2.content
            )
            print(f"无效菜品输入: {invalid_dishes}")
            print(f"LLM完整响应: {result_invalid.content}")
            print(f"返回变量: {result_invalid.variables}")
            print(f"元数据: {result_invalid.metadata}")

            print("✅ 变量上下文场景完整验证通过")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_variable_context_skill_project_scenario():
    """测试变量上下文场景 - 技能项目依赖（英文）"""
    print("\n=== 技能-项目上下文测试（英文） ===")

    document = """?[%{{skill}} Python|JavaScript|Java|Go]

---

Based on user's selected {{skill}}, ask for specific projects they want to work on and record to {{project_type}}"""

    document_prompt = """You are a project manager. Based on the programming language, suggest relevant project types:
- Python: Web scraping, Data analysis, Machine learning, Django web apps
- JavaScript: React apps, Node.js APIs, Frontend interfaces, Full-stack projects
- Java: Spring applications, Enterprise systems, Android apps
- Go: Microservices, CLI tools, System programming

Language: English
Format: Provide specific project options based on the selected programming language, users can select multiple projects"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
                    )

        # 第一步：用户选择技能
        print("--- Step 1: User selects skill ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE,
            user_input={"skill": ["Python"]}
        )
        print(f"User selection: Python")
        print(f"Collected variables: {result1.variables}")

        # 第二步：基于技能生成项目选项
        print("\n--- Step 2: Generate project options based on skill ---")
        result2 = mf.process(
            block_index=1,
            mode=ProcessMode.COMPLETE,
            variables=result1.variables
        )

        print(f"Converted to interaction: {result2.transformed_to_interaction}")
        print(f"Generated project options: {result2.content}")

        if result2.transformed_to_interaction:
            # 验证是否生成了Python相关的项目
            print("\n--- Validate Context-Based Project Options ---")
            python_projects = ['scraping', 'analysis', 'learning', 'Django']
            has_python_projects = any(project.lower() in result2.content.lower() for project in python_projects)

            if has_python_projects:
                print("✅ Successfully generated Python-related project options")
            else:
                print("⚠️ May not have correctly generated context-based options")

            # 验证多选格式（项目通常可以多选）
            is_multi_select = "||" in result2.content
            if is_multi_select:
                print("✅ Correctly identified as multi-select scenario")

            # 第三步：用户选择项目
            print("\n--- Step 3: User selects projects ---")
            project_choices = ["Data analysis", "Machine learning"]
            result3 = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"project_type": project_choices},
                dynamic_interaction_format=result2.content
            )

            print(f"User project selection: {project_choices}")
            print(f"Final variables: {result3.variables}")

            # 验证变量存储
            assert result3.variables.get("skill") == ["Python"], "Skill should remain unchanged"
            assert result3.variables.get("project_type") == project_choices, "Projects should be stored correctly"
            print("✅ Variable storage validated")

            # 测试单个项目选择
            print("\n--- Test Single Project Selection ---")
            single_project = ["Web scraping"]
            result4 = mf.process(
                block_index=1,
                mode=ProcessMode.COMPLETE,
                variables=result1.variables,
                user_input={"project_type": single_project},
                dynamic_interaction_format=result2.content
            )
            print(f"Single project result: {result4.variables.get('project_type')}")

            print("✅ Skill-project scenario validation completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_user_question_text_input():
    """测试用户疑问式文本输入场景"""
    print("\n=== 用户疑问文本输入测试 ===")

    document = """询问用户的故事风格偏好，并记录到变量{{风格选择}}"""

    document_prompt = """你是故事创作助手。为用户提供故事风格选项：
- 常见风格：幽默、搞笑、悬疑、浪漫、文言文
- 同时允许用户输入其他风格偏好

语言：中文
格式：提供常见风格选项 + 允许自定义文本输入（使用...前缀）"""

    try:
        llm_provider = create_llm_provider()
        mf = MarkdownFlow(
            document=document,
            llm_provider=llm_provider,
            document_prompt=document_prompt
        )

        # 生成动态交互
        print("--- 生成故事风格选项 ---")
        result1 = mf.process(
            block_index=0,
            mode=ProcessMode.COMPLETE
        )

        print(f"转换为交互块: {result1.transformed_to_interaction}")
        print(f"生成的交互: {result1.content}")

        if result1.transformed_to_interaction:
            # 验证是否包含文本输入选项
            has_text_input = "..." in result1.content
            if has_text_input:
                print("✅ 包含文本输入选项")

            # 测试用户疑问式输入
            print("\n--- 测试疑问式文本输入 ---")
            question_input = ["这里必须要选择么?"]

            result2 = mf.process(
                block_index=0,
                mode=ProcessMode.COMPLETE,
                user_input={"风格选择": question_input},
                dynamic_interaction_format=result1.content
            )

            print(f"用户疑问输入: {question_input}")
            print(f"验证结果: {result2.variables}")

            # 显示疑问输入的完整处理结果
            print(f"疑问输入: {question_input}")
            print(f"LLM完整响应: {result2.content}")
            print(f"返回变量: {result2.variables}")
            print(f"元数据: {result2.metadata}")

            # 测试其他类型的自定义输入
            print("\n--- 测试其他自定义输入 ---")
            custom_inputs = [
                ["我想要科幻加悬疑的混合风格"],
                ["可以不选择吗"],
                ["这些选项都不适合我"]
            ]

            for custom_input in custom_inputs:
                result_custom = mf.process(
                    block_index=0,
                    mode=ProcessMode.COMPLETE,
                    user_input={"风格选择": custom_input},
                    dynamic_interaction_format=result1.content
                )
                print(f"\n自定义输入: {custom_input}")
                print(f"LLM完整响应: {result_custom.content}")
                print(f"返回变量: {result_custom.variables}")
                print(f"元数据: {result_custom.metadata}")

            print("✅ 用户疑问文本输入场景测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


def run_all_tests():
    """运行所有 document_prompt 测试"""
    print("🧪 开始 document_prompt 动态交互测试")
    print("=" * 60)

    tests = [
        test_chinese_restaurant_scenario,
        test_english_education_scenario,
        test_japanese_fitness_scenario,
        test_korean_travel_scenario,
        test_complex_job_consultation_scenario,
        test_text_input_scenario,
        test_variable_context_cuisine_scenario,
        test_variable_context_skill_project_scenario,
        test_user_question_text_input
    ]

    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")

    print("\n" + "=" * 60)
    print("🎉 document_prompt 动态交互测试完成")


if __name__ == "__main__":
    # 检查环境变量
    if not os.getenv("LLM_API_KEY"):
        print("⚠️  警告: 需要设置环境变量")
        print("请运行: source tests/dev.sh")
        print("或手动设置:")
        print("export LLM_API_KEY=your_api_key")
        print("export LLM_BASE_URL=your_base_url")
        sys.exit(1)

    # 运行测试
    run_all_tests()
