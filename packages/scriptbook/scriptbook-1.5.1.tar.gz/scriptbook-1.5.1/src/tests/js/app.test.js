/**
 * Scriptbook Frontend - JavaScript Unit Tests
 * 测试 app.js 中的所有功能
 */

// 模拟 localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => { store[key] = value.toString(); }),
    removeItem: jest.fn((key) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
    get store() { return store; }
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true
});

// 在每个测试前清空 localStorage
beforeEach(() => {
  localStorageMock.clear();
});

describe('App 类', () => {
  // 在每个测试前加载 app.js
  beforeEach(() => {
    // 清空所有模拟
    jest.clearAllMocks();

    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
    };

    // 加载 app.js (这会创建 window.app)
    require('../../scriptbook/static/js/app.js');

    // 加载后，window.app 应该已经创建
  });

  describe('初始化', () => {
    test('应该创建 App 实例', () => {
      expect(global.window.app).toBeDefined();
      expect(global.window.app).toBeInstanceOf(Object);
    });

    test('应该初始化 currentFile 为 null', () => {
      expect(global.window.app.currentFile).toBeNull();
    });

    test('应该初始化 activeConnections 为空 Map', () => {
      expect(global.window.app.activeConnections).toBeInstanceOf(Map);
      expect(global.window.app.activeConnections.size).toBe(0);
    });
  });

  describe('bindEvents 方法', () => {
    test('应该为文件选择器绑定 change 事件', () => {
      const fileSelect = document.getElementById('file-select');
      const addEventListenerSpy = jest.spyOn(fileSelect, 'addEventListener');

      // 直接调用已存在的 window.app 的方法
      global.window.app.bindEvents();

      expect(addEventListenerSpy).toHaveBeenCalledWith('change', expect.any(Function));
    });
  });

  describe('loadFileList 方法', () => {
    test('应该成功加载文件列表', async () => {
      const mockFiles = [
        { name: 'file1.md', size: 100 },
        { name: 'file2.md', size: 200 },
      ];

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ files: mockFiles }),
      });

      const files = await global.window.app.loadFileList();

      expect(fetch).toHaveBeenCalledWith('/api/markdown/files');
      expect(files).toEqual(mockFiles);
      expect(global.window.app.fileList).toEqual(mockFiles);
    });

    test('应该在加载失败时处理错误', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const showErrorSpy = jest.spyOn(global.window.app, 'showError');

      await global.window.app.loadFileList();

      expect(showErrorSpy).toHaveBeenCalledWith(expect.stringContaining('Network error'));
    });
  });

  describe('updateFileSelect 方法', () => {
    test('应该更新文件选择器的选项', () => {
      const fileSelect = document.getElementById('file-select');

      const mockFiles = [
        { name: 'file1.md', size: 100 },
        { name: 'file2.md', size: 200 },
      ];

      global.window.app.updateFileSelect(mockFiles);

      expect(fileSelect.children.length).toBe(2);
      expect(fileSelect.children[0].value).toBe('file1.md');
      expect(fileSelect.children[1].value).toBe('file2.md');
    });

    test('应该在没有文件时显示提示信息', () => {
      const fileSelect = document.getElementById('file-select');

      global.window.app.updateFileSelect([]);

      expect(fileSelect.children[0].textContent).toContain('没有找到markdown文件');
    });
  });

  describe('selectFile 方法', () => {
    test('应该成功选择并加载文件', async () => {
      const mockData = {
        html: '<h1>测试文档</h1>',
        scripts: [],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      await global.window.app.selectFile('test.md');

      expect(global.window.app.currentFile).toBe('test.md');
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/markdown/render?file=test.md'),
        expect.any(Object)
      );
    });

    test('应该将选择的文件保存到 localStorage', async () => {
      const mockData = {
        html: '<h1>测试文档</h1>',
        scripts: [],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      await global.window.app.selectFile('test.md');

      expect(localStorage.setItem).toHaveBeenCalledWith('scriptbook_currentFile', 'test.md');
    });

    test('应该在空文件名时不执行操作', async () => {
      await global.window.app.selectFile('');

      expect(fetch).not.toHaveBeenCalled();
    });

    test('应该在加载失败时处理错误', async () => {
      fetch.mockRejectedValueOnce(new Error('File not found'));

      const showErrorSpy = jest.spyOn(global.window.app, 'showError');

      await global.window.app.selectFile('nonexistent.md');

      expect(showErrorSpy).toHaveBeenCalledWith(expect.stringContaining('File not found'));
    });
  });

  describe('addScriptOutput 方法', () => {
    test('应该向输出区域添加内容', () => {
      // 设置 DOM - 需要有 script-block 结构
      const scriptBlock = document.createElement('div');
      scriptBlock.className = 'script-block';
      scriptBlock.dataset.scriptId = 'test-script';
      scriptBlock.innerHTML = `
        <pre class="script-code"></pre>
        <div id="output-test-script"></div>
      `;
      document.body.appendChild(scriptBlock);

      // 先创建终端
      global.window.app.createTerminalForScript('test-script');

      global.window.app.addScriptOutput('test-script', 'stdout', '测试输出');

      // 验证终端的 writeln 方法被调用
      const term = global.window.app.terminalManager.getTerminal('test-script');
      expect(term).not.toBeNull();
      expect(term.writeln).toHaveBeenCalledWith('测试输出', 'stdout');
    });

    test('应该处理不同类型的输出', () => {
      const scriptBlock = document.createElement('div');
      scriptBlock.className = 'script-block';
      scriptBlock.dataset.scriptId = 'test-script2';
      scriptBlock.innerHTML = `
        <pre class="script-code"></pre>
        <div id="output-test-script2"></div>
      `;
      document.body.appendChild(scriptBlock);

      // 先创建终端
      global.window.app.createTerminalForScript('test-script2');

      global.window.app.addScriptOutput('test-script2', 'stderr', '错误信息');
      global.window.app.addScriptOutput('test-script2', 'stdin', '> 用户输入');

      // 验证终端的 writeln 方法被调用
      const term = global.window.app.terminalManager.getTerminal('test-script2');
      expect(term).not.toBeNull();
      expect(term.writeln).toHaveBeenCalledWith('错误信息', 'stderr');
      expect(term.writeln).toHaveBeenCalledWith('> 用户输入', 'stdin');
    });
  });

  describe('formatFileSize 方法', () => {
    test('应该正确格式化文件大小', () => {
      expect(global.window.app.formatFileSize(0)).toBe('0 B');
      expect(global.window.app.formatFileSize(1024)).toBe('1 KB');
      expect(global.window.app.formatFileSize(1048576)).toBe('1 MB');
      expect(global.window.app.formatFileSize(1073741824)).toBe('1 GB');
    });
  });

  describe('文档持久化', () => {
    test('选择文件时应该保存到 localStorage', async () => {
      const mockData = {
        html: '<h1>测试文档</h1>',
        scripts: [],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      await global.window.app.selectFile('test.md');

      expect(localStorage.setItem).toHaveBeenCalledWith('scriptbook_currentFile', 'test.md');
    });
  });
});

describe('文档持久化集成', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
  });

  test('页面刷新后应该恢复之前选择的文档', async () => {
    // 设置保存的文件
    localStorageMock.setItem('scriptbook_currentFile', 'test.md');

    jest.resetModules();
    require('../../scriptbook/static/js/app.js');

    // Mock DOM elements
    document.body.innerHTML = `
      <select id="file-select"></select>
      <span id="current-file"></span>
      <div id="markdown-content"></div>
    `;

    const mockData = {
      html: '<h1>测试文档</h1>',
      scripts: [],
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [{ name: 'test.md', size: 100 }] }),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    // 调用 init
    await global.window.app.init();

    // 验证选择了保存的文件
    expect(global.window.app.currentFile).toBe('test.md');
  });

  test('如果没有保存的文档，应该选择第一个文件', async () => {
    jest.resetModules();
    require('../../scriptbook/static/js/app.js');

    // Mock DOM elements
    document.body.innerHTML = `
      <select id="file-select"></select>
      <span id="current-file"></span>
      <div id="markdown-content"></div>
    `;

    const mockData = {
      html: '<h1>第一个文档</h1>',
      scripts: [],
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [{ name: 'first.md', size: 100 }] }),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    // 调用 init
    await global.window.app.init();

    // 验证选择了第一个文件
    expect(global.window.app.currentFile).toBe('first.md');
  });

  test('如果保存的文档不存在，应该选择第一个文件', async () => {
    // 设置一个不存在的文件
    localStorageMock.setItem('scriptbook_currentFile', 'nonexistent.md');

    jest.resetModules();
    require('../../scriptbook/static/js/app.js');

    // Mock DOM elements
    document.body.innerHTML = `
      <select id="file-select"></select>
      <span id="current-file"></span>
      <div id="markdown-content"></div>
    `;

    const mockData = {
      html: '<h1>第一个文档</h1>',
      scripts: [],
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ files: [{ name: 'first.md', size: 100 }] }),
    });
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    // 调用 init
    await global.window.app.init();

    // 验证选择了第一个文件（因为保存的不存在）
    expect(global.window.app.currentFile).toBe('first.md');
  });
});

describe('全局函数 - executeScript', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
      WebSocket: { OPEN: 1 }, // 添加 WebSocket 常量
    };
    // 加载 app.js (会创建 window.app 和全局函数)
    require('../../scriptbook/static/js/app.js');

    document.body.innerHTML = `
      <div class="script-block" data-script-id="test-script">
        <pre class="script-code"><code>echo "test"</code></pre>
        <div id="output-test-script"></div>
        <button class="execute-btn">执行脚本</button>
        <button class="stop-btn" disabled>停止</button>
      </div>
    `;
  });

  test('应该成功执行脚本', async () => {
    // 模拟 WebSocket
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      onclose: null,
      addEventListener: jest.fn(function(event, callback) {
        // 将事件处理器保存到对应的属性上
        if (event === 'open') {
          this.onopen = callback;
        } else if (event === 'message') {
          this.onmessage = callback;
        } else if (event === 'close') {
          this.onclose = callback;
        }
      }),
      readyState: 1,
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    // 执行脚本
    const executePromise = window.executeScript('test-script');

    // 手动触发事件
    mockWebSocket.onopen();
    mockWebSocket.onmessage({ data: JSON.stringify({ type: 'stdout', content: 'test output' }) });
    mockWebSocket.onclose();

    // 等待执行完成
    await executePromise;
    await new Promise(resolve => setTimeout(resolve, 50));

    // 验证代码被发送
    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({ code: 'echo "test"' })
    );
  });

  test('应该在输入框中显示输入容器', async () => {
    document.body.innerHTML += '<div id="input-container-test-script"></div>';

    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn((event, callback) => {
        if (event === 'open') setTimeout(callback, 0);
        if (event === 'close') setTimeout(callback, 10);
      }),
      readyState: 1,
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    await window.executeScript('test-script');

    // 等待异步操作完成
    await new Promise(resolve => setTimeout(resolve, 50));

    const inputContainer = document.getElementById('input-container-test-script');
    expect(inputContainer.style.display).toBe('flex');
  });

  test('应该关闭现有连接', async () => {
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      readyState: 1,
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    // 创建应用实例并模拟已有连接
    global.window.app.activeConnections.set('test-script', mockWebSocket);

    await window.executeScript('test-script');

    // 验证旧连接被关闭
    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  test('应该在错误时恢复UI状态', async () => {
    document.body.innerHTML += '<div id="input-container-test-script" style="display: flex;"></div>';

    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onerror: null,
      addEventListener: jest.fn(function(event, callback) {
        if (event === 'error') {
          this.onerror = callback;
        }
      }),
      readyState: 1,
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    // 执行脚本
    const executePromise = window.executeScript('test-script');

    // 手动触发错误事件，传递错误对象
    mockWebSocket.onerror(new Error('Test error'));

    // 等待执行完成
    await executePromise;
    await new Promise(resolve => setTimeout(resolve, 50));

    const executeBtn = document.querySelector('.execute-btn');
    expect(executeBtn.disabled).toBe(false);
    expect(executeBtn.textContent).toBe('执行脚本');

    const inputContainer = document.getElementById('input-container-test-script');
    expect(inputContainer.style.display).toBe('none');
  });
});

describe('全局函数 - copyCode', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
    };
    // 加载 app.js
    require('../../scriptbook/static/js/app.js');

    document.body.innerHTML = `
      <div class="script-block" data-script-id="test-script">
        <pre class="script-code"><code>echo "test code"</code></pre>
      </div>
    `;
  });

  test('应该成功复制代码到剪贴板', async () => {
    await window.copyCode('test-script');

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('echo "test code"');
  });
});

describe('全局函数 - sendInput', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
      WebSocket: { OPEN: 1 }, // 添加 WebSocket 常量
    };
    // 加载 app.js
    require('../../scriptbook/static/js/app.js');

    document.body.innerHTML = `
      <input type="text" id="input-test-script" value="test input" />
      <div class="script-block" data-script-id="test-script">
        <div id="output-test-script"></div>
      </div>
    `;
  });

  test('应该成功发送输入', async () => {
    const mockWebSocket = {
      send: jest.fn(),
      readyState: 1, // OPEN 状态
    };

    // 模拟 activeConnections 和 addScriptOutput
    global.window.app.activeConnections = new Map([['test-script', mockWebSocket]]);
    global.window.app.addScriptOutput = jest.fn();

    await window.sendInput('test-script');

    // 等待异步操作完成
    await new Promise(resolve => setTimeout(resolve, 10));

    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'input', content: 'test input' })
    );
    expect(global.window.app.addScriptOutput).toHaveBeenCalledWith(
      'test-script',
      'stdin',
      '> test input'
    );
  });

  test('应该在空输入时不发送', async () => {
    document.getElementById('input-test-script').value = '';

    const mockWebSocket = {
      send: jest.fn(),
      readyState: 1,
    };

    global.window.app.activeConnections = new Map([['test-script', mockWebSocket]]);
    global.window.app.addScriptOutput = jest.fn();

    await window.sendInput('test-script');

    expect(mockWebSocket.send).not.toHaveBeenCalled();
  });

  test('应该在没有WebSocket连接时显示错误', async () => {
    global.window.app.activeConnections = new Map();
    global.window.app.addScriptOutput = jest.fn();

    // 记录调用前的状态
    const initialCallCount = global.window.app.addScriptOutput.mock.calls.length;

    await window.sendInput('test-script');

    // 等待异步操作完成
    await new Promise(resolve => setTimeout(resolve, 50));

    // 验证 addScriptOutput 被调用
    expect(global.window.app.addScriptOutput).toHaveBeenCalled();
    expect(global.window.app.addScriptOutput.mock.calls.length).toBeGreaterThan(initialCallCount);
    expect(global.window.app.addScriptOutput).toHaveBeenCalledWith(
      'test-script',
      'error',
      expect.stringContaining('没有活动的WebSocket连接')
    );
  });

  test('应该在输入后清空输入框', async () => {
    const mockWebSocket = {
      send: jest.fn(),
      readyState: 1,
    };

    global.window.app.activeConnections = new Map([['test-script', mockWebSocket]]);
    global.window.app.addScriptOutput = jest.fn();

    await window.sendInput('test-script');

    // 等待异步操作完成
    await new Promise(resolve => setTimeout(resolve, 10));

    const inputElement = document.getElementById('input-test-script');
    expect(inputElement.value).toBe('');
  });
});

describe('WebSocket 事件处理', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
      WebSocket: { OPEN: 1 }, // 添加 WebSocket 常量
    };
    // 加载 app.js
    require('../../scriptbook/static/js/app.js');

    document.body.innerHTML = `
      <div class="script-block" data-script-id="test-script">
        <pre class="script-code"><code>echo "test"</code></pre>
        <div id="output-test-script"></div>
        <button class="execute-btn">执行脚本</button>
        <button class="stop-btn" disabled>停止</button>
        <div id="input-container-test-script" style="display: none;"></div>
      </div>
    `;
  });

  test('应该在收到 exit 消息时隐藏输入容器', async () => {
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      addEventListener: jest.fn(function(event, callback) {
        if (event === 'open') {
          this.onopen = callback;
        } else if (event === 'message') {
          this.onmessage = callback;
        }
      }),
      readyState: 1,
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    // 清空 activeConnections
    global.window.app.activeConnections.clear();

    // 执行脚本
    const executePromise = window.executeScript('test-script');

    // 手动触发事件
    mockWebSocket.onopen();
    mockWebSocket.onmessage({ data: JSON.stringify({ type: 'exit', content: '完成' }) });

    // 等待执行完成
    await executePromise;
    await new Promise(resolve => setTimeout(resolve, 50));

    const inputContainer = document.getElementById('input-container-test-script');
    expect(inputContainer.style.display).toBe('none');
  });

  test('应该在收到 error 消息时隐藏输入容器', async () => {
    const mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      addEventListener: jest.fn(function(event, callback) {
        if (event === 'open') {
          this.onopen = callback;
        } else if (event === 'message') {
          this.onmessage = callback;
        }
      }),
      readyState: 1,
    };

    global.WebSocket = jest.fn(() => mockWebSocket);

    // 清空 activeConnections
    global.window.app.activeConnections.clear();

    // 执行脚本
    const executePromise = window.executeScript('test-script');

    // 手动触发事件
    mockWebSocket.onopen();
    mockWebSocket.onmessage({ data: JSON.stringify({ type: 'error', content: '错误' }) });

    // 等待执行完成
    await executePromise;
    await new Promise(resolve => setTimeout(resolve, 50));

    const inputContainer = document.getElementById('input-container-test-script');
    expect(inputContainer.style.display).toBe('none');
  });
});