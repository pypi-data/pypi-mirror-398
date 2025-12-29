// Scriptbook 主应用逻辑

class App {
    constructor() {
        this.currentFile = null;
        this.activeConnections = new Map(); // scriptId -> WebSocket
        this.terminalManager = new window.TerminalManager();
    }

    async init() {
        console.log('Scriptbook 应用初始化...');

        // 等待 xterm.js 加载完成
        await this.waitForXterm();

        // 等待插件加载器初始化完成（确保终端主题配置可用）
        if (window.pluginLoader) {
            await window.pluginLoader.init();
        }

        // 绑定事件
        this.bindEvents();

        // 加载文件列表
        await this.loadFileList();

        // 恢复之前选择的文件，或自动选择第一个文件
        const savedFile = localStorage.getItem('scriptbook_currentFile');
        if (savedFile && this.fileList) {
            const fileExists = this.fileList.some(f => f.name === savedFile);
            if (fileExists) {
                await this.selectFile(savedFile);
            } else if (this.fileList.length > 0) {
                await this.selectFile(this.fileList[0].name);
            }
        } else if (this.fileList && this.fileList.length > 0) {
            await this.selectFile(this.fileList[0].name);
        }

        // 如果已经有当前文件，恢复结果
        if (this.currentFile) {
            this.restoreScriptResults();
        }

        console.log('Scriptbook 应用初始化完成');
    }

    /**
     * 等待 xterm.js 加载完成
     */
    waitForXterm() {
        return new Promise((resolve) => {
            if (window.Terminal) {
                resolve();
            } else {
                const checkInterval = setInterval(() => {
                    if (window.Terminal) {
                        clearInterval(checkInterval);
                        resolve();
                    }
                }, 100);
                // 超时保护
                setTimeout(() => {
                    clearInterval(checkInterval);
                    resolve();
                }, 5000);
            }
        });
    }

    bindEvents() {
        console.log('绑定事件监听器...');

        // 文件选择器
        const fileSelect = document.getElementById('file-select');
        if (!fileSelect) {
            console.error('找不到文件选择器元素 #file-select');
            return;
        }
        fileSelect.addEventListener('change', (e) => {
            console.log('文件选择器变更:', e.target.value);
            this.selectFile(e.target.value);
        });
    }

    async loadFileList() {
        console.log('loadFileList 调用...');
        try {
            const response = await fetch('/api/markdown/files');
            console.log('文件列表响应状态:', response.status);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            console.log('收到文件列表，文件数量:', data.files?.length);
            this.fileList = data.files;
            this.updateFileSelect(data.files);

            return data.files;
        } catch (error) {
            console.error('加载文件列表失败:', error);
            this.showError('加载文件列表失败: ' + error.message);
            return [];
        }
    }

    updateFileSelect(files) {
        const select = document.getElementById('file-select');
        select.innerHTML = '';

        if (files.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = '没有找到markdown文件';
            select.appendChild(option);
            return;
        }

        files.forEach(file => {
            const option = document.createElement('option');
            option.value = file.name;
            option.textContent = `${file.name} (${this.formatFileSize(file.size)})`;
            select.appendChild(option);
        });
    }

    async selectFile(filename) {
        console.log('selectFile 调用，filename:', filename);
        if (!filename) {
            console.log('selectFile: 空文件名，返回');
            return;
        }

        // 保存到 localStorage
        localStorage.setItem('scriptbook_currentFile', filename);

        try {
            this.currentFile = filename;
            const currentFileElement = document.getElementById('current-file');
            if (currentFileElement) {
                currentFileElement.textContent = `当前文件: ${filename}`;
            } else {
                console.error('找不到 #current-file 元素');
            }

            // 更新下拉框选择
            const fileSelect = document.getElementById('file-select');
            if (fileSelect) {
                fileSelect.value = filename;
            }

            console.log('请求 /api/markdown/render?file=', encodeURIComponent(filename));
            // 使用新的 /render 端点加载完整HTML，禁用缓存
            const response = await fetch(`/api/markdown/render?file=${encodeURIComponent(filename)}`, {
                cache: 'no-cache'
            });
            console.log('响应状态:', response.status, response.ok);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            console.log('收到渲染数据，脚本块数量:', data.scripts.length);

            // 设置HTML到markdown内容区域（包含脚本块）
            const container = document.getElementById('markdown-content');
            if (!container) {
                console.error('找不到 #markdown-content 容器');
                return;
            }
            container.innerHTML = data.html;

            console.log('文件加载完成:', filename);

            // 初始化所有脚本块的终端
            this.initScriptTerminals();

            // 恢复脚本执行结果
            this.restoreScriptResults();

            // 为所有脚本块绑定停止按钮事件
            this.bindStopButtons();

        } catch (error) {
            console.error('选择文件失败:', error);
            this.showError('加载文件失败: ' + error.message);
        }
    }

    /**
     * 初始化所有脚本块的终端
     */
    initScriptTerminals() {
        const scriptBlocks = document.querySelectorAll('.script-block');
        scriptBlocks.forEach(block => {
            const scriptId = block.dataset.scriptId;
            this.createTerminalForScript(scriptId);
        });
    }

    /**
     * 为指定脚本创建终端
     * @param {string} scriptId - 脚本ID
     */
    createTerminalForScript(scriptId) {
        const scriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
        if (!scriptBlock) return;

        // 查找或创建输出容器
        let outputContainer = scriptBlock.querySelector('.script-output');
        if (!outputContainer) {
            // 创建输出容器
            outputContainer = document.createElement('div');
            outputContainer.className = 'script-output';
            outputContainer.id = `output-${scriptId}`;
            outputContainer.style.minHeight = '100px';
            outputContainer.style.maxHeight = '400px';
            outputContainer.style.overflow = 'hidden';
            outputContainer.style.borderTop = '1px solid';
            outputContainer.style.padding = '0';

            // 添加到脚本块
            const scriptCode = scriptBlock.querySelector('.script-code');
            if (scriptCode) {
                scriptCode.parentNode.insertBefore(outputContainer, scriptCode.nextSibling);
            }
        }

        // 清除容器内容
        outputContainer.innerHTML = '';

        // 创建终端
        this.terminalManager.createTerminal(scriptId, outputContainer);
    }

    addScriptOutput(scriptId, type, content) {
        // 使用终端管理器写入内容
        this.terminalManager.writeln(scriptId, content, type);

        // 保存到localStorage（用于持久化）
        this.saveScriptResult(scriptId, type, content);
    }

    saveScriptResult(scriptId, type, content) {
        try {
            if (!this.currentFile) return;

            const storageKey = `scriptResults_${this.currentFile}`;
            const savedResults = JSON.parse(localStorage.getItem(storageKey) || '{}');

            if (!savedResults[scriptId]) {
                savedResults[scriptId] = [];
            }

            savedResults[scriptId].push({
                type,
                content,
                timestamp: new Date().toISOString()
            });

            localStorage.setItem(storageKey, JSON.stringify(savedResults));
            console.log(`已保存脚本 ${scriptId} 的执行结果到 localStorage`);
        } catch (error) {
            console.error('保存脚本结果失败:', error);
        }
    }

    restoreScriptResults() {
        if (!this.currentFile) return;

        try {
            const storageKey = `scriptResults_${this.currentFile}`;
            const savedResults = JSON.parse(localStorage.getItem(storageKey) || '{}');

            console.log(`恢复脚本执行结果:`, savedResults);

            // 恢复每个脚本的结果
            Object.keys(savedResults).forEach(scriptId => {
                const results = savedResults[scriptId];
                const term = this.terminalManager.getTerminal(scriptId);

                if (term && results.length > 0) {
                    // 清除终端并重新写入历史内容
                    term.clear();

                    results.forEach(result => {
                        this.terminalManager.writeln(scriptId, result.content, result.type);
                    });

                    console.log(`已恢复脚本 ${scriptId} 的 ${results.length} 条结果`);
                }
            });
        } catch (error) {
            console.error('恢复脚本结果失败:', error);
        }
    }

    clearScriptResults(scriptId) {
        if (!this.currentFile) return;

        try {
            const storageKey = `scriptResults_${this.currentFile}`;
            const savedResults = JSON.parse(localStorage.getItem(storageKey) || '{}');

            if (savedResults[scriptId]) {
                delete savedResults[scriptId];
                localStorage.setItem(storageKey, JSON.stringify(savedResults));
                console.log(`已清除脚本 ${scriptId} 的执行结果`);
            }
        } catch (error) {
            console.error('清除脚本结果失败:', error);
        }
    }

    bindStopButtons() {
        // 为所有停止按钮绑定事件
        const stopButtons = document.querySelectorAll('.stop-btn');
        stopButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const scriptBlock = e.target.closest('.script-block');
                const scriptId = scriptBlock.dataset.scriptId;
                this.stopScript(scriptId);
            });
        });
    }

    stopScript(scriptId) {
        console.log('停止脚本:', scriptId);

        // 关闭WebSocket连接
        if (this.activeConnections.has(scriptId)) {
            const ws = this.activeConnections.get(scriptId);
            try {
                ws.close();
                console.log('已关闭WebSocket连接:', scriptId);
            } catch (error) {
                console.error('关闭WebSocket连接失败:', error);
            }
            this.activeConnections.delete(scriptId);
        }

        // 恢复UI状态
        const scriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
        if (scriptBlock) {
            const executeBtn = scriptBlock.querySelector('.execute-btn');
            const stopBtn = scriptBlock.querySelector('.stop-btn');

            if (executeBtn) {
                executeBtn.disabled = false;
                executeBtn.textContent = '执行脚本';
            }

            if (stopBtn) {
                stopBtn.disabled = true;
            }

            // 添加停止信息到输出
            this.addScriptOutput(scriptId, 'stdout', '=== 脚本已被用户停止 ===');
        }

        // 隐藏输入容器
        const inputContainer = document.getElementById(`input-container-${scriptId}`);
        if (inputContainer) {
            inputContainer.style.display = 'none';
        }
    }

    showError(message) {
        console.error(message);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 将函数分配给 window 对象，使其在测试环境中可以访问
window.executeScript = async function executeScript(scriptId) {
    console.log('执行脚本:', scriptId);

    // 获取脚本代码
    const scriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
    const codeElement = scriptBlock.querySelector('.script-code');
    const code = codeElement.textContent;

    // 获取输入容器和输入框
    const inputContainer = document.getElementById(`input-container-${scriptId}`);
    const inputElement = document.getElementById(`input-${scriptId}`);

    // 显示输入容器
    if (inputContainer) {
        inputContainer.style.display = 'flex';
    }

    // 添加输入框Enter键事件监听器
    if (inputElement) {
        const handleInputKeyPress = (event) => {
            if (event.key === 'Enter') {
                sendInput(scriptId);
            }
        };
        // 先移除之前的监听器，避免重复添加
        inputElement.removeEventListener('keypress', handleInputKeyPress);
        inputElement.addEventListener('keypress', handleInputKeyPress);
    }

    // 关闭现有连接
    if (window.app.activeConnections.has(scriptId)) {
        const ws = window.app.activeConnections.get(scriptId);
        ws.close();
        window.app.activeConnections.delete(scriptId);
    }

    // 更新UI
    const executeBtn = scriptBlock.querySelector('.execute-btn');
    const stopBtn = scriptBlock.querySelector('.stop-btn');
    executeBtn.disabled = true;
    executeBtn.textContent = '执行中...';
    stopBtn.disabled = false;

    // 重新绑定停止按钮事件（确保绑定正确）
    stopBtn.onclick = () => {
        console.log('停止按钮被点击:', scriptId);
        window.app.stopScript(scriptId);
    };

    // 清空终端输出
    window.app.terminalManager.clear(scriptId);

    // 清除保存的结果
    window.app.clearScriptResults(scriptId);

    // 建立WebSocket连接
    try {
        const ws = new WebSocket(`ws://${window.location.host}/api/scripts/${scriptId}/execute`);
        window.app.activeConnections.set(scriptId, ws);

        ws.onopen = () => {
            console.log(`WebSocket连接已建立: ${scriptId}`);
            window.app.addScriptOutput(scriptId, 'stdout', `=== 开始执行: ${scriptId} ===`);

            // 发送脚本代码
            ws.send(JSON.stringify({ code: code }));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const { type, content } = data;
            window.app.addScriptOutput(scriptId, type, content);

            // 如果是退出或错误，恢复按钮状态并隐藏输入容器
            if (type === 'exit' || type === 'error') {
                const currentScriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
                if (currentScriptBlock) {
                    const currentExecuteBtn = currentScriptBlock.querySelector('.execute-btn');
                    const currentStopBtn = currentScriptBlock.querySelector('.stop-btn');

                    if (currentExecuteBtn) {
                        currentExecuteBtn.disabled = false;
                        currentExecuteBtn.textContent = '执行脚本';
                    }

                    if (currentStopBtn) {
                        currentStopBtn.disabled = true;
                    }
                }

                window.app.activeConnections.delete(scriptId);

                // 隐藏输入容器
                const inputContainer = document.getElementById(`input-container-${scriptId}`);
                if (inputContainer) {
                    inputContainer.style.display = 'none';
                }
            }
        };

        ws.onerror = (error) => {
            console.error(`WebSocket错误: ${scriptId}`, error);
            window.app.addScriptOutput(scriptId, 'error', `脚本执行错误: ${error.message || '未知错误'}`);

            const currentScriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
            if (currentScriptBlock) {
                const currentExecuteBtn = currentScriptBlock.querySelector('.execute-btn');
                const currentStopBtn = currentScriptBlock.querySelector('.stop-btn');

                if (currentExecuteBtn) {
                    currentExecuteBtn.disabled = false;
                    currentExecuteBtn.textContent = '执行脚本';
                }

                if (currentStopBtn) {
                    currentStopBtn.disabled = true;
                }
            }

            window.app.activeConnections.delete(scriptId);

            // 隐藏输入容器
            const inputContainer = document.getElementById(`input-container-${scriptId}`);
            if (inputContainer) {
                inputContainer.style.display = 'none';
            }
        };

        ws.onclose = () => {
            console.log(`WebSocket连接已关闭: ${scriptId}`);

            // 只有在脚本块还存在时才更新UI（可能被用户停止了）
            const currentScriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
            if (currentScriptBlock) {
                const currentExecuteBtn = currentScriptBlock.querySelector('.execute-btn');
                const currentStopBtn = currentScriptBlock.querySelector('.stop-btn');

                if (currentExecuteBtn) {
                    currentExecuteBtn.disabled = false;
                    currentExecuteBtn.textContent = '执行脚本';
                }

                if (currentStopBtn) {
                    currentStopBtn.disabled = true;
                }
            }

            window.app.activeConnections.delete(scriptId);

            // 隐藏输入容器
            const inputContainer = document.getElementById(`input-container-${scriptId}`);
            if (inputContainer) {
                inputContainer.style.display = 'none';
            }
        };

    } catch (error) {
        console.error(`执行脚本失败: ${scriptId}`, error);
        window.app.addScriptOutput(scriptId, 'error', `执行失败: ${error.message}`);

        const currentScriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
        if (currentScriptBlock) {
            const currentExecuteBtn = currentScriptBlock.querySelector('.execute-btn');
            const currentStopBtn = currentScriptBlock.querySelector('.stop-btn');

            if (currentExecuteBtn) {
                currentExecuteBtn.disabled = false;
                currentExecuteBtn.textContent = '执行脚本';
            }

            if (currentStopBtn) {
                currentStopBtn.disabled = true;
            }
        }

        // 隐藏输入容器
        const inputContainer = document.getElementById(`input-container-${scriptId}`);
        if (inputContainer) {
            inputContainer.style.display = 'none';
        }
    }
}

// 将函数分配给 window 对象，使其在测试环境中可以访问
window.copyCode = async function copyCode(scriptId) {
    const scriptBlock = document.querySelector(`[data-script-id="${scriptId}"]`);
    const codeElement = scriptBlock.querySelector('.script-code');
    const code = codeElement.textContent;

    try {
        await navigator.clipboard.writeText(code);
        console.log('代码已复制到剪贴板');
    } catch (err) {
        console.error('复制失败:', err);
    }
}

// 将函数分配给 window 对象，使其在测试环境中可以访问
window.sendInput = async function sendInput(scriptId) {
    const inputElement = document.getElementById(`input-${scriptId}`);
    const inputValue = inputElement.value.trim();

    if (!inputValue) {
        return;
    }

    // 获取WebSocket连接
    const ws = window.app.activeConnections.get(scriptId);
    if (!ws || ws.readyState !== (window.WebSocket?.OPEN ?? 1)) {
        console.error(`脚本 ${scriptId} 没有活动的WebSocket连接`);
        window.app.addScriptOutput(scriptId, 'error', `脚本 ${scriptId} 没有活动的WebSocket连接`);
        return;
    }

    try {
        // 发送输入消息
        ws.send(JSON.stringify({ type: "input", content: inputValue }));

        // 在输出中显示用户输入（可选）
        window.app.addScriptOutput(scriptId, 'stdin', `> ${inputValue}`);

        // 清空输入框
        inputElement.value = '';

        // 聚焦输入框以便继续输入
        inputElement.focus();

    } catch (error) {
        console.error(`发送输入失败: ${scriptId}`, error);
        window.app.addScriptOutput(scriptId, 'error', `发送输入失败: ${error.message}`);
    }
}

// 创建全局应用实例
window.app = new App();

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', async () => {
    await window.app.init();
});
