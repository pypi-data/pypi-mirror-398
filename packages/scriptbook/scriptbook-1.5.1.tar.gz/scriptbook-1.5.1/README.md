# Scriptbook - 可执行脚本的 Markdown 服务器

[English](README_en.md)

一个支持脚本执行的在线 Markdown 服务器。借鉴 Jupyter Notebook 的设计理念，支持在 Markdown 文档中嵌入并执行脚本，非常适合 SOP（标准操作流程）自动化和交互式文档场景。

## 功能特性

- **交互式文档** - 在Markdown中嵌入可执行脚本，类似Jupyter Notebook
- **交互式输入** - 支持在脚本执行过程中接收用户输入（如`read`命令）
- **实时执行** - WebSocket实现脚本实时输出流
- **独立输出** - 每个脚本块下方有独立的输出区域
- **结果持久化** - 页面刷新后自动恢复脚本执行结果（使用localStorage）
- **停止执行** - 支持随时终止正在执行的脚本
- **多文档支持** - 支持多个文档切换，结果独立保存
- **主题切换** - 支持浅色、暗色、GitHub三种主题
- **终端主题** - 终端配色与主题风格一致
- **ANSI颜色支持** - 脚本输出的颜色和格式在浏览器中正确显示
- **导航栏优化** - 顶部导航栏布局，集成文件选择和主题切换
- **GitHub链接** - 页面右上角提供GitHub仓库链接
- **WebSocket优化** - 改进并发处理，支持页面刷新场景
- **SOP自动化** - 适用于企业标准操作流程的展示和执行
- **完整测试** - 包含109个JavaScript单元测试和集成测试

## 截图预览

![Scriptbook界面截图](docs/screenshot-2025-12-25.png)

## 快速开始

### 环境要求
- Python 3.10+
- 现代浏览器

### 安装

```bash
# 直接安装（推荐）
pip install scriptbook

# 或者从源码安装
git clone https://github.com/lengmoXXL/scriptbook.git
cd scriptbook
pip install .
```

### 使用方法

```bash
# 启动服务（使用默认content目录）
scriptbook content/

# 指定自定义文档目录
scriptbook /path/to/my/documents/

# 指定端口
scriptbook content/ --port 9000

# 允许外部访问
scriptbook content/ --host 0.0.0.0

# 访问应用
open http://localhost:8000
```

**注意**: 修改代码后请手动重启服务以应用更改。

## 发布信息

### PyPI安装

```bash
pip install scriptbook
```

**PyPI链接**: https://pypi.org/project/scriptbook/

### 版本

- 当前版本: 1.5.1
- Python要求: >=3.10

### 更新日志

#### v1.5.1 (2025-12-26)
- 🎨 **终端输出框滚动条优化**
  - 修复多个滚动条显示问题
  - 终端输出框现在只显示一个滚动条
  - 终端内容自适应扩展，高度达到 400px 时启用滚动

#### v1.5.0 (2025-12-25)
- ✨ **新主题：GitHub 风格**
  - 新增 GitHub 风格主题，与 GitHub Markdown 渲染一致
  - 优化代码块、表格、引用块等样式
- 🎨 **终端主题集成**
  - 终端配色与主题风格一致
  - 终端主题配置通过插件 manifest.json 管理
- 🔧 **主题系统重构**
  - 统一主题命名规范（theme-light、theme-dark、theme-github）
  - 插件系统支持终端主题配置
- 🏗️ **导航栏优化**
  - 顶部导航栏布局，整合文件选择和主题切换
  - 移除独立的控制栏区域
  - 添加 GitHub 仓库链接图标
- 📚 **代码清理**
  - 删除 "Markdown预览" 标题
  - 简化页脚内容

#### v1.4.4 (2025-12-25)
- 🔧 **Python 3.10 兼容性修复**
  - 使用 `asyncio.wait_for` 替代 `asyncio.timeout`
  - 修复 async generator 超时处理

#### v1.4.3 (2025-12-25)
- ✨ **PTY 支持** - 修复 Python 3.10~3.14 兼容性问题
  - 使用 `pty.openpty()` 替代被移除的 `pty` 参数
  - 支持 `tty` 命令和需要 TTY 的命令（如 `docker exec -it`）
- 🔧 **代码重构** - 重构 `script_executor.py`
  - 提取 `_cleanup()` 方法简化资源清理
  - 使用 `asyncio.wait_for` 替代 `asyncio.timeout` 以支持 Python 3.10
- ✅ **测试增强** - 新增 TTY 命令集成测试

#### v1.4.2 (2025-12-24)
- 🎨 **xterm.js Canvas渲染器** - 从DOM渲染器切换到Canvas渲染器
  - 解决滚动问题，提供更流畅的滚动体验
  - 终端背景与页面主题保持一致
  - 主题切换时终端自动跟随变色
- 🐛 **问题修复**
  - 修复 xterm.css 问题，下载正确样式文件
  - 修复 xterm.js 背景灰色问题
  - 修复主题切换时终端颜色不变的问题
  - 修复暗色主题下终端初始化为白色的问题
- 📚 **代码清理** - 移除废弃样式和调试代码

#### v1.4.0 (2025-12-24)
- ✨ **xterm.js嵌入式终端** - 使用专业终端模拟器渲染脚本输出
  - 支持完整的ANSI转义序列解析
  - 提供更好的终端体验（滚动、选择、复制）
  - 浅色主题适配（#f5f5f5背景 + #333333文字）
  - 颜色编码：stdout无色、stderr红色、stdin青色、exit黄色
- 🔧 **技术改进**
  - 新增 `terminal-manager.js` 终端管理器类
  - 新增 `lib/xterm.js` 和 `lib/xterm.css`
  - 移除废弃的 `ansi-html.js` 和 `ansi-parser.js`
- 🧪 **测试增强** - 新增26个TerminalManager单元测试，总测试数更新为192个

#### v1.3.0 (2025-12-22)
- ✨ **ANSI转义序列解析** - 脚本输出的颜色和格式在浏览器中正确显示
  - 支持16种基础颜色（黑、红、绿、黄、蓝、紫、青、白）
  - 支持粗体、斜体、下划线、反色等格式效果
  - 支持 \x1b[]、\033[] 和 [] 格式的ANSI序列
- 🎨 **按钮布局优化** - 所有操作按钮移至脚本块头部同一行
  - 统一按钮样式：执行（绿）+ 复制（蓝）+ 停止（红）
  - 响应式布局，移动端自适应
- 🔧 **输出区域优化** - 移除分隔线，极紧凑行间距，baseline对齐
- 📚 **文档完善** - 新增15+个ANSI使用示例
- 🧪 **测试增强** - 新增15个JavaScript测试，总测试数更新为153个

#### v1.2.0 (2025-12-22)
- 📚 新增发布流程文档 - 规范化代码整理和发布流程
- 🔧 优化项目结构 - 清理开发过程文档，创建完整文档体系
- 📄 完善文档系统 - 添加CLAUDE.md、CHANGELOG.md、RELEASE_PROCESS.md
- 🎯 简化发布流程 - 优化RELEASE_PROCESS.md使其更简洁易用
- ✨ 改进开发体验 - 提供清晰的项目结构和操作指南

#### v1.0.0 (2025-12-21)
- 项目重命名为 Scriptbook
- 新增交互式输入功能，支持在脚本执行过程中接收用户输入
- 新增25个JavaScript单元测试
- 重组测试目录结构，统一管理测试文件
- 优化WebSocket通信，支持stdin双向交互
- 所有102个测试全部通过

### 许可证

MIT License

### GitHub仓库

- 源码: https://github.com/lengmoXXL/scriptbook
- 问题反馈: https://github.com/lengmoXXL/scriptbook/issues

## 测试

本项目包含完整的测试套件，总计192个测试用例。

### 运行所有测试

```bash
# 运行所有测试（单元测试 + 集成测试）
pytest src/ src/integration_tests/ -v

# 运行JavaScript测试
cd src/tests/js
npm test
```

### 分别运行测试

```bash
# Python 单元测试
pytest src/tests/ -v

# JavaScript 单元测试
cd src/tests/js
npm test

# 集成测试
pytest src/integration_tests/ -v
```

### 测试文件说明

- **脚本结果持久化测试** (`script-results-persistence.test.js`): 9个测试
- **脚本结果持久化集成测试** (`script-results-persistence-integration.test.js`): 7个测试
- **WebSocket并发测试** (`websocket-concurrency.test.js`): 8个测试
- **脚本停止功能测试** (`script-stop-functionality.test.js`): 12个测试
- **App类基础功能测试** (`app.test.js`): 25个测试

### 测试覆盖率

- **JavaScript 测试**: 109个测试用例（使用Jest + JSDOM）
  - TerminalManager测试: 26个
  - 插件加载器测试: 16个
  - 脚本结果持久化测试: 9个
  - 脚本结果持久化集成测试: 7个
  - WebSocket并发测试: 8个
  - 脚本停止功能测试: 12个
  - App类基础功能测试: 25个
- **Python 单元测试**: 70个测试用例
- **集成测试**: 13个测试用例
- **总测试数**: 192个，全部通过

测试覆盖：
- App类初始化和基本功能
- 全局函数（executeScript、copyCode、sendInput、stopScript）
- WebSocket事件处理和并发控制
- 脚本结果持久化和恢复
- 脚本停止执行功能
- 文件扫描和Markdown解析
- 插件管理系统
- 脚本执行器
- 交互式输入功能

## 开发指南

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/lengmoXXL/scriptbook.git
cd scriptbook

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .
pip install -r requirements-test.txt

# 安装JavaScript测试依赖（仅测试需要）
cd src/tests/js
npm install

# 返回根目录
cd /path/to/scriptbook

# 运行所有测试
pytest src/ src/integration_tests/ -v
```

### 发布到PyPI

```bash
# 构建包
python -m build

# 上传到PyPI
twine upload dist/*
```

或者使用GitHub Actions进行自动发布。

---

**Scriptbook** - 让文档更易于理解和执行
