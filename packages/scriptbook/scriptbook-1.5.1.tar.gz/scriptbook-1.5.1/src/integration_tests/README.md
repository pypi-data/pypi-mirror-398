# 集成测试

此目录包含Scriptbook的集成测试，用于验证整个系统的端到端功能。

## 测试文件

- `test_routers.py` - 路由器和API端点的集成测试（使用TestClient，无需真实服务器）
- `test_scriptbook_pytest.py` - pytest功能测试，自动启动真实服务器进行端到端测试
- `conftest.py` - 公共测试配置和fixture，包含TestServer类管理服务器生命周期

## ⚠️ 兼容性说明

当前集成测试存在starlette版本兼容性问题，可能导致失败。这些失败不影响实际功能使用。

### 问题详情

- **测试文件**: `test_routers.py`
- **错误类型**: `TypeError: Client.__init__() got an unexpected keyword argument 'app'`
- **原因**: starlette 0.27.0与httpx 0.28.1之间的兼容性问题
- **状态**: 已知问题，需要升级starlette或降级httpx解决

### 解决方案

1. **升级starlette**:
   ```bash
   pip install --upgrade starlette
   ```

2. **降级httpx**:
   ```bash
   pip install "httpx<0.28"
   ```

## 运行集成测试

```bash
# 运行所有集成测试
pytest integration_tests/ -v

# 运行特定测试
pytest integration_tests/test_routers.py::TestMarkdownRouter -v

# 忽略兼容性警告
pytest integration_tests/ -v --disable-warnings
```

## 功能测试

运行pytest功能测试（自动启动真实服务器进行端到端测试）：

```bash
# 运行所有功能测试
pytest integration_tests/test_scriptbook_pytest.py -v

# 运行特定测试
pytest integration_tests/test_scriptbook_pytest.py::TestScriptbook::test_health_check -v

# 启用详细输出
pytest integration_tests/test_scriptbook_pytest.py -v -s
```

### pytest版本功能测试的特点

- ✅ **自动管理服务生命周期** - 测试启动前自动启动服务器，测试结束后自动关闭
- ✅ **真正的端到端测试** - 使用真实服务器而非模拟
- ✅ **更好的集成** - 与pytest生态系统完全集成
- ✅ **会话级fixture** - 服务器在整个测试会话中只启动一次，提高测试效率
- ✅ **清晰的断言** - 使用pytest的断言机制，提供更好的错误信息

**注意**: pytest版本需要安装requests库 (`pip install requests`)

## 公共服务器管理

`conftest.py` 提供了 `TestServer` 类和 `test_server` fixture，统一管理服务器生命周期：

```python
@pytest.fixture(scope="session")
def test_server():
    """会话级fixture，管理测试服务器生命周期（端口8015）"""
    server = TestServer("content", port=8015)
    # 自动启动服务器
    yield server
    # 自动关闭服务器
    server.stop()
```

### 可用的fixture

- `test_server` - 主测试服务器（端口8015）
- `test_server_8016` - 独立测试服务器（端口8016）

### 运行所有集成测试

```bash
# 运行所有集成测试
pytest integration_tests/ -v

# 只运行pytest功能测试
pytest integration_tests/test_scriptbook_pytest.py -v

# 只运行路由集成测试
pytest integration_tests/test_routers.py -v
```

## 测试分类

- **单元测试** (`src/tests/`): 测试核心业务逻辑，所有测试通过
- **集成测试** (`src/integration_tests/`): 测试API端点，部分测试因依赖版本问题失败
- **功能测试** (`src/integration_tests/test_scriptbook_pytest.py`): 使用pytest自动启动真实服务器进行端到端测试

## 建议

1. **开发时**: 使用核心单元测试验证逻辑 (`pytest src/tests/`)
2. **部署前**: 使用pytest功能测试验证系统 (`pytest src/integration_tests/test_scriptbook_pytest.py -v`)
3. **问题调试**: 需要时解决集成测试的依赖问题

## 参考

- [pytest文档](https://docs.pytest.org/)
- [starlette文档](https://www.starlette.io/)
- [FastAPI测试指南](https://fastapi.tiangolo.com/tutorial/testing/)
