# Scriptbook 测试用例文档

本文档包含各种测试用例，用于验证 Scriptbook 平台的功能完整性。

## 1. 基础脚本块测试

### 1.1 无元数据的简单脚本

```bash
echo "这是一个简单的echo命令"
echo "多行输出"
ls -la
```

### 1.2 带元数据的脚本块

```bash {"id": "custom_script_1", "title": "自定义标题的脚本"}
echo "这个脚本有自定义的ID和标题"
date
whoami
```

### 1.3 部分元数据（只有title）

```bash {"title": "仅标题测试"}
echo "只有title，没有自定义ID"
pwd
```

## 2. 不同编程语言

### 2.1 Python脚本

```python
print("Hello from Python!")
import sys
print(f"Python版本: {sys.version}")
```

### 2.2 Shell脚本（无语言指定）

```sh {"title": "Shell脚本"}
#!/bin/bash
echo "Shell脚本测试"
for i in {1..3}; do
    echo "循环 $i"
done
```

### 2.3 无语言标识（默认）

```text
echo "这是一个没有指定语言的代码块"
# 注释测试
```

## 3. 复杂代码结构

### 3.1 长脚本（多行）

```bash {"title": "复杂系统检查"}
#!/bin/bash

# 系统信息
echo "=== 系统信息 ==="
echo "主机名: $(hostname)"
echo "内核版本: $(uname -r)"
echo "系统架构: $(uname -m)"
echo ""

# 磁盘使用
echo "=== 磁盘使用 ==="
df -h
echo ""

# 内存使用
echo "=== 内存使用 ==="
free -h
```

### 3.2 嵌套引号测试

```bash {"title": "嵌套引号处理"}
echo '单引号: 内部有"双引号"'
echo "双引号: 内部有'单引号'"
echo "混合引号: 特殊字符测试 \$PATH"
```

### 3.3 特殊字符和转义

```bash {"title": "特殊字符测试"}
# 特殊字符测试
echo "美元符号: \$100"
echo "反斜杠: \\"
echo "换行符: 第一行\n第二行"
echo "制表符: [\t]"
```

## 4. 错误和边缘情况

### 4.1 无效JSON元数据

```bash {invalid json here
echo "元数据不是有效的JSON"
ls
```

### 4.2 空代码块

```bash {"title": "空代码块测试"}

```

### 4.3 只有注释的代码块

```bash {"title": "纯注释测试"}
# 这是一个注释
# 另一个注释
# 没有实际命令
```

## 5. 智能标题生成测试

### 5.1 echo命令提取

```bash
echo "欢迎使用 Scriptbook"
date
```

### 5.2 cat命令提取

```bash
cat /etc/hostname
```

### 5.3 ls命令提取

```bash
ls -la /tmp
```

### 5.4 cd命令提取

```bash
cd /usr/local
pwd
```

### 5.5 git命令提取

```bash
git status
git log --oneline -3
```

### 5.6 长命令提取

```bash
这是一个非常长的命令，包含了很多单词，应该被截断成前几个词作为标题
```

## 6. Markdown混合内容

### 6.1 脚本前后有文本

脚本前的文本内容。

```bash {"title": "前后有文本的脚本"}
echo "这个脚本在普通文本之间"
```

脚本后的文本内容。

### 6.2 列表中的脚本

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

### 6.3 代码块中的代码块（嵌套）

这是一个包含反引号的段落：`内联代码`。

```
这不是脚本块，因为没有三个反引号
```

## 7. 多脚本交互

### 7.1 创建文件并读取

```bash {"id": "create_file", "title": "创建测试文件"}
echo "测试内容" > /tmp/test_scriptbook.txt
echo "文件已创建"
```

```bash {"id": "read_file", "title": "读取测试文件"}
cat /tmp/test_scriptbook.txt
```

```bash {"id": "delete_file", "title": "删除测试文件"}
rm /tmp/test_scriptbook.txt
echo "文件已删除"
```

### 7.2 顺序执行示例

```bash {"title": "第一步：初始化"}
counter=0
echo "计数器初始化: $counter"
```

```bash {"title": "第二步：递增"}
counter=$((counter + 1))
echo "计数器递增: $counter"
```

```bash {"title": "第三步：完成"}
echo "最终计数器: $counter"
```

## 8. 输出格式测试

### 8.1 标准输出

```bash {"title": "标准输出测试"}
echo "正常输出"
echo "多行输出1"
echo "多行输出2"
echo "多行输出3"
```

### 8.2 标准错误

```bash {"title": "标准错误测试"}
echo "先输出正常信息" >&1
echo "再输出错误信息" >&2
ls /nonexistent_directory 2>&1
```

### 8.3 退出码测试

```bash {"title": "成功退出"}
echo "命令成功"
exit 0
```

```bash {"title": "失败退出"}
echo "命令失败"
exit 1
```

## 9. 性能测试

### 9.1 快速输出

```bash {"title": "快速输出测试"}
for i in {1..10}; do
    echo "输出行 $i"
    sleep 0.1
done
```

### 9.2 长时间运行

```bash {"title": "长时间运行测试"}
echo "脚本开始运行"
for i in {1..30}; do
    echo "运行中... $i 秒"
    sleep 1
done
echo "脚本完成"
```

## 10. WebSocket特定测试

### 10.1 实时输出

```bash {"title": "WebSocket实时输出"}
echo "开始实时输出测试"
for i in {1..5}; do
    echo "实时数据包 $i"
    sleep 0.5
done
echo "实时输出完成"
```

### 10.2 大输出量

```bash {"title": "大输出量测试"}
echo "生成大输出..."
for i in {1..100}; do
    echo "行号 $i: $(date '+%H:%M:%S.%N')"
done
echo "输出完成"
```

---

## 总结

这个文档包含了各种测试用例，涵盖了：

1. **基本功能**：脚本提取、元数据解析、智能标题生成
2. **边界情况**：空代码块、无效JSON、特殊字符
3. **复杂场景**：多脚本交互、嵌套引号、长脚本
4. **性能测试**：实时输出、大输出量、长时间运行
5. **集成测试**：WebSocket通信、脚本执行顺序

用于确保 Scriptbook 平台在各种情况下都能正常工作。