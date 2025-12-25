#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
测试优化的HanLP导入功能
验证pyhanlp可用性检测
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, '/ai/wks/aitpf/src')

def test_hanlp_import():
    """测试HanLP导入和可用性"""

    print("=== HanLP导入测试 ===\n")

    # 测试1: 检查pyhanlp导入状态
    print("1. 检查pyhanlp导入状态:")
    try:
        from tpf.nlp.text import HanLP, PYHANLP_AVAILABLE
        print(f"   - PYHANLP_AVAILABLE: {PYHANLP_AVAILABLE}")
        print(f"   - HanLP对象: {HanLP}")

        if PYHANLP_AVAILABLE:
            print("   ✅ pyhanlp已安装并可用")
        else:
            print("   ⚠️  pyhanlp未安装，HanLP设为None")

    except Exception as e:
        print(f"   ❌ 导入测试失败: {e}")

    print("\n2. 测试TLP类功能:")
    try:
        from tpf.nlp.text import TLP
        tlp = TLP()
        print("   ✅ TLP类实例化成功")

        # 测试文本
        test_text = "这是一个测试文本，用于验证HanLP功能。"

        # 测试分词功能
        print("\n3. 测试分词功能:")
        words = tlp.segment(test_text)
        print(f"   - 分词结果: {words}")

        if words:
            print("   ✅ HanLP分词功能正常")
        else:
            print("   ⚠️  HanLP分词功能不可用（可能未安装pyhanlp）")

        # 测试摘要功能
        print("\n4. 测试摘要功能:")
        summary = tlp.summary(test_text, n=3)
        print(f"   - 摘要结果: {summary}")

        if summary:
            print("   ✅ HanLP摘要功能正常")
        else:
            print("   ⚠️  HanLP摘要功能不可用（可能未安装pyhanlp）")

    except Exception as e:
        print(f"   ❌ TLP功能测试失败: {e}")

    print("\n5. 安装提示:")
    if 'PYHANLP_AVAILABLE' in locals() and not PYHANLP_AVAILABLE:
        print("   - 要使用HanLP功能，请安装pyhanlp:")
        print("     pip install pyhanlp")
    else:
        print("   - pyhanlp已安装")

    print("\n=== 测试完成 ===")
    print("\n使用说明:")
    print("1. 代码会自动检测pyhanlp是否安装")
    print("2. 如果未安装，HanLP变量为None，不会报错")
    print("3. 调用HanLP相关方法会返回空列表并显示警告")
    print("4. 可以通过PYHANLP_AVAILABLE变量检查可用性")

if __name__ == "__main__":
    test_hanlp_import()