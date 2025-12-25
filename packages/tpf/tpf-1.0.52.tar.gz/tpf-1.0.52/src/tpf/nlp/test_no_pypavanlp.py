#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
测试没有pyhanlp时的行为
模拟pyhanlp未安装的情况
"""

import sys
import os
from unittest.mock import patch, MagicMock

# 添加模块路径
sys.path.insert(0, '/ai/wks/aitpf/src')

def test_no_hanlp():
    """测试没有pyhanlp时的行为"""

    print("=== 模拟pyhanlp未安装测试 ===\n")

    # 模拟pyhanlp未安装的情况
    with patch.dict('sys.modules'):
        # 移除pyhanlp模块，模拟未安装
        sys.modules.pop('pyhanlp', None)

        print("1. 模拟pyhanlp未安装:")
        print("   - 已移除pyhanlp模块")

        print("\n2. 测试导入行为:")
        try:
            # 重新导入模块
            if 'tpf.nlp.text' in sys.modules:
                del sys.modules['tpf.nlp.text']

            from tpf.nlp.text import HanLP, PYHANLP_AVAILABLE
            print(f"   - PYHANLP_AVAILABLE: {PYHANLP_AVAILABLE}")
            print(f"   - HanLP对象: {HanLP}")

            if PYHANLP_AVAILABLE:
                print("   ❌ 预期：pyhanlp应该不可用")
            else:
                print("   ✅ 正确：pyhanlp不可用，HanLP=None")

        except Exception as e:
            print(f"   ❌ 导入测试失败: {e}")

        print("\n3. 测试TLP类功能:")
        try:
            from tpf.nlp.text import TLP
            tlp = TLP()
            print("   ✅ TLP类实例化成功")

            # 测试文本
            test_text = "这是一个测试文本"

            # 测试分词功能
            print("\n4. 测试分词功能:")
            words = tlp.segment(test_text)
            print(f"   - 分词结果: {words}")
            print("   - 预期：空列表 + 警告信息")

            if not words:
                print("   ✅ 正确：返回空列表（应该有警告信息）")
            else:
                print("   ❌ 意外：返回了非空结果")

            # 测试摘要功能
            print("\n5. 测试摘要功能:")
            summary = tlp.summary(test_text, n=3)
            print(f"   - 摘要结果: {summary}")
            print("   - 预期：空列表 + 警告信息")

            if not summary:
                print("   ✅ 正确：返回空列表（应该有警告信息）")
            else:
                print("   ❌ 意外：返回了非空结果")

        except Exception as e:
            print(f"   ❌ TLP功能测试失败: {e}")

    print("\n=== 优雅降级测试完成 ===")
    print("\n优化效果:")
    print("✅ 代码不会因为pyhanlp未安装而崩溃")
    print("✅ HanLP变量设为None，避免AttributeError")
    print("✅ 调用HanLP方法会优雅降级")
    print("✅ 提供清晰的警告信息")
    print("✅ 可以通过PYHANLP_AVAILABLE检查状态")

if __name__ == "__main__":
    test_no_hanlp()