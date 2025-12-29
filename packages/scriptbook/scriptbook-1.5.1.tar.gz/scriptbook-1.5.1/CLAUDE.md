# Scriptbook 项目结构

## 项目概述

Scriptbook 是一个支持脚本执行的 Markdown 服务器，提供结果持久化和停止功能。

## 目录结构

```
scriptbook/
├── content/                    # 示例Markdown文件目录
│   ├── example.md             # 示例文档
│   ├── test_cases.md          # 测试用例
│   └── test_interactive.md    # 交互式测试
│
├── docs/                      # 项目文档
│   ├── screenshot.png         # 界面截图
│   └── testing/               # 测试相关文档
│       ├── STOP_BUTTON_FIX.md
│       ├── test-stop-button.html
│       └── verify-stop-button.html
│
├── src/                       # 源代码
│   ├── scriptbook/           # 主包
│   │   ├── __init__.py       # 包初始化，版本信息
│   │   ├── main.py           # FastAPI应用入口
│   │   ├── cli.py            # 命令行接口
│   │   │
│   │   ├── core/             # 核心功能
│   │   │   ├── __init__.py
│   │   │   ├── file_scanner.py      # 文件扫描
│   │   │   ├── markdown_parser.py   # Markdown解析
│   │   │   ├── plugin_manager.py    # 插件管理
│   │   │   └── script_executor.py   # 脚本执行
│   │   │
│   │   ├── models/           # 数据模型
│   │   │   ├── __init__.py
│   │   │   └── schemas.py           # Pydantic模式
│   │   │
│   │   ├── routers/          # API路由
│   │   │   ├── __init__.py
│   │   │   ├── markdown.py          # Markdown相关API
│   │   │   ├── plugins.py           # 插件相关API
│   │   │   └── scripts.py           # 脚本执行API
│   │   │
│   │   └── static/           # 静态资源
│   │       ├── css/
│   │       │   └── main.css         # 主样式文件
│   │       ├── js/
│   │       │   ├── app.js           # 主应用逻辑
│   │       │   ├── plugin-loader.js # 插件加载器
│   │       │   ├── terminal-manager.js # 终端管理器
│   │       │   └── lib/
│   │       │       ├── xterm.js     # xterm.js终端库
│   │       │       └── xterm.css    # xterm.js样式
│   │       ├── index.html           # 主页面模板
│   │       └── plugins/             # 主题插件
│   │           ├── default/
│   │           └── dark-theme/
│   │
│   ├── tests/                # 单元测试
│   │   ├── __init__.py
│   │   ├── conftest.py       # pytest配置
│   │   ├── js/               # JavaScript测试
│   │   │   ├── setup.js           # 测试环境设置
│   │   │   ├── __mocks__/         # 模拟文件
│   │   │   ├── app.test.js        # App类测试 (25个)
│   │   │   ├── plugin-loader.test.js # 插件加载器测试 (16个)
│   │   │   ├── script-results-persistence.test.js  # 持久化测试 (9个)
│   │   │   ├── script-results-persistence-integration.test.js # 集成测试 (7个)
│   │   │   ├── websocket-concurrency.test.js      # WebSocket测试 (8个)
│   │   │   └── script-stop-functionality.test.js  # 停止功能测试 (12个)
│   │   │
│   │   ├── test_file_scanner.py   # 文件扫描测试
│   │   ├── test_markdown_parser.py # Markdown解析测试
│   │   ├── test_plugin_manager.py  # 插件管理测试
│   │   ├── test_report.py         # 报告测试
│   │   └── test_script_executor.py # 脚本执行测试
│   │
│   └── integration_tests/     # 集成测试
│       ├── conftest.py
│       ├── test_scriptbook_pytest.py
│       └── test_websocket_integration.py
│
├── pyproject.toml            # 项目配置和依赖
├── pytest.ini                # pytest配置
├── RELEASE.md                # 发布流程文档
├── requirements.txt          # 生产依赖
├── requirements-test.txt     # 测试依赖
├── README.md                 # 项目说明
└── README_en.md              # 英文版说明
```

## 核心文件说明

### 后端 (Python)
- **`main.py`**: FastAPI应用主入口
- **`routers/scripts.py`**: WebSocket脚本执行，支持并发和错误处理
- **`core/markdown_parser.py`**: Markdown解析和脚本块提取
- **`core/script_executor.py`**: 脚本执行器

### 前端 (JavaScript/CSS)
- **`static/js/app.js`**: 主应用逻辑，包含结果持久化和停止功能
- **`static/css/main.css`**: 主样式，修复了停止按钮可见性
- **`static/index.html`**: 主页面模板

### 测试 (总计192个)
- **JavaScript测试 (109个)**: 使用Jest + JSDOM
- **Python单元测试 (70个)**: 使用pytest
- **集成测试 (13个)**: 端到端测试

## 主要功能

1. **脚本执行**: 通过WebSocket实时执行bash脚本
2. **结果持久化**: localStorage保存，页面刷新后恢复
3. **停止功能**: 红色按钮立即终止脚本执行
4. **交互式输入**: 支持stdin双向通信
5. **主题切换**: 明亮/暗色主题支持
6. **多文档**: 支持多个Markdown文件切换

## 版本历史

- **v1.4.2**: xterm.js Canvas渲染器，主题支持，代码清理
- **v1.4.1**: 修复 docker 命令 TTY 支持问题
- **v1.4.0**: xterm.js嵌入式终端，TerminalManager单元测试
- **v1.3.1**: 修复主题和文档持久化，代码优化，回归测试
- **v1.3.0**: ANSI转义序列解析，按钮布局优化
- **v1.2.0**: 文档体系完善
- **v1.1.0**: 新增持久化和停止功能，修复WebSocket并发
- **v1.0.0**: 初始版本，支持基础脚本执行和交互式输入

## 许可证

MIT License
