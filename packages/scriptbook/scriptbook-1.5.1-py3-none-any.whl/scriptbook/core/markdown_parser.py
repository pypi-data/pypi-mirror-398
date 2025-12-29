import re
import json
from typing import List, Dict, Any, Tuple
from scriptbook.models.schemas import ScriptBlock

class MarkdownParser:
    """Markdown解析器，支持特殊脚本语法"""

    def __init__(self):
        # 支持可选的缩进（用于列表中的代码块）
        # 使用负向前瞻确保不会匹配到代码内容中的 ```
        # 模式：开头缩进 + ``` + 语言 + 可选元数据 + 换行 + 代码内容(不含```) + 换行 + 缩进 + ```
        self.script_pattern = re.compile(
            r'^[ \t]*```(bash|sh|shell)\s*(\{[^}]*\})?\s*\n((?:(?!```).)*)[ \t]*\n[ \t]*```',
            re.MULTILINE | re.DOTALL
        )

    def extract_scripts(self, markdown_text: str) -> Tuple[str, List[ScriptBlock]]:
        """
        从markdown文本中提取脚本块

        返回:
            - 清理后的markdown文本（脚本块被替换为占位符）
            - 脚本块列表
        """
        scripts = []
        cleaned_text = markdown_text
        offset = 0

        for match in self.script_pattern.finditer(markdown_text):
            language = match.group(1)
            metadata_str = match.group(2)
            code = match.group(3).strip()

            # 处理language为None的情况
            if language is None:
                language = "text"

            script_id = f'script_{len(scripts)}'
            title = f'{language}脚本'  # 默认title

            # 如果有metadata字符串，尝试解析
            if metadata_str and metadata_str.strip():
                try:
                    metadata = json.loads(metadata_str)
                    # 如果解析成功，使用metadata中的值
                    if 'id' in metadata:
                        script_id = metadata['id']
                    if 'title' in metadata:
                        title = metadata['title']
                    else:
                        # 有metadata但没有title，使用智能生成
                        title = self._generate_title(code, language)
                except (json.JSONDecodeError, ValueError):
                    # JSON解析失败，使用默认title
                    pass
            else:
                # 没有metadata，使用智能生成title
                title = self._generate_title(code, language)

            script_block = ScriptBlock(
                id=script_id,
                title=title,
                language=language,
                code=code,
                line_start=match.start() - offset,
                line_end=match.end() - offset
            )
            scripts.append(script_block)

            # 用占位符替换脚本块
            placeholder = f'\n\n[脚本块: {script_id} - {title}]\n\n'
            cleaned_text = (
                cleaned_text[:match.start() - offset] +
                placeholder +
                cleaned_text[match.end() - offset:]
            )
            offset += len(match.group(0)) - len(placeholder)

        return cleaned_text, scripts

    def _generate_title(self, code: str, language: str) -> str:
        """
        从代码中智能生成title
        """
        lines = code.strip().split('\n')
        first_line = lines[0].strip() if lines else ''

        # 尝试从echo命令提取引号内的内容
        echo_match = re.search(r'echo\s+["\']([^"\']+)["\']', first_line, re.IGNORECASE)
        if echo_match:
            return echo_match.group(1)

        # 尝试从printf命令提取引号内的内容
        printf_match = re.search(r'printf\s+["\']([^"\']+)["\']', first_line, re.IGNORECASE)
        if printf_match:
            return printf_match.group(1)

        # 如果是cat命令，尝试获取文件名
        cat_match = re.search(r'cat\s+(\S+)', first_line)
        if cat_match:
            return f"读取文件: {cat_match.group(1)}"

        # 如果是ls命令，生成描述
        if re.match(r'^\s*ls\b', first_line, re.IGNORECASE):
            if '-l' in first_line or '-la' in first_line:
                return "列出文件详情"
            return "列出文件"

        # 如果是cd命令，生成描述
        cd_match = re.search(r'cd\s+(\S+)', first_line)
        if cd_match:
            return f"切换目录: {cd_match.group(1)}"

        # 如果是git命令，生成描述
        git_match = re.search(r'git\s+(\w+)', first_line)
        if git_match:
            git_actions = {
                'clone': '克隆仓库',
                'pull': '更新代码',
                'push': '推送代码',
                'commit': '提交代码',
                'status': '查看状态',
                'checkout': '切换分支',
            }
            action = git_match.group(1)
            return git_actions.get(action, f'Git操作: {action}')

        # 如果第一行不超过30个字符，直接使用
        if len(first_line) <= 30:
            # 清理引号
            first_line = first_line.strip('"').strip("'")
            return first_line

        # 否则取前几个词作为title
        words = first_line.split()[:4]
        return ' '.join(words) + ('...' if len(first_line.split()) > 4 else '')

    def parse(self, markdown_text: str) -> Dict[str, Any]:
        """
        解析markdown文本，返回解析结果

        返回:
            {
                "html": "渲染后的HTML",
                "scripts": [脚本块列表]
            }
        """
        # 提取脚本块
        cleaned_text, scripts = self.extract_scripts(markdown_text)

        # 这里应该使用markdown库渲染cleaned_text
        # 暂时返回原始文本
        html = cleaned_text

        return {
            "html": html,
            "scripts": scripts
        }


# 创建全局解析器实例
parser = MarkdownParser()