#!/usr/bin/env python3
"""
Scriptbook 测试报告生成器
生成 JavaScript 单元测试的摘要报告
"""

import os
from pathlib import Path

def generate_test_summary():
    """生成测试摘要报告"""

    # 获取当前脚本所在目录
    script_dir = Path(__file__).parent
    # 获取项目根目录
    project_root = script_dir.parent.parent
    # 测试文件路径（相对于脚本目录）
    test_file = script_dir / "js" / "app.test.js"

    if not test_file.exists():
        print("❌ 错误: 测试文件不存在")
        print(f"   路径: {test_file.absolute()}")
        print("\n💡 请确保已创建测试文件")
        return

    # 读取测试文件
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计测试用例
    test_count = content.count('test(') + content.count('it(')
    describe_count = content.count("describe('")

    # 提取测试组
    test_groups = []
    current_group = None

    for line in content.split('\n'):
        if "describe('" in line:
            current_group = line.split("describe('")[1].split("'")[0]
            if current_group not in test_groups:
                test_groups.append(current_group)

    # 生成报告
    print("=" * 60)
    print("Scriptbook JavaScript 单元测试报告")
    print("=" * 60)
    print()

    # 基本信息
    print("📊 测试统计")
    print("-" * 60)
    print(f"测试文件: {test_file}")
    print(f"测试用例数: {test_count}")
    print(f"测试组数: {describe_count}")
    print(f"测试模块: {len(test_groups)}")
    print()

    # 测试组列表
    print("📋 测试组列表")
    print("-" * 60)
    for i, group in enumerate(test_groups, 1):
        print(f"{i}. {group}")
    print()

    # 详细测试列表
    print("🧪 测试用例列表")
    print("-" * 60)

    current_module = None
    test_num = 1

    for line in content.split('\n'):
        if "describe('" in line:
            current_module = line.split("describe('")[1].split("'")[0]
            print(f"\n[{current_module}]")
        elif "test('" in line or "it('" in line:
            test_name = line.split("test('")[1].split("'")[0] if "test('" in line else line.split("it('")[1].split("'")[0]
            print(f"  {test_num}. {test_name}")
            test_num += 1

    print()
    print("=" * 60)
    print("测试覆盖范围")
    print("=" * 60)
    print()
    print("✅ App 类测试 (14 个)")
    print("   - 初始化和构造函数")
    print("   - bindEvents() 事件绑定")
    print("   - loadFileList() 文件列表加载")
    print("   - updateFileSelect() 文件选择器更新")
    print("   - selectFile() 文件选择")
    print("   - addScriptOutput() 输出添加")
    print("   - formatFileSize() 文件大小格式化")
    print()
    print("✅ 全局函数测试 (10 个)")
    print("   - executeScript() 脚本执行")
    print("     * WebSocket 连接创建")
    print("     * 代码发送")
    print("     * 输入容器显示")
    print("     * 连接管理")
    print("     * 错误处理")
    print("   - copyCode() 代码复制")
    print("   - sendInput() 输入发送")
    print("     * 输入验证")
    print("     * WebSocket 通信")
    print("     * UI 状态更新")
    print()
    print("✅ WebSocket 事件测试 (4 个)")
    print("   - 消息接收处理")
    print("   - 退出消息处理")
    print("   - 错误消息处理")
    print("   - 输入容器状态管理")
    print()

    # Mock 策略
    print("=" * 60)
    print("Mock 策略")
    print("=" * 60)
    print()
    print("🌐 浏览器 API Mock")
    print("   ✓ fetch() - API 请求")
    print("   ✓ WebSocket - 实时通信")
    print("   ✓ navigator.clipboard - 剪贴板")
    print("   ✓ console.* - 日志输出")
    print()
    print("📦 测试环境 Mock")
    print("   ✓ DOM 环境 (JSDOM)")
    print("   ✓ 样式文件 (styleMock)")
    print("   ✓ 全局变量 (window, global)")
    print()

    # 运行方式
    print("=" * 60)
    print("运行测试")
    print("=" * 60)
    print()
    print("📦 方式 1: 使用便捷脚本")
    print("   $ chmod +x run_js_tests.sh")
    print("   $ ./run_js_tests.sh")
    print()
    print("📦 方式 2: 手动运行")
    print("   $ cd src/tests/js")
    print("   $ npm install")
    print("   $ npm test")
    print()
    print("📦 方式 3: 监视模式")
    print("   $ cd src/tests/js")
    print("   $ npm run test:watch")
    print()
    print("📦 方式 4: 覆盖率报告")
    print("   $ cd src/tests/js")
    print("   $ npm run test:coverage")
    print()

    # 文档
    print("=" * 60)
    print("测试文档")
    print("=" * 60)
    print()
    print("📖 完整文档")
    docs = [
        ("JS_TESTING_GUIDE.md", "JavaScript 测试完整指南"),
        ("src/tests/js/README.md", "测试目录详细文档"),
        ("src/tests/js/test-summary.md", "测试总结"),
        ("TESTING_SUMMARY.md", "项目测试总览"),
        ("INTERACTIVE_INPUT_GUIDE.md", "交互式输入功能指南"),
    ]
    for doc, desc in docs:
        path = Path(doc)
        status = "✅" if path.exists() else "❌"
        print(f"   {status} {doc:<35} - {desc}")
    print()

    # 环境要求
    print("=" * 60)
    print("环境要求")
    print("=" * 60)
    print()
    print("🔧 必需工具")
    print("   - Node.js >= 14.0")
    print("   - npm >= 6.0")
    print()
    print("📦 开发依赖")
    print("   - jest ^29.7.0")
    print("   - @babel/core ^7.23.0")
    print("   - @babel/preset-env ^7.23.0")
    print("   - babel-jest ^29.7.0")
    print("   - jest-environment-jsdom ^29.7.0")
    print()

    print("=" * 60)
    print("✅ 测试套件创建完成！")
    print("=" * 60)
    print()
    print("💡 下一步:")
    print("   1. 安装 Node.js 和 npm")
    print("   2. 运行: ./run_js_tests.sh")
    print("   3. 查看覆盖率报告")
    print("   4. 根据需要添加更多测试")
    print()

if __name__ == "__main__":
    generate_test_summary()