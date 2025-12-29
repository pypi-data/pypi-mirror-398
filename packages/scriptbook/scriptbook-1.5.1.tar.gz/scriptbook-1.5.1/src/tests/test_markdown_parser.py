import json
from scriptbook.core.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """测试Markdown解析器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.parser = MarkdownParser()

    def test_initialization(self):
        """测试初始化"""
        assert self.parser.script_pattern is not None

    def test_extract_scripts_empty(self):
        """测试提取空文本中的脚本块"""
        text = "没有脚本的普通文本。"
        cleaned, scripts = self.parser.extract_scripts(text)

        assert cleaned == text
        assert scripts == []

    def test_extract_scripts_single_script(self):
        """测试提取单个脚本块"""
        text = """# 文档标题

一些文本。

```bash {"id": "test1", "title": "测试脚本"}
echo "Hello"
ls -la
```

更多文本。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        # 检查清理后的文本
        assert "[脚本块: test1 - 测试脚本]" in cleaned
        assert "```bash" not in cleaned

        # 检查脚本块
        assert len(scripts) == 1
        script = scripts[0]
        assert script.id == "test1"
        assert script.title == "测试脚本"
        assert script.language == "bash"
        assert script.code == 'echo "Hello"\nls -la'
        assert script.line_start >= 0
        assert script.line_end > script.line_start

    def test_extract_scripts_multiple_scripts(self):
        """测试提取多个脚本块"""
        text = """# 文档

```bash {"id": "bash1", "title": "Bash脚本1"}
echo "Hello"
```

中间文本。

```bash {"id": "bash2", "title": "Bash脚本2"}
echo "World"
```

结尾。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        # 检查清理后的文本
        assert "[脚本块: bash1 - Bash脚本1]" in cleaned
        assert "[脚本块: bash2 - Bash脚本2]" in cleaned
        assert "```bash" not in cleaned

        # 检查脚本块
        assert len(scripts) == 2

        bash_script1 = scripts[0]
        assert bash_script1.id == "bash1"
        assert bash_script1.title == "Bash脚本1"
        assert bash_script1.language == "bash"
        assert bash_script1.code == 'echo "Hello"'

        bash_script2 = scripts[1]
        assert bash_script2.id == "bash2"
        assert bash_script2.title == "Bash脚本2"
        assert bash_script2.language == "bash"
        assert bash_script2.code == 'echo "World"'

    def test_extract_scripts_no_metadata(self):
        """测试没有元数据的脚本块（智能生成title）"""
        text = """# 文档

```bash
echo "Default"
```

结束。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        # 检查清理后的文本
        assert "[脚本块: script_0 - Default]" in cleaned

        # 检查脚本块
        assert len(scripts) == 1
        script = scripts[0]
        assert script.id == "script_0"  # 自动生成的ID
        assert script.title == "Default"  # 智能生成的标题（从echo中提取）
        assert script.language == "bash"
        assert script.code == 'echo "Default"'

    def test_extract_scripts_invalid_json_metadata(self):
        """测试无效JSON元数据"""
        text = """# 文档

```bash {"id": test1, title: "测试"}
echo "Hello"
```

结束。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        # 应该使用默认值
        assert len(scripts) == 1
        script = scripts[0]
        assert script.id == "script_0"  # 自动生成的ID
        assert script.title == "bash脚本"  # 默认标题

    def test_extract_scripts_partial_metadata(self):
        """测试部分元数据（只有id，没有title）"""
        text = """# 文档

```bash {"id": "custom_id"}
echo "Partial metadata"
```

结束。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        script = scripts[0]
        assert script.id == "custom_id"  # 自定义ID
        assert script.title == "Partial metadata"  # 智能生成的标题
        assert script.code == 'echo "Partial metadata"'

    def test_extract_scripts_with_code_containing_backticks(self):
        """测试代码中包含反引号的脚本块"""
        text = r"""# 文档

```bash {"id": "test1", "title": "包含反引号"}
echo "This contains \`backticks\`"
echo 'And \`more\` backticks'
```

结束。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        script = scripts[0]
        assert r"contains \`backticks\`" in script.code
        assert r"And \`more\` backticks" in script.code

    def test_extract_scripts_multiline_code(self):
        """测试多行代码的脚本块"""
        text = """# 文档

```bash {"id": "multiline", "title": "多行脚本"}
echo "Line 1"
echo "Line 2"
echo "Line 3"

if [ true ]; then
    echo "Conditional"
fi
```

结束。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        script = scripts[0]
        lines = script.code.split('\n')
        assert len(lines) >= 7
        assert "Line 1" in script.code
        assert "Conditional" in script.code

    def test_extract_scripts_preserves_original_text_structure(self):
        """测试保持原始文本结构"""
        text = """第一段。

```bash {"id": "s1", "title": "脚本1"}
echo "Script 1"
```

第二段。

```bash {"id": "s2", "title": "脚本2"}
echo "Script 2"
```

第三段。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        # 检查段落顺序
        parts = cleaned.split('[脚本块:')
        assert len(parts) == 3  # 两个脚本块占位符 + 最后一部分
        assert "第一段" in parts[0]
        assert "第二段" in parts[1]
        assert "第三段" in parts[2]

    def test_parse_method(self):
        """测试parse方法"""
        text = """# 标题

```bash {"id": "test", "title": "测试"}
echo "Hello"
```

文本。"""

        result = self.parser.parse(text)

        assert "html" in result
        assert "scripts" in result
        assert len(result["scripts"]) == 1
        assert result["scripts"][0].id == "test"

        # 由于没有实际渲染Markdown，html应该包含清理后的文本
        assert "[脚本块: test - 测试]" in result["html"]

    def test_script_pattern_matching(self):
        """测试正则表达式匹配"""
        test_cases = [
            # 标准格式
            ('```bash {"id": "test", "title": "测试"}\necho "Hello"\n```', True),
            # 没有元数据
            ('```bash\necho "Hello"\n```', True),
            # sh和shell也应该匹配
            ('```sh\necho "Hello"\n```', True),
            ('```shell\necho "Hello"\n```', True),
            # 不同语言 - 不应该匹配
            ('```python\nprint("Hi")\n```', False),
            ('```javascript\nconsole.log("Hi")\n```', False),
            # 无效格式
            ('```\necho "Hello"\n```', False),  # 没有语言，不应该匹配
            ('echo "Hello"', False),  # 没有代码块标记
            ('``bash\necho "Hello"\n``', False),  # 只有两个反引号
        ]

        for text, should_match in test_cases:
            match = self.parser.script_pattern.search(text)
            if should_match:
                assert match is not None, f"应该匹配: {text}"
            else:
                assert match is None, f"不应该匹配: {text}"

    def test_extract_scripts_with_whitespace_variations(self):
        """测试不同空白字符格式"""
        variations = [
            # 标准格式
            ('```bash {"id": "test1", "title": "测试"}\necho "Hello"\n```', 'test1'),
            # 额外空白（闭合```前有空格）
            ('```bash {"id": "test2", "title": "测试"}\necho "Hello"  \n```', 'test2'),
            # 简单格式（无metadata，使用默认id）
            ('```bash\necho "Hello"\n```', 'script_0'),
        ]

        for text, expected_id in variations:
            cleaned, scripts = self.parser.extract_scripts(text)
            assert len(scripts) == 1, f"应该提取一个脚本: {text[:50]}..."
            script = scripts[0]
            assert script.id == expected_id, f"期望 {expected_id}, 得到 {script.id}"
            assert "Hello" in script.code

    def test_extract_scripts_position_order(self):
        """测试脚本块位置信息按出现顺序排列"""
        text = """# 文档

这是第一段。

```bash {"id": "first", "title": "第一个脚本"}
echo "First"
```

这是第二段。

```bash {"id": "second", "title": "第二个脚本"}
echo "Second"
```

这是第三段。

```bash {"id": "third", "title": "第三个脚本"}
echo "Third"
```

结束。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        # 应该有3个脚本块
        assert len(scripts) == 3

        # 验证位置顺序（按出现顺序）
        assert scripts[0].id == "first"
        assert scripts[1].id == "second"
        assert scripts[2].id == "third"

        # 验证 line_start 递增
        assert scripts[0].line_start < scripts[1].line_start < scripts[2].line_start

        # 验证 line_end > line_start
        assert all(s.line_end > s.line_start for s in scripts)

        # 验证清理后的文本保持正确顺序
        assert "[脚本块: first - 第一个脚本]" in cleaned
        assert "[脚本块: second - 第二个脚本]" in cleaned
        assert "[脚本块: third - 第三个脚本]" in cleaned

        # 验证原始文本中的位置关系
        first_pos = cleaned.find("[脚本块: first")
        second_pos = cleaned.find("[脚本块: second")
        third_pos = cleaned.find("[脚本块: third")
        assert first_pos < second_pos < third_pos, "脚本块应该按原始顺序排列"

    def test_extract_scripts_line_start_matches_position(self):
        """测试 line_start 正确反映脚本块在原始文本中的位置"""
        text = """# 标题

一些介绍文本。

```bash {"id": "test", "title": "测试"}
echo "Hello"
```

结束文本。"""

        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        script = scripts[0]

        # line_start 应该等于脚本块在原始文本中的起始位置
        # 使用正则查找验证
        import re
        match = re.search(r'```bash', text)
        assert match is not None
        assert script.line_start == match.start()

    def test_router_extract_script_blocks_position(self):
        """测试路由层 extract_script_blocks 使用正确的位置信息"""
        from scriptbook.routers.markdown import extract_script_blocks

        text = """# 文档

开头文本。

```bash {"id": "script1", "title": "脚本1"}
echo "First"
```

中间文本。

```bash {"id": "script2", "title": "脚本2"}
echo "Second"
```

结尾文本。"""

        scripts = extract_script_blocks(text)

        # 应该有2个脚本块
        assert len(scripts) == 2

        # 验证位置信息正确传递
        assert scripts[0]['id'] == "script1"
        assert scripts[1]['id'] == "script2"

        # 第一个脚本的位置应该在第二个之前
        assert scripts[0]['start'] < scripts[1]['start']

        # 位置不应该都是0
        assert scripts[0]['start'] > 0, "start 不应该为0"
        assert scripts[0]['end'] > 0, "end 不应该为0"

    def test_embed_scripts_no_residue(self):
        """测试 embed_scripts_in_markdown 不会残留 markdown 代码块"""
        from scriptbook.routers.markdown import embed_scripts_in_markdown, extract_script_blocks

        text = """# 文档

这是第一段。

```bash {"id": "script1", "title": "脚本1"}
echo "First"
```

这是第二段。

```bash {"id": "script2", "title": "脚本2"}
echo "Second"
```

这是第三段。

```bash {"id": "script3", "title": "脚本3"}
echo "Third"
```

结束。"""

        # 提取脚本块
        scripts = extract_script_blocks(text)

        # 应该有3个脚本块
        assert len(scripts) == 3

        # 嵌入脚本块
        result = embed_scripts_in_markdown(text, scripts)

        # 验证没有残留的 ```bash 代码块
        assert '```bash' not in result, "不应该有残留的 ```bash 代码块"

        # 验证占位符已被替换
        assert '[[SCRIPT_BLOCK_' not in result, "占位符应该被替换"

        # 验证脚本块 HTML 存在
        assert '<div class="script-block"' in result, "应该包含脚本块 HTML"

        # 验证脚本块按正确顺序出现
        script1_pos = result.find('data-script-id="script1"')
        script2_pos = result.find('data-script-id="script2"')
        script3_pos = result.find('data-script-id="script3"')
        assert script1_pos < script2_pos < script3_pos, "脚本块应该按原始顺序排列"

    def test_embed_scripts_preserves_markdown_content(self):
        """测试 embed_scripts_in_markdown 保留非脚本块内容"""
        from scriptbook.routers.markdown import embed_scripts_in_markdown, extract_script_blocks

        text = """# 标题

这是一个测试文档。

```bash
echo "test"
```

文档结束。"""

        scripts = extract_script_blocks(text)
        result = embed_scripts_in_markdown(text, scripts)

        # 验证 markdown 内容被保留（渲染后）
        assert '<h1' in result or '标题' in result, "应该保留标题"
        assert '这是一个测试文档' in result, "应该保留正文"
        assert '文档结束' in result, "应该保留结尾"

        # 验证脚本块被正确嵌入
        assert '<div class="script-block"' in result

    def test_embed_scripts_with_example_file(self):
        """测试使用 example.md 文件进行完整的嵌入流程"""
        from scriptbook.routers.markdown import embed_scripts_in_markdown, extract_script_blocks
        from pathlib import Path

        example_file = Path('/Users/lzy/Desktop/PROJECTS/web/content/example.md')
        if not example_file.exists():
            # 如果文件不存在，跳过测试
            return

        with open(example_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取脚本块
        scripts = extract_script_blocks(content)

        # example.md 应该有 7 个脚本块
        assert len(scripts) == 7, f"example.md 应该有 7 个脚本块，实际 {len(scripts)} 个"

        # 嵌入脚本块
        result = embed_scripts_in_markdown(content, scripts)

        # 验证没有残留的 markdown 代码块
        assert '```bash' not in result, "example.md 渲染后不应该有残留的 ```bash"

        # 验证所有脚本块都被嵌入
        for i in range(7):
            assert f'data-script-id="script_{i}"' in result, f"脚本块 script_{i} 应该存在"

        # 验证 markdown 标题被保留
        assert 'Markdown脚本执行示例' in result
        assert '基本命令' in result
        assert '系统信息' in result
        assert '网络检查' in result
        assert '文件操作' in result
        assert '结束' in result

    def test_extract_scripts_indented_code_blocks(self):
        """测试提取列表中的缩进代码块"""
        text = """## 6.2 列表中的脚本

- 第一步：检查系统

  ```bash {"title": "列表中的脚本1"}
  uname -a
  ```

- 第二步：检查网络

  ```bash {"title": "列表中的脚本2"}
  ping -c 1 127.0.0.1
  ```

- 第三步：检查用户

  ```bash {"title": "列表中的脚本3"}
  whoami
  ```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        # 应该提取3个脚本块
        assert len(scripts) == 3, f"期望3个脚本块，实际{len(scripts)}个"

        # 验证第一个脚本
        assert scripts[0].title == "列表中的脚本1"
        assert scripts[0].language == "bash"
        assert "uname -a" in scripts[0].code

        # 验证第二个脚本
        assert scripts[1].title == "列表中的脚本2"
        assert scripts[1].language == "bash"
        assert "ping -c 1 127.0.0.1" in scripts[1].code

        # 验证第三个脚本
        assert scripts[2].title == "列表中的脚本3"
        assert scripts[2].language == "bash"
        assert "whoami" in scripts[2].code

        # 验证清理后的文本不包含原始代码块
        assert "```bash" not in cleaned

    def test_extract_scripts_empty_code_block(self):
        """测试提取空代码块"""
        text = """```bash {"title": "空代码块测试"}

```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        assert scripts[0].title == "空代码块测试"
        assert scripts[0].code == ""

    def test_extract_scripts_consecutive_blocks(self):
        """测试连续多个代码块（中间无空行）"""
        text = """```bash {"title": "脚本1"}
echo "1"
```
```bash {"title": "脚本2"}
echo "2"
```
```bash {"title": "脚本3"}
echo "3"
```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 3
        assert scripts[0].title == "脚本1"
        assert scripts[0].code == 'echo "1"'
        assert scripts[1].title == "脚本2"
        assert scripts[1].code == 'echo "2"'
        assert scripts[2].title == "脚本3"
        assert scripts[2].code == 'echo "3"'

    def test_extract_scripts_with_backticks_in_code(self):
        """测试代码中包含反引号的脚本块"""
        text = r"""```bash {"title": "包含反引号"}
echo "Test \`with backticks\`"
echo 'Another `test`'
```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        assert scripts[0].title == "包含反引号"
        # 代码应该包含反引号
        assert '`' in scripts[0].code or '\\`' in scripts[0].code

    def test_extract_scripts_nested_indentation(self):
        """测试多级缩进（嵌套列表中的代码块）"""
        text = """- 一级列表

  - 二级列表

    ```bash {"title": "深层缩进脚本"}
    echo "deep"
    ```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        assert scripts[0].title == "深层缩进脚本"
        assert "echo" in scripts[0].code
        assert "deep" in scripts[0].code

    def test_extract_scripts_with_code_containing_triple_backticks(self):
        """测试代码中包含三个反引号的脚本（edge case）"""
        text = r"""```bash {"title": "包含三个反引号"}
echo "Here is a code example:"
echo "\`\`\`"
echo "End of example"
```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 1
        assert scripts[0].title == "包含三个反引号"
        # 应该能正确处理包含 ``` 的代码
        assert "echo" in scripts[0].code

    def test_extract_scripts_tabs_and_spaces_indentation(self):
        """测试混合缩进（制表符和空格）"""
        text = """- 使用空格缩进

  ```bash {"title": "空格缩进"}
  echo "space indented"
  ```

- 使用制表符缩进

	```bash {"title": "制表符缩进"}
	echo "tab indented"
	```
"""
        cleaned, scripts = self.parser.extract_scripts(text)

        assert len(scripts) == 2
        assert scripts[0].title == "空格缩进"
        assert "space indented" in scripts[0].code
        assert scripts[1].title == "制表符缩进"
        assert "tab indented" in scripts[1].code

    def test_router_extract_script_blocks_with_indentation(self):
        """测试路由层的 extract_script_blocks 支持缩进代码块"""
        from scriptbook.routers.markdown import extract_script_blocks

        text = """### 6.2 列表中的脚本

- 第一步：检查系统

  ```bash {"title": "脚本1"}
  uname -a
  ```

- 第二步：检查网络

  ```bash {"title": "脚本2"}
  ping -c 1 127.0.0.1
  ```
"""
        scripts = extract_script_blocks(text)

        assert len(scripts) == 2
        assert scripts[0]['title'] == "脚本1"
        assert "uname -a" in scripts[0]['code']
        assert scripts[1]['title'] == "脚本2"
        assert "ping" in scripts[1]['code']

    def test_router_extract_consecutive_indented_blocks(self):
        """测试路由层处理连续缩进代码块"""
        from scriptbook.routers.markdown import extract_script_blocks

        text = """- 项目A

  ```bash {"title": "A脚本"}
  echo A
  ```

- 项目B

  ```bash {"title": "B脚本"}
  echo B
  ```

- 项目C

  ```bash {"title": "C脚本"}
  echo C
  ```
"""
        scripts = extract_script_blocks(text)

        assert len(scripts) == 3
        assert scripts[0]['title'] == "A脚本"
        assert scripts[1]['title'] == "B脚本"
        assert scripts[2]['title'] == "C脚本"