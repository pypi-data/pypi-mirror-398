import os
import json
import tempfile
from pathlib import Path
from scriptbook.core.plugin_manager import PluginManager
from scriptbook.models.schemas import PluginInfo


class TestPluginManager:
    """测试插件管理器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_manager = PluginManager(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_plugin(self, plugin_name, manifest_data):
        """创建测试插件"""
        plugin_dir = os.path.join(self.temp_dir, plugin_name)
        os.makedirs(plugin_dir, exist_ok=True)

        manifest_path = os.path.join(plugin_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f)

        return plugin_dir

    def test_initialization(self):
        """测试初始化"""
        assert self.plugin_manager.plugins_dir == self.temp_dir
        assert self.plugin_manager._plugins_cache is None
        assert self.plugin_manager._active_plugins == []

    def test_initialization_with_default_dir(self):
        """测试使用默认目录初始化"""
        manager = PluginManager()
        assert manager.plugins_dir == "app/plugins"

    def test_scan_plugins_empty_directory(self):
        """测试扫描空插件目录"""
        plugins = self.plugin_manager.scan_plugins()
        assert plugins == []
        assert self.plugin_manager._plugins_cache == []

    def test_scan_plugins_directory_creation(self):
        """测试自动创建插件目录"""
        new_dir = os.path.join(self.temp_dir, "nonexistent")
        manager = PluginManager(new_dir)

        plugins = manager.scan_plugins()
        assert plugins == []
        assert os.path.exists(new_dir)

    def test_scan_plugins_valid_plugin(self):
        """测试扫描有效插件"""
        manifest = {
            "name": "test-theme",
            "version": "1.0.0",
            "description": "测试主题",
            "type": "theme",
            "css": "style.css",
            "js": "script.js"
        }
        self.create_test_plugin("test-theme", manifest)

        plugins = self.plugin_manager.scan_plugins()

        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.name == "test-theme"
        assert plugin.version == "1.0.0"
        assert plugin.description == "测试主题"
        assert plugin.type == "theme"
        assert plugin.css == "style.css"
        assert plugin.js == "script.js"
        assert isinstance(plugin, PluginInfo)

    def test_scan_plugins_multiple_plugins(self):
        """测试扫描多个插件"""
        # 创建第一个插件
        manifest1 = {
            "name": "theme1",
            "version": "1.0.0",
            "description": "主题1",
            "type": "theme"
        }
        self.create_test_plugin("theme1", manifest1)

        # 创建第二个插件
        manifest2 = {
            "name": "theme2",
            "version": "2.0.0",
            "description": "主题2",
            "type": "theme",
            "css": "theme2.css"
        }
        self.create_test_plugin("theme2", manifest2)

        # 创建非插件文件（应该被忽略）
        non_plugin_file = os.path.join(self.temp_dir, "not-a-plugin.txt")
        with open(non_plugin_file, "w") as f:
            f.write("Not a plugin")

        plugins = self.plugin_manager.scan_plugins()

        assert len(plugins) == 2
        plugin_names = {p.name for p in plugins}
        assert plugin_names == {"theme1", "theme2"}

    def test_scan_plugins_missing_manifest(self):
        """测试缺少清单文件的插件目录"""
        plugin_dir = os.path.join(self.temp_dir, "no-manifest")
        os.makedirs(plugin_dir, exist_ok=True)

        plugins = self.plugin_manager.scan_plugins()
        assert plugins == []  # 应该被忽略

    def test_scan_plugins_invalid_json(self):
        """测试无效JSON清单文件"""
        plugin_dir = os.path.join(self.temp_dir, "invalid-json")
        os.makedirs(plugin_dir, exist_ok=True)

        manifest_path = os.path.join(plugin_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            f.write("{ invalid json }")

        plugins = self.plugin_manager.scan_plugins()
        assert plugins == []  # 应该被忽略

    def test_scan_plugins_missing_name_field(self):
        """测试缺少name字段的清单"""
        manifest = {
            "version": "1.0.0",
            "description": "无名称插件"
        }
        self.create_test_plugin("plugin-without-name", manifest)

        plugins = self.plugin_manager.scan_plugins()

        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.name == "plugin-without-name"  # 应该使用目录名

    def test_scan_plugins_default_values(self):
        """测试默认值"""
        manifest = {
            "name": "minimal-plugin"
        }
        self.create_test_plugin("minimal", manifest)

        plugins = self.plugin_manager.scan_plugins()

        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.name == "minimal-plugin"
        assert plugin.version == "1.0.0"  # 默认值
        assert plugin.description == ""  # 默认值
        assert plugin.type == "theme"  # 默认值
        assert plugin.css is None
        assert plugin.js is None

    def test_scan_plugins_cache(self):
        """测试缓存功能"""
        manifest = {"name": "test"}
        self.create_test_plugin("test", manifest)

        # 第一次扫描
        plugins1 = self.plugin_manager.scan_plugins()
        cache1 = self.plugin_manager._plugins_cache

        # 第二次扫描，应该使用缓存
        plugins2 = self.plugin_manager.scan_plugins()
        cache2 = self.plugin_manager._plugins_cache

        assert plugins1 == plugins2
        assert cache1 == cache2
        assert plugins1 is not cache1  # 应该是副本
        assert plugins2 is not cache2

    def test_get_plugin_existing(self):
        """测试获取存在的插件"""
        manifest = {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "测试插件"
        }
        self.create_test_plugin("test", manifest)

        plugin = self.plugin_manager.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.name == "test-plugin"
        assert plugin.version == "1.0.0"

    def test_get_plugin_nonexistent(self):
        """测试获取不存在的插件"""
        plugin = self.plugin_manager.get_plugin("nonexistent")
        assert plugin is None

    def test_activate_plugin_success(self):
        """测试成功激活插件"""
        manifest = {"name": "test-plugin"}
        self.create_test_plugin("test", manifest)

        result = self.plugin_manager.activate_plugin("test-plugin")
        assert result is True
        assert "test-plugin" in self.plugin_manager._active_plugins

    def test_activate_plugin_nonexistent(self):
        """测试激活不存在的插件"""
        result = self.plugin_manager.activate_plugin("nonexistent")
        assert result is False
        assert "nonexistent" not in self.plugin_manager._active_plugins

    def test_activate_plugin_duplicate(self):
        """测试重复激活插件"""
        manifest = {"name": "test-plugin"}
        self.create_test_plugin("test", manifest)

        # 第一次激活
        result1 = self.plugin_manager.activate_plugin("test-plugin")
        assert result1 is True
        assert self.plugin_manager._active_plugins.count("test-plugin") == 1

        # 第二次激活（重复）
        result2 = self.plugin_manager.activate_plugin("test-plugin")
        assert result2 is True  # 仍然返回True
        assert self.plugin_manager._active_plugins.count("test-plugin") == 1  # 不应该重复添加

    def test_deactivate_plugin_success(self):
        """测试成功停用插件"""
        manifest = {"name": "test-plugin"}
        self.create_test_plugin("test", manifest)

        # 先激活
        self.plugin_manager.activate_plugin("test-plugin")
        assert "test-plugin" in self.plugin_manager._active_plugins

        # 停用
        result = self.plugin_manager.deactivate_plugin("test-plugin")
        assert result is True
        assert "test-plugin" not in self.plugin_manager._active_plugins

    def test_deactivate_plugin_not_active(self):
        """测试停用未激活的插件"""
        result = self.plugin_manager.deactivate_plugin("nonexistent")
        assert result is False

    def test_get_active_plugins(self):
        """测试获取激活插件列表"""
        # 添加一些插件
        manifests = [
            {"name": "plugin1"},
            {"name": "plugin2"},
            {"name": "plugin3"}
        ]

        for i, manifest in enumerate(manifests, 1):
            self.create_test_plugin(f"plugin{i}", manifest)
            self.plugin_manager.activate_plugin(f"plugin{i}")

        active_plugins = self.plugin_manager.get_active_plugins()

        assert len(active_plugins) == 3
        assert "plugin1" in active_plugins
        assert "plugin2" in active_plugins
        assert "plugin3" in active_plugins
        assert active_plugins == ["plugin1", "plugin2", "plugin3"]

        # 返回的应该是副本
        active_plugins.append("plugin4")
        assert "plugin4" not in self.plugin_manager._active_plugins

    def test_get_active_plugins_info(self):
        """测试获取激活插件的详细信息"""
        manifests = [
            {"name": "theme1", "description": "主题1"},
            {"name": "theme2", "description": "主题2"}
        ]

        for i, manifest in enumerate(manifests, 1):
            self.create_test_plugin(f"theme{i}", manifest)
            self.plugin_manager.activate_plugin(f"theme{i}")

        active_plugins_info = self.plugin_manager.get_active_plugins_info()

        assert len(active_plugins_info) == 2
        for plugin_info in active_plugins_info:
            assert isinstance(plugin_info, PluginInfo)
            assert plugin_info.name.startswith("theme")
            assert "主题" in plugin_info.description

    def test_get_active_plugins_info_with_inactive(self):
        """测试获取包含未激活插件的详细信息"""
        manifest = {"name": "inactive-plugin"}
        self.create_test_plugin("inactive", manifest)

        # 不激活插件
        active_plugins_info = self.plugin_manager.get_active_plugins_info()
        assert active_plugins_info == []

    def test_plugin_lifecycle(self):
        """测试插件完整生命周期"""
        manifest = {"name": "lifecycle-plugin"}
        self.create_test_plugin("lifecycle", manifest)

        # 1. 扫描插件
        plugins = self.plugin_manager.scan_plugins()
        assert len(plugins) == 1

        # 2. 获取插件信息
        plugin = self.plugin_manager.get_plugin("lifecycle-plugin")
        assert plugin is not None

        # 3. 激活插件
        activate_result = self.plugin_manager.activate_plugin("lifecycle-plugin")
        assert activate_result is True
        assert "lifecycle-plugin" in self.plugin_manager.get_active_plugins()

        # 4. 获取激活插件信息
        active_info = self.plugin_manager.get_active_plugins_info()
        assert len(active_info) == 1
        assert active_info[0].name == "lifecycle-plugin"

        # 5. 停用插件
        deactivate_result = self.plugin_manager.deactivate_plugin("lifecycle-plugin")
        assert deactivate_result is True
        assert "lifecycle-plugin" not in self.plugin_manager.get_active_plugins()

        # 6. 插件信息仍然可以获取
        plugin_after = self.plugin_manager.get_plugin("lifecycle-plugin")
        assert plugin_after is not None

    def test_plugin_with_css_and_js(self):
        """测试包含CSS和JS资源的插件"""
        manifest = {
            "name": "resourceful-plugin",
            "css": "styles/main.css",
            "js": "scripts/main.js"
        }
        self.create_test_plugin("resourceful", manifest)

        plugin = self.plugin_manager.get_plugin("resourceful-plugin")
        assert plugin.css == "styles/main.css"
        assert plugin.js == "scripts/main.js"

    def test_directory_with_non_directory_items(self):
        """测试包含非目录项的插件目录"""
        # 创建有效插件
        manifest = {"name": "valid-plugin"}
        self.create_test_plugin("valid", manifest)

        # 创建文件（不是目录）
        file_path = os.path.join(self.temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("I'm a file, not a plugin")

        # 创建符号链接（如果需要可以跳过）

        plugins = self.plugin_manager.scan_plugins()
        assert len(plugins) == 1  # 只应该找到有效插件
        assert plugins[0].name == "valid-plugin"