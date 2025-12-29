import os
import tempfile
import time
from datetime import datetime
from scriptbook.core.file_scanner import FileScanner


class TestFileScanner:
    """测试文件扫描器"""

    def test_initialization(self):
        """测试初始化"""
        scanner = FileScanner()
        assert scanner.content_dir == "content"
        assert scanner._cache is None
        assert scanner._cache_time == 0
        assert scanner._cache_ttl == 10

    def test_initialization_with_custom_dir(self):
        """测试使用自定义目录初始化"""
        scanner = FileScanner("custom_dir")
        assert scanner.content_dir == "custom_dir"

    def test_scan_files_empty_directory(self, temp_content_dir):
        """测试扫描空目录"""
        scanner = FileScanner(temp_content_dir)
        files = scanner.scan_files()
        assert files == []
        assert scanner._cache == []

    def test_scan_files_with_markdown_files(self, temp_content_dir):
        """测试扫描包含markdown文件的目录"""
        # 创建测试文件
        test_file1 = os.path.join(temp_content_dir, "test1.md")
        test_file2 = os.path.join(temp_content_dir, "test2.md")
        non_md_file = os.path.join(temp_content_dir, "test.txt")

        with open(test_file1, "w") as f:
            f.write("# Test 1")
        with open(test_file2, "w") as f:
            f.write("# Test 2")
        with open(non_md_file, "w") as f:
            f.write("Not markdown")

        scanner = FileScanner(temp_content_dir)
        files = scanner.scan_files()

        assert len(files) == 2
        file_names = {f["name"] for f in files}
        assert file_names == {"test1.md", "test2.md"}

        # 检查文件信息
        for file_info in files:
            assert "name" in file_info
            assert "size" in file_info
            assert "modified" in file_info
            assert isinstance(file_info["modified"], datetime)
            assert file_info["size"] > 0

    def test_scan_files_cache(self, temp_content_dir):
        """测试缓存功能"""
        scanner = FileScanner(temp_content_dir)

        # 第一次扫描
        files1 = scanner.scan_files()
        cache_time1 = scanner._cache_time

        # 立即再次扫描，应该使用缓存
        files2 = scanner.scan_files()
        cache_time2 = scanner._cache_time

        assert files1 == files2
        assert cache_time1 == cache_time2  # 缓存时间不变

    def test_scan_files_force_refresh(self, temp_content_dir):
        """测试强制刷新缓存"""
        scanner = FileScanner(temp_content_dir)

        # 第一次扫描
        scanner.scan_files()
        cache_time1 = scanner._cache_time

        # 强制刷新
        time.sleep(0.1)  # 确保时间不同
        scanner.scan_files(force_refresh=True)
        cache_time2 = scanner._cache_time

        assert cache_time2 > cache_time1

    def test_scan_files_cache_expiry(self, temp_content_dir):
        """测试缓存过期"""
        scanner = FileScanner(temp_content_dir)
        scanner._cache_ttl = 0.1  # 设置很短的TTL

        # 第一次扫描
        scanner.scan_files()
        cache_time1 = scanner._cache_time

        # 等待缓存过期
        time.sleep(0.2)

        # 再次扫描，应该刷新缓存
        scanner.scan_files()
        cache_time2 = scanner._cache_time

        assert cache_time2 > cache_time1

    def test_get_file_content_success(self, sample_markdown_file):
        """测试成功获取文件内容"""
        temp_dir = os.path.dirname(sample_markdown_file)
        scanner = FileScanner(temp_dir)

        content = scanner.get_file_content("test.md")
        assert content.startswith("# 测试文档")
        assert "Hello Test" in content

    def test_get_file_content_file_not_found(self, temp_content_dir):
        """测试获取不存在的文件"""
        scanner = FileScanner(temp_content_dir)

        try:
            scanner.get_file_content("nonexistent.md")
            assert False, "应该抛出FileNotFoundError"
        except FileNotFoundError as e:
            assert "nonexistent.md" in str(e)

    def test_get_file_content_invalid_extension(self, temp_content_dir):
        """测试获取非markdown文件"""
        scanner = FileScanner(temp_content_dir)

        try:
            scanner.get_file_content("test.txt")
            assert False, "应该抛出ValueError"
        except ValueError as e:
            assert "markdown文件" in str(e)

    def test_get_file_content_path_traversal(self, temp_content_dir):
        """测试路径遍历攻击防护"""
        scanner = FileScanner(temp_content_dir)

        test_cases = [
            "../test.md",
            "../../test.md",
            "test/../test.md",
            "test\\..\\test.md",
        ]

        for filename in test_cases:
            try:
                scanner.get_file_content(filename)
                assert False, f"应该拒绝文件名: {filename}"
            except ValueError as e:
                assert "文件名不合法" in str(e)

    def test_directory_creation(self):
        """测试自动创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "nonexistent")
            scanner = FileScanner(new_dir)

            # 扫描时应该自动创建目录
            files = scanner.scan_files()
            assert files == []
            assert os.path.exists(new_dir)

    def test_file_sorting(self, temp_content_dir):
        """测试文件按名称排序"""
        # 创建无序文件
        files_to_create = ["zebra.md", "apple.md", "banana.md"]
        for filename in files_to_create:
            filepath = os.path.join(temp_content_dir, filename)
            with open(filepath, "w") as f:
                f.write("# " + filename)

        scanner = FileScanner(temp_content_dir)
        files = scanner.scan_files()

        assert len(files) == 3
        assert files[0]["name"] == "apple.md"
        assert files[1]["name"] == "banana.md"
        assert files[2]["name"] == "zebra.md"