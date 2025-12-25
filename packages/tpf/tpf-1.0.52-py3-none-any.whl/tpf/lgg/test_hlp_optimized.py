#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
测试优化后的HLP类
验证model_path参数的功能
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, '/ai/wks/aitpf/src')

from tpf.lgg.hlp import HLP

def test_hlp_optimized():
    """测试优化后的HLP类"""

    print("=== HLP类优化测试 ===\n")

    # 先创建一个临时的配置，避免JVM启动
    temp_config = {"isjmv_running": True}  # 防止启动JVM

    # 测试1：使用默认路径
    print("1. 测试使用默认路径:")
    try:
        # 临时修改代码避免JVM启动
        import tpf.lgg.hlp as hlp_module
        original_start = hlp_module.HLP.start

        def dummy_start(self, model_path=None):
            if model_path is None:
                model_path = self.model_path
            print(f"   - 模拟启动JVM，路径: {model_path}")

        hlp_module.HLP.start = dummy_start

        hlp1 = hlp_module.HLP(config=temp_config)
        print(f"   - 模型路径: {hlp1.model_path}")
        print(f"   - 版本: {hlp1.version}")
        print(f"   - JAR文件: {hlp1.jar_name}")
        print("   ✅ 默认路径测试通过")

        # 恢复原方法
        hlp_module.HLP.start = original_start

    except Exception as e:
        print(f"   ❌ 默认路径测试失败: {e}")

    # 测试2：使用指定路径
    print("\n2. 测试使用指定路径:")
    try:
        custom_path = "/wks/models/HanLP"
        hlp2 = hlp_module.HLP(config=temp_config, model_path=custom_path)
        print(f"   - 模型路径: {hlp2.model_path}")
        print(f"   - 版本: {hlp2.version}")
        print(f"   - JAR文件: {hlp2.jar_name}")
        print("   ✅ 指定路径测试通过")
    except Exception as e:
        print(f"   ❌ 指定路径测试失败: {e}")

    # 测试3：指定版本和路径
    print("\n3. 测试指定版本和路径:")
    try:
        hlp3 = hlp_module.HLP(version="1.8", model_path="/wks/models/HanLP", config=temp_config)
        print(f"   - 模型路径: {hlp3.model_path}")
        print(f"   - 版本: {hlp3.version}")
        print(f"   - 版本目录: {hlp3.version_dir}")
        print(f"   - JAR文件: {hlp3.jar_name}")
        print("   ✅ 指定版本和路径测试通过")
    except Exception as e:
        print(f"   ❌ 指定版本和路径测试失败: {e}")

    # 测试4：路径构建验证
    print("\n4. 测试路径构建:")
    try:
        hlp4 = hlp_module.HLP(config=temp_config, model_path="/wks/models/HanLP")
        expected_jar_path = os.path.join(hlp4.model_path, hlp4.version_dir, hlp4.jar_name)
        print(f"   - 期望JAR路径: {expected_jar_path}")
        print(f"   - 路径存在: {os.path.exists(os.path.dirname(expected_jar_path))}")
        print("   ✅ 路径构建测试通过")
    except Exception as e:
        print(f"   ❌ 路径构建测试失败: {e}")

    # 测试5：不同版本
    print("\n5. 测试不同版本:")
    versions = ["1.5", "1.6", "1.8"]
    for version in versions:
        try:
            hlp5 = hlp_module.HLP(version=version, config=temp_config, model_path="/wks/models/HanLP")
            print(f"   - 版本 {version}: JAR={hlp5.jar_name}, 目录={hlp5.version_dir}")
            print(f"     ✅ 版本 {version} 测试通过")
        except Exception as e:
            print(f"     ❌ 版本 {version} 测试失败: {e}")

    print("\n=== 测试完成 ===")
    print("\n使用说明:")
    print("1. 默认使用: hlp = HLP()")
    print("2. 指定路径: hlp = HLP(model_path='/wks/models/HanLP')")
    print("3. 指定版本: hlp = HLP(version='1.8', model_path='/wks/models/HanLP')")
    print("4. 运行时指定: hlp.start(model_path='/custom/path')")

if __name__ == "__main__":
    test_hlp_optimized()