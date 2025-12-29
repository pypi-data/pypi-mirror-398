# ANSI 转义序列解析示例

本文档展示了 Scriptbook 的 ANSI 转义序列解析功能，可以让脚本输出的颜色和格式在浏览器中正确显示。

## 什么是 ANSI 转义序列？

ANSI 转义序列是终端控制码，用于在命令行中显示颜色、粗体、下划线等格式效果。

## 基本颜色示例

以下脚本演示了基本的颜色输出：

```bash
#!/bin/bash
# 颜色代码说明：
# 红色：\033[31m 或 \033[1;31m
# 绿色：\033[32m 或 \033[1;32m
# 黄色：\033[33m 或 \033[1;33m
# 蓝色：\033[34m
# 重置：\033[0m

printf "\033[32m✓ 成功：操作已完成\033[0m\n"
printf "\033[33m⚠ 警告：这是一个警告信息\033[0m\n"
printf "\033[31m✗ 错误：操作失败\033[0m\n"
printf "\033[34mℹ 信息：这是一条普通信息\033[0m\n"
```

## 带格式的颜色示例

```bash
#!/bin/bash
printf "\033[1;32m粗体绿色文本\033[0m\n"
printf "\033[4;33m下划线黄色文本\033[0m\n"
printf "\033[1;4;31m粗体下划线红色文本\033[0m\n"
printf "\033[7;32m反色显示绿色背景\033[0m\n"
```

## 构建过程示例

模拟一个典型的构建过程，带有彩色输出：

```bash
#!/bin/bash
printf "\033[1;34m=== 开始构建项目 ===\033[0m\n"
printf "\n"

printf "\033[33m[1/4]\033[0m 检查依赖...\n"
sleep 1
printf "\033[32m✓ 依赖检查完成\033[0m\n"
printf "\n"

printf "\033[33m[2/4]\033[0m 编译源码...\n"
sleep 1
printf "\033[32m✓ 编译成功\033[0m\n"
printf "\n"

printf "\033[33m[3/4]\033[0m 运行测试...\n"
sleep 1
printf "\033[31m✗ 测试失败：3 个测试用例未通过\033[0m\n"
printf "\n"

printf "\033[33m[4/4]\033[0m 打包...\n"
sleep 1
printf "\033[32m✓ 打包完成\033[0m\n"
printf "\n"

printf "\033[1;32m=== 构建完成 ===\033[0m\n"
```

## 包管理器输出示例

模拟 npm/yarn 的彩色输出：

```bash
#!/bin/bash
printf "\033[1;36mnpm\033[0m \033[32minstall\033[0m lodash\n"
printf "\n"
printf "\033[90mnpm WARN\033[0m \033[33mpackage.json\033[0m No license field\n"
printf "\033[90mnpm WARN\033[0m \033[33mdeprecated\033[0m \033[1;33mtunnel-agent\033[0m@0.6.1: \033[31mDEPRECATED\033[0m\n"
printf "\n"
printf "\033[32m+ lodash@4.17.21\033[0m\n"
printf "\033[36madded\033[0m \033[1;32m1 package\033[0m \033[90min 2s\033[0m\n"
```

## Git 操作示例

```bash
#!/bin/bash
printf "\033[1;32mOn branch main\033[0m\n"
printf "\033[90mYour branch is up to date with 'origin/main'.\033[0m\n"
printf "\n"
printf "\033[32mnothing to commit, working tree clean\033[0m\n"
printf "\n"
printf "\033[1;33mChanges not staged for commit:\033[0m\n"
printf "  \033[31mmodified:\033[0m   src/app.js\n"
printf "  \033[32madded:\033[0m    README.md\n"
```

## 系统监控示例

```bash
#!/bin/bash
printf "\033[1;36m=== 系统监控 ===\033[0m\n"

# CPU 使用率
printf "\033[33mCPU 使用率:\033[0m\n"
printf "  \033[32m███\033[0m\033[90m███████\033[0m \033[1;32m25%\033[0m\n"
printf "\n"

# 内存使用
printf "\033[33m内存使用:\033[0m\n"
printf "  \033[32m███████\033[0m\033[90m███\033[0m \033[1;32m75%\033[0m (6.0GB/8.0GB)\n"
printf "\n"

# 磁盘使用
printf "\033[33m磁盘使用:\033[0m\n"
printf "  \033[31m██████████\033[0m \033[1;31m100%\033[0m (1.2TB/1.2TB)\n"
printf "\n"

printf "\033[1;32m✓ 监控完成\033[0m\n"
```

## 错误处理示例

```bash
#!/bin/bash
printf "\033[31m✗ 错误：文件不存在\033[0m\n"
printf "\033[90m  at /path/to/script.js:10:5\033[0m\n"
printf "\033[90m  at Module._compile (internal/modules/cjs/loader.js:1063:15)\033[0m\n"
printf "\n"
printf "\033[33m提示：检查文件路径是否正确\033[0m\n"
```

## 自定义颜色函数示例

```bash
#!/bin/bash
# 定义颜色函数
print_success() {
    echo -e "\033[1;32m✓ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠ $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m✗ $1\033[0m"
}

print_info() {
    echo -e "\033[1;36mℹ $1\033[0m"
}

# 使用颜色函数
print_success "操作成功完成"
print_warning "这是一个警告"
print_error "发生了一个错误"
print_info "这是一条信息"
```

## 多行彩色文本

```bash
#!/bin/bash
cat << 'EOF'
\033[1;32m
 ____  _                           _       _
|  _ \| |__   ___  _ __   ___   ___| |_   _| |
| |_) | '_ \ / _ \| '_ \ / _ \ / _ \ | | | | |
|  __/| | | | (_) | | | |  __/ |  __/ | |_| |_|
|_|   |_| |_|\___/|_| |_|\___|  \___|_|\__, (_)
                                        __/ |
                                       |___/
\033[0m
EOF
echo ""
echo -e "\033[1;36m欢迎使用 Scriptbook！\033[0m"
```

## 进度条示例

```bash
#!/bin/bash
echo -e "\033[1;36m正在下载文件...\033[0m"
for i in {0..100..10}; do
    echo -ne "\r\033[33m进度: [\033[0m"
    for ((j=0; j<i/10; j++)); do
        echo -ne "\033[32m█\033[0m"
    done
    for ((j=i/10; j<10; j++)); do
        echo -ne "\033[90m░\033[0m"
    done
    echo -ne "\033[33m] \033[1;32m${i}%\033[0m"
    sleep 0.2
done
echo ""
echo -e "\033[32m✓ 下载完成！\033[0m"
```

## 表格输出示例

```bash
#!/bin/bash
echo -e "\033[1;36m=== 服务器状态 ===\033[0m"
echo ""
echo -e "\033[90m┌────────────┬────────┬────────┐\033[0m"
echo -e "\033[90m│\033[0m \033[33m服务名\033[0m       \033[90m│\033[0m \033[33m状态\033[0m   \033[90m│\033[0m \033[33m内存\033[0m  \033[90m│\033[0m"
echo -e "\033[90m├────────────┼────────┼────────┤\033[0m"
echo -e "\033[90m│\033[0m Web Server  \033[90m│\033[0m \033[32m运行中\033[0m \033[90m│\033[0m 256MB \033[90m│\033[0m"
echo -e "\033[90m│\033[0m Database    \033[90m│\033[0m \033[32m运行中\033[0m \033[90m│\033[0m 512MB \033[90m│\033[0m"
echo -e "\033[90m│\033[0m Cache       \033[90m│\033[0m \033[31m已停止\033[0m \033[90m│\033[0m   0MB \033[90m│\033[0m"
echo -e "\033[90m└────────────┴────────┴────────┘\033[0m"
```

## 提示

在 Scriptbook 中运行这些脚本时，您会看到：

1. ✅ 所有的 ANSI 转义序列会被正确解析
2. ✅ 颜色和格式会显示在浏览器中
3. ✅ 就像在真实终端中一样！
4. ✅ 支持 16 色、256 色等多种颜色模式
5. ✅ 支持粗体、下划线、反色等文本格式

这些示例展示了 ANSI 转义序列的强大功能，让您的脚本输出更加直观和美观！
