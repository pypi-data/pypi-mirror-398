"""
Scriptbook 功能测试 (pytest版本)

启动真实的服务器进行端到端测试，自动管理服务生命周期

依赖:
- pytest
- requests

运行:
    pytest src/integration_tests/test_scriptbook_pytest.py -v
"""
import subprocess
import sys
import requests
import pytest

# 尝试导入requests，如果失败则跳过测试
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    pytest.skip("requests模块未安装，跳过功能测试", allow_module_level=True)


class TestScriptbook:
    """Scriptbook 功能测试"""

    def test_cli_help(self):
        """测试CLI帮助命令"""
        result = subprocess.run(
            ["scriptbook", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "Scriptbook" in result.stdout

    def test_cli_version(self):
        """测试CLI版本显示"""
        result = subprocess.run(
            ["scriptbook", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "scriptbook" in result.stdout or "1.0.0" in result.stdout

    def test_health_check(self, test_server):
        """测试健康检查端点"""
        response = requests.get(f"{test_server.base_url}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "scriptbook"

    def test_markdown_files_api(self, test_server):
        """测试Markdown文件获取API"""
        response = requests.get(f"{test_server.base_url}/api/markdown/files")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "files" in data
        assert isinstance(data["files"], list)
        assert len(data["files"]) > 0
        print(f"  ✅ 发现 {len(data['files'])} 个Markdown文件")

    def test_markdown_render_api(self, test_server):
        """测试Markdown渲染API"""
        # 先获取文件列表
        files_response = requests.get(f"{test_server.base_url}/api/markdown/files")
        assert files_response.status_code == 200

        data = files_response.json()
        if not data.get("files"):
            pytest.skip("没有找到Markdown文件")

        # 选择第一个文件进行渲染测试
        test_file = data["files"][0]["name"]
        render_response = requests.get(
            f"{test_server.base_url}/api/markdown/render",
            params={"file": test_file}
        )
        assert render_response.status_code == 200

        render_data = render_response.json()
        assert "html" in render_data
        assert "scripts" in render_data
        assert isinstance(render_data["scripts"], list)

        print(f"  ✅ 渲染成功，脚本数量: {len(render_data['scripts'])}")

    def test_plugins_api(self, test_server):
        """测试插件API"""
        response = requests.get(f"{test_server.base_url}/api/plugins")

        if response.status_code != 200:
            print(f"  ❌ 错误状态码: {response.status_code}")
            print(f"  ❌ 错误响应: {response.text}")

        assert response.status_code == 200

        plugins = response.json()
        assert isinstance(plugins, list)
        assert len(plugins) > 0
        print(f"  ✅ 发现 {len(plugins)} 个插件")

    def test_root_page(self, test_server):
        """测试根页面"""
        response = requests.get(test_server.base_url)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

        content = response.text
        assert "Scriptbook" in content
        assert "<html" in content.lower()

    def test_static_files(self, test_server):
        """测试静态文件服务"""
        # 测试CSS文件
        css_response = requests.get(f"{test_server.base_url}/static/css/main.css")
        assert css_response.status_code == 200
        assert css_response.headers["content-type"].startswith("text/css")

        # 测试JS文件
        js_response = requests.get(f"{test_server.base_url}/static/js/app.js")
        assert js_response.status_code == 200
        assert "javascript" in js_response.headers["content-type"]

        print(f"  ✅ 静态文件服务正常")


if __name__ == "__main__":
    # 直接运行时的行为
    pytest.main([__file__, "-v"])
