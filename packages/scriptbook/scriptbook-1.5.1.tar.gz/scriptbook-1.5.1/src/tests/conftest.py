import os
import sys
import tempfile
import shutil
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from scriptbook.main import create_app


@pytest.fixture
def temp_content_dir():
    """创建临时内容目录用于测试"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_markdown_file(temp_content_dir):
    """创建示例markdown文件"""
    content = """# 测试文档

这是一个测试Markdown文件。

```bash {"id": "test_script", "title": "测试脚本"}
echo "Hello Test"
ls -la
```

普通文本内容。
"""

    file_path = os.path.join(temp_content_dir, "test.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


@pytest.fixture
def test_client():
    """创建FastAPI测试客户端"""
    app = create_app(Path("content"))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def event_loop():
    """为异步测试提供事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_plugins_dir(temp_content_dir):
    """创建临时插件目录"""
    plugins_dir = os.path.join(temp_content_dir, "plugins")
    os.makedirs(plugins_dir, exist_ok=True)

    # 创建默认插件
    default_plugin_dir = os.path.join(plugins_dir, "default")
    os.makedirs(default_plugin_dir, exist_ok=True)

    manifest = {
        "name": "default",
        "version": "1.0.0",
        "description": "默认主题",
        "type": "theme"
    }

    import json
    manifest_path = os.path.join(default_plugin_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    return plugins_dir