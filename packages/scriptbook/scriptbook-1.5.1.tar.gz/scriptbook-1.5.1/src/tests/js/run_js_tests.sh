#!/bin/bash

# SOP Online JavaScript 测试运行脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 获取项目根目录（脚本所在目录的父目录的父目录）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"

echo "==================================="
echo "SOP Online JavaScript 单元测试"
echo "==================================="
echo ""
echo "项目根目录: $PROJECT_ROOT"
echo "测试目录: $SCRIPT_DIR"
echo ""

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo ""
    echo "请安装 Node.js: https://nodejs.org/"
    echo ""
    exit 1
fi

# 检查 npm 是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    echo ""
    echo "请安装 npm"
    echo ""
    exit 1
fi

# 进入测试目录
cd "$SCRIPT_DIR"

echo "📦 检查测试依赖..."
if [ ! -d "node_modules" ]; then
    echo "📥 安装测试依赖..."
    npm install
    echo ""
fi

echo "🧪 运行单元测试..."
echo ""

# 运行测试
npm test "$@"

echo ""
echo "✅ 测试完成！"