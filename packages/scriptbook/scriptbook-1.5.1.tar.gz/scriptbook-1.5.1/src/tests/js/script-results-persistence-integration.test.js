/**
 * Scriptbook - 脚本执行结果持久化集成测试
 * 测试实际的文件选择和结果恢复功能
 */

describe('脚本结果持久化集成测试', () => {
  beforeEach(() => {
    // 清空所有模拟和localStorage
    jest.clearAllMocks();
    localStorage.clear();

    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
      WebSocket: { OPEN: 1 },
      app: {
        currentFile: null,
        activeConnections: new Map(),
        addScriptOutput: jest.fn(),
        formatFileSize: jest.fn((bytes) => `${bytes} B`),
      },
    };

    // 加载 app.js
    require('../../scriptbook/static/js/app.js');

    // 设置 DOM 结构
    document.body.innerHTML = `
      <div id="file-select"></div>
      <div id="current-file"></div>
      <div id="markdown-content"></div>
    `;
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('文件选择和结果恢复', () => {
    test('应该在新选择文件时恢复保存的结果', async () => {
      // 模拟已有保存的结果
      const fileName = 'test.md';
      const savedResults = {
        'script-1': [
          { type: 'stdout', content: 'Hello World', timestamp: '2025-12-22T10:00:00.000Z' },
          { type: 'exit', content: '进程退出，返回码: 0', timestamp: '2025-12-22T10:00:01.000Z' },
        ],
      };

      localStorage.setItem(`scriptResults_${fileName}`, JSON.stringify(savedResults));

      // 模拟 fetch 响应，包含脚本块HTML
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          html: `
            <div class="script-block" data-script-id="script-1">
              <pre class="script-code"><code>echo "Hello World"</code></pre>
              <div id="output-script-1"></div>
            </div>
          `,
          scripts: [{ id: 'script-1', code: 'echo "Hello World"' }],
        }),
      });

      // 选择文件
      await global.window.app.selectFile(fileName);

      // 验证 currentFile 已设置
      expect(global.window.app.currentFile).toBe(fileName);

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证终端已创建
      const term = global.window.app.terminalManager.getTerminal('script-1');
      expect(term).not.toBeNull();
      // 验证恢复结果时终端的 writeln 被调用
      expect(term.writeln).toHaveBeenCalledWith('Hello World', 'stdout');
      // 验证包含退出信息（可能有不同的返回码）
      const writelnCalls = term.writeln.mock.calls;
      const exitCall = writelnCalls.find(call => call[0].includes('进程退出'));
      expect(exitCall).toBeDefined();
    });

    test('应该在没有保存结果时不恢复', async () => {
      const fileName = 'new-file.md';

      // 没有保存任何结果
      expect(localStorage.getItem(`scriptResults_${fileName}`)).toBeNull();

      // 模拟 fetch 响应，包含脚本块HTML
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          html: `
            <div class="script-block" data-script-id="script-1">
              <pre class="script-code"><code>echo "test"</code></pre>
              <div id="output-script-1"></div>
            </div>
          `,
          scripts: [{ id: 'script-1', code: 'echo "test"' }],
        }),
      });

      // 选择文件
      await global.window.app.selectFile(fileName);

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证终端已创建
      const term = global.window.app.terminalManager.getTerminal('script-1');
      expect(term).not.toBeNull();
      // 没有保存结果，writeln 不会被调用（占位符用 write 不是 writeln）
      expect(term.writeln).not.toHaveBeenCalled();
    });

    test('应该在清空后重新执行时清除保存的结果', async () => {
      const fileName = 'test.md';
      const scriptId = 'script-1';

      // 模拟已有保存的结果
      const savedResults = {
        [scriptId]: [
          { type: 'stdout', content: 'Old Output', timestamp: '2025-12-22T10:00:00.000Z' },
        ],
      };

      localStorage.setItem(`scriptResults_${fileName}`, JSON.stringify(savedResults));

      // 设置 DOM
      document.body.innerHTML += `
        <div class="script-block" data-script-id="${scriptId}">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-${scriptId}"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

      // 设置 currentFile
      global.window.app.currentFile = fileName;

      // 验证结果已保存
      expect(JSON.parse(localStorage.getItem(`scriptResults_${fileName}`))[scriptId]).toHaveLength(1);

      // 模拟执行脚本（调用 clearScriptResults）
      global.window.app.clearScriptResults(scriptId);

      // 验证结果已清除
      const results = JSON.parse(localStorage.getItem(`scriptResults_${fileName}`) || '{}');
      expect(results[scriptId]).toBeUndefined();
    });

    test('应该保存新的输出到localStorage', async () => {
      const fileName = 'test.md';
      const scriptId = 'script-1';

      global.window.app.currentFile = fileName;

      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="${scriptId}">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-${scriptId}"></div>
        </div>
      `;

      // 添加输出
      global.window.app.addScriptOutput(scriptId, 'stdout', 'New Output');

      // 验证已保存到localStorage
      const saved = localStorage.getItem(`scriptResults_${fileName}`);
      expect(saved).toBeTruthy();

      const results = JSON.parse(saved);
      expect(results[scriptId]).toBeDefined();
      expect(results[scriptId]).toHaveLength(1);
      expect(results[scriptId][0].type).toBe('stdout');
      expect(results[scriptId][0].content).toBe('New Output');
      expect(results[scriptId][0].timestamp).toBeTruthy();
    });

    test('应该在不同文件间保持结果独立', async () => {
      const fileName1 = 'file1.md';
      const fileName2 = 'file2.md';
      const scriptId = 'script-1';

      // 为第一个文件保存结果
      const results1 = {
        [scriptId]: [{ type: 'stdout', content: 'File1 Output', timestamp: '2025-12-22T10:00:00.000Z' }],
      };
      localStorage.setItem(`scriptResults_${fileName1}`, JSON.stringify(results1));

      // 为第二个文件保存结果
      const results2 = {
        [scriptId]: [{ type: 'stdout', content: 'File2 Output', timestamp: '2025-12-22T10:00:00.000Z' }],
      };
      localStorage.setItem(`scriptResults_${fileName2}`, JSON.stringify(results2));

      // 模拟 fetch 响应
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          html: `
            <div class="script-block" data-script-id="${scriptId}">
              <pre class="script-code"><code>echo "test"</code></pre>
              <div id="output-${scriptId}"></div>
            </div>
          `,
          scripts: [{ id: scriptId, code: 'echo "test"' }],
        }),
      });

      // 选择第一个文件
      global.window.app.currentFile = fileName1;
      await global.window.app.selectFile(fileName1);

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 恢复结果
      global.window.app.restoreScriptResults();

      // 验证终端显示第一个文件的结果
      const term1 = global.window.app.terminalManager.getTerminal(scriptId);
      expect(term1).not.toBeNull();
      // 验证 File1 Output 被写入
      const calls1 = term1.writeln.mock.calls;
      const file1Call = calls1.find(call => call[0] === 'File1 Output');
      expect(file1Call).toBeDefined();

      // 模拟第二个文件
      document.body.innerHTML = `
        <div class="script-block" data-script-id="${scriptId}">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-${scriptId}"></div>
        </div>
      `;

      // 选择第二个文件
      global.window.app.currentFile = fileName2;
      await global.window.app.selectFile(fileName2);

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 恢复结果
      global.window.app.restoreScriptResults();

      // 验证终端显示第二个文件的结果
      const term2 = global.window.app.terminalManager.getTerminal(scriptId);
      expect(term2).not.toBeNull();
      // 新终端实例，验证新的 writeln 调用
      const calls2 = term2.writeln.mock.calls;
      const file2Call = calls2.find(call => call[0] === 'File2 Output');
      expect(file2Call).toBeDefined();
    });
  });

  describe('localStorage 错误处理', () => {
    test('应该在localStorage不可用时优雅处理', () => {
      // 模拟 localStorage 不可用
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = jest.fn(() => {
        throw new Error('QuotaExceededError');
      });

      const fileName = 'test.md';
      global.window.app.currentFile = fileName;

      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="script-1">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-script-1"></div>
        </div>
      `;

      // 不应该抛出错误
      expect(() => {
        global.window.app.addScriptOutput('script-1', 'stdout', 'test');
      }).not.toThrow();

      // 恢复 localStorage
      localStorage.getItem = originalGetItem;
    });

    test('应该在恢复结果时处理无效JSON', () => {
      const fileName = 'test.md';
      global.window.app.currentFile = fileName;

      // 保存无效JSON
      localStorage.setItem(`scriptResults_${fileName}`, 'invalid json');

      // 不应该抛出错误
      expect(() => {
        global.window.app.restoreScriptResults();
      }).not.toThrow();
    });
  });
});
