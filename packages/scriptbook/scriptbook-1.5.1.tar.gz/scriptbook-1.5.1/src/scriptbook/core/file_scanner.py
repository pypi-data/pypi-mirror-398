import os
import glob
from datetime import datetime
from typing import List, Dict, Any
import time

class FileScanner:
    """文件扫描器，用于扫描markdown文件"""

    def __init__(self, content_dir: str = "content"):
        self.content_dir = content_dir
        self._cache = None
        self._cache_time = 0
        self._cache_ttl = 10  # 缓存时间（秒）

    def scan_files(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        扫描content目录下的所有markdown文件

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            文件信息列表，每个元素包含name, size, modified
        """
        # 检查缓存
        current_time = time.time()
        if (not force_refresh and self._cache is not None and
            current_time - self._cache_time < self._cache_ttl):
            return self._cache

        files = []
        try:
            # 确保目录存在
            if not os.path.exists(self.content_dir):
                os.makedirs(self.content_dir, exist_ok=True)
                return files

            # 扫描.md文件
            pattern = os.path.join(self.content_dir, "*.md")
            for filepath in glob.glob(pattern):
                try:
                    stat = os.stat(filepath)
                    filename = os.path.basename(filepath)

                    files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime)
                    })
                except Exception as e:
                    print(f"读取文件信息失败 {filepath}: {e}")
                    continue

            # 按文件名排序
            files.sort(key=lambda x: x["name"])

            # 更新缓存和时间戳
            self._cache = files
            self._cache_time = current_time

        except Exception as e:
            print(f"扫描文件失败: {e}")
            return []

        return files

    def get_file_content(self, filename: str) -> str:
        """
        获取指定文件的内容

        Args:
            filename: 文件名

        Returns:
            文件内容

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件名不合法
        """
        # 安全检查
        if not filename.endswith(".md"):
            raise ValueError("文件必须是markdown文件 (.md)")

        # 防止目录遍历攻击
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("文件名不合法")

        filepath = os.path.join(self.content_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filename}")

        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()


# 创建全局文件扫描器实例
file_scanner = FileScanner()