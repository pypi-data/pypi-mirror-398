/**
 * TerminalManager - 管理 xterm.js 终端实例
 * 负责创建终端、处理 ANSI 转义序列、持久化等
 */
class TerminalManager {
    constructor() {
        this.terminals = new Map(); // scriptId -> { term, container }
        this.charWidth = null; // 字符宽度（像素）
        this.charHeight = null; // 字符高度（像素）
        this.resizeObserver = null; // ResizeObserver 实例
    }

    /**
     * 测量字符大小
     * @param {HTMLElement} container - 容器元素
     * @returns {{width: number, height: number}}
     */
    measureCharSize(container) {
        // 创建临时测量元素，确保在 DOM 中
        const measureEl = document.createElement('div');
        measureEl.style.position = 'fixed';
        measureEl.style.visibility = 'hidden';
        measureEl.style.whiteSpace = 'pre';
        measureEl.style.left = '-9999px';
        measureEl.style.fontFamily = "'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace";
        measureEl.style.fontSize = '13px';
        measureEl.style.fontKerning = 'none';
        measureEl.style.letterSpacing = '0';
        measureEl.textContent = 'W'.repeat(50); // 50个W字符
        document.body.appendChild(measureEl);

        const rect = measureEl.getBoundingClientRect();
        document.body.removeChild(measureEl);

        const width = rect.width / 50;
        const height = rect.height;

        return { width, height };
    }

    /**
     * 根据容器宽度计算列数
     * @param {HTMLElement} container - 容器元素
     * @returns {number} 列数
     */
    calculateCols(container) {
        // 每次都重新测量，不使用缓存
        const sizes = this.measureCharSize(container);
        this.charWidth = sizes.width;
        this.charHeight = sizes.height;

        // 获取容器可用宽度（减去 padding）
        const containerStyle = window.getComputedStyle(container);
        const paddingLeft = parseFloat(containerStyle.paddingLeft) || 0;
        const paddingRight = parseFloat(containerStyle.paddingRight) || 0;
        const availableWidth = container.clientWidth - paddingLeft - paddingRight;

        // 计算列数（留更多余量，让长文本能换行）
        const cols = Math.floor(availableWidth / this.charWidth) - 3;
        return Math.max(40, cols); // 至少40列
    }

    /**
     * 根据容器高度计算行数
     * @param {HTMLElement} container - 容器元素
     * @returns {number} 行数
     */
    calculateRows(container) {
        if (this.charHeight === null) {
            const sizes = this.measureCharSize(container);
            this.charWidth = sizes.width;
            this.charHeight = sizes.height;
        }

        // 获取容器可用高度（减去 padding）
        const containerStyle = window.getComputedStyle(container);
        const paddingTop = parseFloat(containerStyle.paddingTop) || 0;
        const paddingBottom = parseFloat(containerStyle.paddingBottom) || 0;
        const availableHeight = container.clientHeight - paddingTop - paddingBottom;

        // 计算行数（留更多余量）
        const rows = Math.floor(availableHeight / this.charHeight) - 3;
        return Math.max(6, rows); // 至少6行
    }

    /**
     * 设置 ResizeObserver 监听容器大小变化
     * @param {string} scriptId - 脚本ID
     * @param {HTMLElement} container - 容器元素
     * @param {object} term - 终端实例
     */
    observeResize(scriptId, container, term) {
        // 取消之前的 observer
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }

        // 创建新的 ResizeObserver
        this.resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const cols = this.calculateCols(container);
                const rows = this.calculateRows(container);
                term.resize(cols, rows);
            }
        });

        this.resizeObserver.observe(container);
    }

    /**
     * 为指定脚本创建终端
     * @param {string} scriptId - 脚本ID
     * @param {HTMLElement} container - 终端容器元素
     */
    createTerminal(scriptId, container) {
        if (this.terminals.has(scriptId)) {
            this.disposeTerminal(scriptId);
        }

        // 从当前主题获取终端配色
        const terminalTheme = this.getTerminalTheme();

        // 计算自适应列数和行数
        const cols = this.calculateCols(container);
        const rows = Math.max(10, this.calculateRows(container)); // 至少10行

        // 创建终端实例
        const term = new window.Terminal({
            cursorBlink: false, // 禁用闪烁，避免视觉干扰
            cursorStyle: 'block', // 使用方块光标
            convertEol: true, // 转换 \n 为 \r\n
            fontFamily: "'SF Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace",
            fontSize: 13,
            theme: terminalTheme,
            cols: cols, // 自适应列数
            rows: rows, // 自适应行数
            allowTransparency: true,
            scrollback: 10000, // 滚动缓冲区大小（更多行）
            wraparoundLinesEnabled: true, // 启用自动换行
        });

        // 挂载到容器
        term.open(container);

        // 监听数据写入，动态扩展行数
        term.onData(() => {
            this.maybeExpandTerminal(scriptId, container, term);
        });

        // 设置 ResizeObserver 监听容器大小变化
        this.observeResize(scriptId, container, term);

        term.write('\x1b[2m执行结果将显示在这里...\x1b[0m\r\n');

        // 保存终端实例和容器
        this.terminals.set(scriptId, { term, container });

        return term;
    }

    /**
     * 动态扩展终端行数
     * @param {string} scriptId - 脚本ID
     * @param {HTMLElement} container - 容器元素
     * @param {object} term - 终端实例
     */
    maybeExpandTerminal(scriptId, container, term) {
        const MAX_ROWS = 50; // 最大行数限制
        const buffer = term.buffer;
        const activeBuffer = buffer.active;
        const currentRows = activeBuffer.length;

        // 如果内容超过当前行数，自动扩展
        if (currentRows > term.rows && term.rows < MAX_ROWS) {
            const newRows = Math.min(currentRows + 5, MAX_ROWS);
            term.resize(term.cols, newRows);

            // 当行数超过一定值时，启用滚动条
            if (newRows > 15) {
                container.classList.add('has-overflow');
            }
        } else if (term.rows >= MAX_ROWS) {
            // 已达到最大行数，确保滚动条已启用
            container.classList.add('has-overflow');
        }
    }

    /**
     * 获取终端实例
     * @param {string} scriptId - 脚本ID
     */
    getTerminal(scriptId) {
        const terminal = this.terminals.get(scriptId);
        return terminal ? terminal.term : null;
    }

    /**
     * 向终端写入内容（支持 ANSI 转义序列）
     * @param {string} scriptId - 脚本ID
     * @param {string} content - 要写入的内容
     */
    write(scriptId, content) {
        const term = this.getTerminal(scriptId);
        const terminal = this.terminals.get(scriptId);
        if (term) {
            term.write(content, () => {
                // 写入完成后检查是否需要扩展
                if (terminal) {
                    this.maybeExpandTerminal(scriptId, terminal.container, term);
                }
            });
        }
    }

    /**
     * 向终端写入一行内容
     * @param {string} scriptId - 脚本ID
     * @param {string} content - 要写入的内容
     * @param {string} type - 输出类型 (stdout, stderr, stdin)
     */
    writeln(scriptId, content, type = 'stdout') {
        const term = this.getTerminal(scriptId);
        const terminal = this.terminals.get(scriptId);
        if (!term) return;

        // 根据类型添加颜色标记
        let prefix = '';
        if (type === 'stderr') {
            prefix = '\x1b[31m'; // 红色
        } else if (type === 'stdin') {
            prefix = '\x1b[36m'; // 青色
        } else if (type === 'exit') {
            prefix = '\x1b[33m'; // 黄色
        }

        const suffix = (type === 'stderr' || type === 'exit') ? '\x1b[0m' : '';

        term.write(`${prefix}${content}${suffix}\r\n`, () => {
            // 写入完成后检查是否需要扩展
            if (terminal) {
                this.maybeExpandTerminal(scriptId, terminal.container, term);
            }
        });
    }

    /**
     * 清除终端内容
     * @param {string} scriptId - 脚本ID
     */
    clear(scriptId) {
        const term = this.getTerminal(scriptId);
        if (term) {
            term.clear();
        }
    }

    /**
     * 重置终端
     * @param {string} scriptId - 脚本ID
     */
    reset(scriptId) {
        const term = this.getTerminal(scriptId);
        if (term) {
            term.reset();
        }
    }

    /**
     * 获取终端原始内容（用于持久化）
     * @param {string} scriptId - 脚本ID
     */
    getContent(scriptId) {
        const term = this.getTerminal(scriptId);
        if (term) {
            return term.getContent();
        }
        return '';
    }

    /**
     * 获取终端缓冲区行数
     * @param {string} scriptId - 脚本ID
     */
    getRows(scriptId) {
        const term = this.getTerminal(scriptId);
        if (term) {
            return term.rows;
        }
        return 0;
    }

    /**
     * 释放终端实例
     * @param {string} scriptId - 脚本ID
     */
    disposeTerminal(scriptId) {
        const terminal = this.terminals.get(scriptId);
        if (terminal) {
            try {
                // 断开 ResizeObserver
                if (this.resizeObserver) {
                    this.resizeObserver.disconnect();
                }
                terminal.term.dispose();
            } catch (e) {
                console.warn('释放终端失败:', e);
            }
            this.terminals.delete(scriptId);
        }
    }

    /**
     * 释放所有终端
     */
    disposeAll() {
        this.terminals.forEach((_, scriptId) => {
            this.disposeTerminal(scriptId);
        });
    }

    /**
     * 获取当前主题的终端配色
     * @returns {object} terminal theme 配置
     */
    getTerminalTheme() {
        // 优先从插件加载器获取
        if (window.pluginLoader) {
            return window.pluginLoader.getTerminalTheme();
        }
        // 回退到本地插件列表
        if (window.plugins) {
            const currentTheme = localStorage.getItem('scriptbook_theme') || 'theme-light';
            const plugin = window.plugins.find(p => p.name === currentTheme);
            if (plugin && plugin.terminalTheme) {
                return plugin.terminalTheme;
            }
        }
        // 默认返回 light 主题配置
        return {
            background: '#ffffff',
            foreground: '#333333',
            cursor: '#333333',
            cursorAccent: '#ffffff',
            selectionBackground: '#b4d5ff'
        };
    }

    /**
     * 应用主题
     * @param {string} theme - 主题类型 ('light' 或 'dark')
     */
    applyTheme(theme) {
        // 从插件配置获取终端配色
        const terminalTheme = this.getTerminalTheme();
        this.terminals.forEach((terminal) => {
            const term = terminal.term;
            term.options.theme = terminalTheme;
            // 强制刷新 Canvas renderer
            term.refresh(0, term.rows - 1);
        });
    }
}

// 导出到全局
window.TerminalManager = TerminalManager;
