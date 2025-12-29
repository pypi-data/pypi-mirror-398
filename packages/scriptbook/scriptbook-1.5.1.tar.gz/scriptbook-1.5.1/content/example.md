# Markdown脚本执行示例

这是一个展示脚本执行功能的markdown文件。

## 基本命令

下面是一个简单的bash脚本：

```bash
echo "当前目录文件列表："
ls -la
```

## 带颜色的输出示例

```bash
#!/bin/bash
printf "\033[32m✓ 成功：文件创建完成\033[0m\n"
printf "\033[33m⚠ 警告：请检查文件权限\033[0m\n"
printf "\033[31m✗ 错误：文件不存在\033[0m\n"
```

## 系统信息

查看系统信息：

```bash
echo "系统信息："
uname -a
echo ""
echo "内存使用："
free -h
```

## 网络检查

检查网络连接：

```bash
echo "测试网络连接..."
ping -c 3 google.com
```

## 文件操作

创建和删除测试文件：

```bash
echo "创建测试文件："
echo "Hello from script" > test.txt
cat test.txt
echo ""
echo "删除测试文件："
rm test.txt
echo "文件已删除"
```

## TTY 检查

查看当前终端设备：

```bash
tty
```

## 长输出测试

测试长文本输出效果（超过100个字符的行）：

```bash
for i in {1..5}; do
    echo "这是一行很长的测试输出，用于测试终端对长文本的渲染效果，字符数超过一百五十个字符确保测试准确性和完整性验证终端的滚动条行为和水平滚动功能是否正常工作。"
done
echo "上面5行输出，每行都超过150个字符，用于测试滚动和渲染效果，确保长文本不会截断或错误换行。"
```

## 结束

所有脚本都可以通过点击旁边的"执行"按钮来运行。