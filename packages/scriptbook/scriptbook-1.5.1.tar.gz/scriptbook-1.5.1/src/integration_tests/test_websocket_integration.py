#!/usr/bin/env python3
"""
WebSocket脚本执行集成测试

测试WebSocket端点是否能正常工作，使用TestServer fixture
"""

import asyncio
import json
import websockets
import sys
import pytest
import os


@pytest.mark.asyncio
async def test_websocket_script_execution(test_server):
    """测试WebSocket脚本执行"""
    # 使用test_server的base_url构建WebSocket URL
    base_url = test_server.base_url
    # 将http://替换为ws://
    ws_url = base_url.replace("http://", "ws://") + "/api/scripts/test_script/execute"

    print(f"🔌 连接WebSocket: {ws_url}")
    try:
        # 禁用代理，避免SOCKS代理错误
        os.environ['no_proxy'] = '*'
        os.environ['NO_PROXY'] = '*'
        async with websockets.connect(ws_url, proxy=None) as websocket:
            print("✅ 连接成功")

            # 发送测试脚本
            test_code = "echo 'Hello, World!'\ndate"
            print(f"📤 发送脚本代码: {test_code[:50]}...")
            await websocket.send(json.dumps({"code": test_code}))

            # 接收消息
            message_count = 0
            async for message in websocket:
                message_count += 1
                data = json.loads(message)
                print(f"📨 消息 #{message_count}: [{data['type']}] {data['content'][:60]}")

                # 如果是退出消息，结束测试
                if data['type'] == 'exit':
                    print("✅ 脚本执行完成")
                    break

                # 限制接收消息数量
                if message_count > 20:
                    print("⚠️  接收消息过多，退出")
                    break

    except Exception as e:
        pytest.fail(f"WebSocket测试失败: {e}")


@pytest.mark.asyncio
async def test_websocket_multiple_scripts(test_server):
    """测试多个WebSocket脚本执行"""
    base_url = test_server.base_url
    ws_url = base_url.replace("http://", "ws://") + "/api/scripts/test_script/execute"

    print(f"🔌 连接WebSocket: {ws_url}")
    try:
        # 禁用代理，避免SOCKS代理错误
        os.environ['no_proxy'] = '*'
        os.environ['NO_PROXY'] = '*'
        async with websockets.connect(ws_url, proxy=None) as websocket:
            print("✅ 连接成功")

            # 发送第一个脚本
            test_code1 = "echo 'First script'\necho 'Hello from script 1'"
            await websocket.send(json.dumps({"code": test_code1}))

            # 接收消息直到退出
            exit_received = False
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'exit':
                    exit_received = True
                    break

            assert exit_received, "未收到第一个脚本的退出消息"
            print("✅ 第一个脚本执行完成")

    except Exception as e:
        pytest.fail(f"WebSocket多个脚本测试失败: {e}")


@pytest.mark.asyncio
async def test_websocket_interactive_input(test_server):
    """测试WebSocket交互式输入功能"""
    base_url = test_server.base_url
    ws_url = base_url.replace("http://", "ws://") + "/api/scripts/test_script/execute"

    print(f"🔌 连接WebSocket: {ws_url}")
    try:
        # 禁用代理，避免SOCKS代理错误
        os.environ['no_proxy'] = '*'
        os.environ['NO_PROXY'] = '*'
        async with websockets.connect(ws_url, proxy=None) as websocket:
            print("✅ 连接成功")

            # 发送需要交互式输入的脚本
            test_code = '''echo "请输入你的名字："
read name
echo "你好, $name!"
echo "输入完成"'''

            print(f"📤 发送交互式脚本代码")
            await websocket.send(json.dumps({"code": test_code}))

            # 接收初始输出
            received_echo = False
            received_prompt = False
            input_sent = False

            async for message in websocket:
                data = json.loads(message)
                print(f"📨 收到: [{data['type']}] {data['content'][:60]}")

                # 检查是否收到提示信息
                if data['type'] == 'stdout' and '请输入你的名字' in data['content']:
                    received_prompt = True
                    print("✅ 收到输入提示")

                    # 发送输入
                    print("📤 发送输入: John")
                    await websocket.send(json.dumps({"type": "input", "content": "John"}))
                    input_sent = True

                # 检查是否收到输入回显
                if data['type'] == 'stdout' and '你好, John' in data['content']:
                    print("✅ 收到输入响应")
                    break

                # 如果是退出消息，结束测试
                if data['type'] == 'exit':
                    print("✅ 脚本执行完成")
                    break

            # 验证测试结果
            assert received_prompt, "未收到输入提示"
            assert input_sent, "未发送输入"
            print("✅ 交互式输入测试通过")

    except Exception as e:
        pytest.fail(f"WebSocket交互式输入测试失败: {e}")


@pytest.mark.asyncio
async def test_websocket_interactive_read_command(test_server):
    """测试read命令的交互式输入"""
    base_url = test_server.base_url
    ws_url = base_url.replace("http://", "ws://") + "/api/scripts/test_script/execute"

    print(f"🔌 连接WebSocket: {ws_url}")
    try:
        # 禁用代理，避免SOCKS代理错误
        os.environ['no_proxy'] = '*'
        os.environ['NO_PROXY'] = '*'
        async with websockets.connect(ws_url, proxy=None) as websocket:
            print("✅ 连接成功")

            # 发送包含read命令的脚本
            test_code = '''echo "Enter your age:"
read age
echo "You are $age years old"'''

            print(f"📤 发送read命令脚本")
            await websocket.send(json.dumps({"code": test_code}))

            # 接收输出并发送输入
            input_sent = False
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 收到: [{data['type']}] {data['content'][:60]}")

                # 当收到提示时发送输入
                if data['type'] == 'stdout' and 'Enter your age' in data['content']:
                    if not input_sent:
                        print("📤 发送输入: 25")
                        await websocket.send(json.dumps({"type": "input", "content": "25"}))
                        input_sent = True

                # 检查响应
                if data['type'] == 'stdout' and 'You are 25 years old' in data['content']:
                    print("✅ read命令交互测试通过")
                    break

                if data['type'] == 'exit':
                    print("✅ 脚本执行完成")
                    break

            assert input_sent, "未发送输入"
            print("✅ read命令交互式输入测试通过")

    except Exception as e:
        pytest.fail(f"read命令交互式输入测试失败: {e}")


@pytest.mark.asyncio
async def test_websocket_interactive_multiple_inputs(test_server):
    """测试多行交互式输入"""
    base_url = test_server.base_url
    ws_url = base_url.replace("http://", "ws://") + "/api/scripts/test_script/execute"

    print(f"🔌 连接WebSocket: {ws_url}")
    try:
        # 禁用代理，避免SOCKS代理错误
        os.environ['no_proxy'] = '*'
        os.environ['NO_PROXY'] = '*'
        async with websockets.connect(ws_url, proxy=None) as websocket:
            print("✅ 连接成功")

            # 发送需要多次输入的脚本
            test_code = '''echo "Enter your name:"
read name
echo "Hello, $name!"
echo "Enter your age:"
read age
echo "You are $age years old"'''

            print(f"📤 发送多行输入脚本")
            await websocket.send(json.dumps({"code": test_code}))

            # 接收输出并发送多次输入
            inputs_sent = 0
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 收到: [{data['type']}] {data['content'][:60]}")

                # 第一次输入
                if data['type'] == 'stdout' and 'Enter your name' in data['content']:
                    if inputs_sent == 0:
                        print("📤 发送输入: Alice")
                        await websocket.send(json.dumps({"type": "input", "content": "Alice"}))
                        inputs_sent += 1

                # 第二次输入
                if data['type'] == 'stdout' and 'Enter your age' in data['content']:
                    if inputs_sent == 1:
                        print("📤 发送输入: 30")
                        await websocket.send(json.dumps({"type": "input", "content": "30"}))
                        inputs_sent += 1

                # 检查最终响应
                if data['type'] == 'stdout' and 'You are 30 years old' in data['content']:
                    print("✅ 多行输入测试通过")
                    break

                if data['type'] == 'exit':
                    print("✅ 脚本执行完成")
                    break

            assert inputs_sent == 2, f"应该发送2次输入，实际发送了{inputs_sent}次"
            print("✅ 多行交互式输入测试通过")

    except Exception as e:
        pytest.fail(f"多行交互式输入测试失败: {e}")


@pytest.mark.asyncio
async def test_websocket_tty_command(test_server):
    """测试 tty 命令（验证 PTY 分配）"""
    base_url = test_server.base_url
    ws_url = base_url.replace("http://", "ws://") + "/api/scripts/test_script/execute"

    print(f"🔌 连接WebSocket: {ws_url}")
    try:
        # 禁用代理，避免SOCKS代理错误
        os.environ['no_proxy'] = '*'
        os.environ['NO_PROXY'] = '*'
        async with websockets.connect(ws_url, proxy=None) as websocket:
            print("✅ 连接成功")

            # 发送 tty 命令
            test_code = "tty"
            print(f"📤 发送 tty 命令")
            await websocket.send(json.dumps({"code": test_code}))

            # 接收输出
            tty_output = None
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 收到: [{data['type']}] {data['content'][:60]}")

                if data['type'] == 'stdout':
                    # tty 输出应该是 /dev/ttys* 或 /dev/pts/*
                    tty_output = data['content'].strip()
                    assert tty_output.startswith('/dev/'), f"tty 输出应该是 /dev/ 开头的路径，实际: {tty_output}"
                    print(f"✅ 收到有效的 TTY 设备: {tty_output}")

                if data['type'] == 'exit':
                    print("✅ 脚本执行完成")
                    break

            assert tty_output is not None, "未收到 tty 命令的输出"
            print("✅ TTY 命令测试通过")

    except Exception as e:
        pytest.fail(f"TTY 命令测试失败: {e}")


if __name__ == "__main__":
    # 直接运行时的行为（向后兼容）
    print("=" * 60)
    print("🧪 WebSocket脚本执行集成测试")
    print("=" * 60)

    # 直接运行时需要手动启动服务器，这很复杂
    print("⚠️  直接运行此脚本需要手动启动服务器")
    print("建议使用: pytest src/integration_tests/test_websocket_integration.py -v")
    sys.exit(1)