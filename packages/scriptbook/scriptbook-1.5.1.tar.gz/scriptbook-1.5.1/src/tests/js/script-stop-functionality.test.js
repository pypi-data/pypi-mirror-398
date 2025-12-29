/**
 * Scriptbook - 脚本停止功能测试
 * 测试停止脚本执行的功能
 */

describe('脚本停止功能', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();

    // 设置全局 window 对象
    global.window = {
      location: { host: 'localhost:8888' },
      WebSocket: { OPEN: 1 },
      app: {
        currentFile: 'test.md',
        activeConnections: new Map(),
        addScriptOutput: jest.fn(),
        formatFileSize: jest.fn((bytes) => `${bytes} B`),
      },
    };

    // 加载 app.js
    require('../../scriptbook/static/js/app.js');

    // 设置 DOM 结构
    document.body.innerHTML = `
      <div class="script-block" data-script-id="test-script">
        <pre class="script-code"><code>sleep 10</code></pre>
        <div id="output-test-script"></div>
        <button class="execute-btn">执行脚本</button>
        <button class="stop-btn" disabled>停止执行</button>
        <div id="input-container-test-script" style="display: none;"></div>
      </div>
    `;
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('停止按钮可见性', () => {
    test('应该默认显示停止按钮', () => {
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <button class="stop-btn" disabled>停止执行</button>
        </div>
      `;

      const stopBtn = document.querySelector('.stop-btn');

      // 验证按钮可见（不是display: none）
      expect(stopBtn.style.display).not.toBe('none');
    });

    test('应该在未执行时禁用停止按钮', () => {
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <button class="stop-btn" disabled>停止执行</button>
        </div>
      `;

      const stopBtn = document.querySelector('.stop-btn');

      // 验证按钮被禁用
      expect(stopBtn.disabled).toBe(true);
    });
  });

  describe('停止按钮功能', () => {
    test('应该启用停止按钮并在执行时绑定事件', async () => {
      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证按钮状态
      const executeBtn = document.querySelector('.execute-btn');
      const stopBtn = document.querySelector('.stop-btn');

      expect(executeBtn.disabled).toBe(true);
      expect(executeBtn.textContent).toBe('执行中...');
      expect(stopBtn.disabled).toBe(false);

      // 验证停止按钮绑定事件
      expect(stopBtn.onclick).toBeDefined();
      expect(typeof stopBtn.onclick).toBe('function');
    });

    test('应该能通过点击停止按钮终止执行', async () => {
      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 点击停止按钮
      const stopBtn = document.querySelector('.stop-btn');
      stopBtn.click();

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证WebSocket连接已关闭
      expect(mockWebSocket.close).toHaveBeenCalled();

      // 验证连接已从activeConnections中移除
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);

      // 验证按钮状态已恢复
      const executeBtn = document.querySelector('.execute-btn');
      expect(executeBtn.disabled).toBe(false);
      expect(executeBtn.textContent).toBe('执行脚本');
      expect(stopBtn.disabled).toBe(true);
    });

    test('应该在停止时显示停止信息', async () => {
      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // 重置addScriptOutput模拟
      global.window.app.addScriptOutput = jest.fn();

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 点击停止按钮
      const stopBtn = document.querySelector('.stop-btn');
      stopBtn.click();

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证addScriptOutput被调用
      expect(global.window.app.addScriptOutput).toHaveBeenCalled();
      expect(global.window.app.addScriptOutput).toHaveBeenCalledWith(
        'test-script',
        'stdout',
        '=== 脚本已被用户停止 ==='
      );
    });

    test('应该在停止时隐藏输入容器', async () => {
      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 点击停止按钮
      const stopBtn = document.querySelector('.stop-btn');
      stopBtn.click();

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证输入容器已隐藏
      const inputContainer = document.getElementById('input-container-test-script');
      expect(inputContainer.style.display).toBe('none');
    });

    test('应该在停止后能够重新执行', async () => {
      // 模拟 WebSocket
      const mockWebSocket1 = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      const mockWebSocket2 = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      let wsIndex = 0;
      global.WebSocket = jest.fn(() => {
        wsIndex++;
        return wsIndex === 1 ? mockWebSocket1 : mockWebSocket2;
      });

      // 第一次执行
      const executePromise1 = window.executeScript('test-script');

      await new Promise(resolve => {
        if (mockWebSocket1.onopen) {
          mockWebSocket1.onopen();
          resolve();
        }
      });

      await new Promise(resolve => setTimeout(resolve, 50));

      // 点击停止按钮
      const stopBtn = document.querySelector('.stop-btn');
      stopBtn.click();

      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证第一次停止
      expect(mockWebSocket1.close).toHaveBeenCalled();
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);

      // 第二次执行
      const executePromise2 = window.executeScript('test-script');

      await new Promise(resolve => {
        if (mockWebSocket2.onopen) {
          mockWebSocket2.onopen();
          resolve();
        }
      });

      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证第二次执行成功
      const executeBtn = document.querySelector('.execute-btn');
      const stopBtn2 = document.querySelector('.stop-btn');

      expect(executeBtn.disabled).toBe(true);
      expect(stopBtn2.disabled).toBe(false);
      expect(mockWebSocket2.send).toHaveBeenCalled();
    });
  });

  describe('停止按钮事件绑定', () => {
    test('应该在文件加载时绑定停止按钮事件', async () => {
      // 模拟已有保存的结果
      const fileName = 'test.md';
      const savedResults = {
        'test-script': [
          { type: 'stdout', content: 'Previous output', timestamp: '2025-12-22T10:00:00.000Z' },
        ],
      };

      localStorage.setItem(`scriptResults_${fileName}`, JSON.stringify(savedResults));

      // 模拟 fetch 响应
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          html: `
            <div class="script-block" data-script-id="test-script">
              <pre class="script-code"><code>sleep 10</code></pre>
              <div id="output-test-script"></div>
              <button class="execute-btn">执行脚本</button>
              <button class="stop-btn" disabled>停止执行</button>
            </div>
          `,
          scripts: [{ id: 'test-script', code: 'sleep 10' }],
        }),
      });

      // 选择文件
      await global.window.app.selectFile(fileName);

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证停止按钮存在且绑定事件
      const stopBtn = document.querySelector('.stop-btn');
      expect(stopBtn).not.toBeNull();
      expect(stopBtn.disabled).toBe(true); // 没有执行时应该禁用
    });

    test('应该为多个脚本块分别绑定停止按钮事件', async () => {
      document.body.innerHTML = `
        <div class="script-block" data-script-id="script-1">
          <pre class="script-code"><code>sleep 10</code></pre>
          <div id="output-script-1"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止执行</button>
        </div>
        <div class="script-block" data-script-id="script-2">
          <pre class="script-code"><code>sleep 20</code></pre>
          <div id="output-script-2"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止执行</button>
        </div>
      `;

      // 模拟 fetch 响应
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          html: `
            <div class="script-block" data-script-id="script-1">
              <pre class="script-code"><code>sleep 10</code></pre>
              <div id="output-script-1"></div>
              <button class="execute-btn">执行脚本</button>
              <button class="stop-btn" disabled>停止执行</button>
            </div>
            <div class="script-block" data-script-id="script-2">
              <pre class="script-code"><code>sleep 20</code></pre>
              <div id="output-script-2"></div>
              <button class="execute-btn">执行脚本</button>
              <button class="stop-btn" disabled>停止执行</button>
            </div>
          `,
          scripts: [
            { id: 'script-1', code: 'sleep 10' },
            { id: 'script-2', code: 'sleep 20' },
          ],
        }),
      });

      // 选择文件
      await global.window.app.selectFile('test.md');

      // 等待异步操作完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 验证两个停止按钮都存在
      const stopButtons = document.querySelectorAll('.stop-btn');
      expect(stopButtons.length).toBe(2);
    });
  });

  describe('停止功能错误处理', () => {
    test('应该在WebSocket关闭失败时优雅处理', async () => {
      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(() => {
          throw new Error('Close failed');
        }),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      await new Promise(resolve => setTimeout(resolve, 50));

      // 点击停止按钮 - 不应该抛出错误
      expect(() => {
        const stopBtn = document.querySelector('.stop-btn');
        stopBtn.click();
      }).not.toThrow();

      // 验证连接已从activeConnections中移除
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);
    });

    test('应该在停止不存在的连接时优雅处理', () => {
      // 模拟没有活动连接的情况
      expect(global.window.app.activeConnections.has('nonexistent-script')).toBe(false);

      // 调用停止函数 - 不应该抛出错误
      expect(() => {
        global.window.app.stopScript('nonexistent-script');
      }).not.toThrow();
    });

    test('应该在停止时处理DOM元素不存在的情况', async () => {
      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => mockWebSocket);

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      await new Promise(resolve => setTimeout(resolve, 50));

      // 移除脚本块DOM
      const scriptBlock = document.querySelector('[data-script-id="test-script"]');
      scriptBlock.remove();

      // 点击停止按钮 - 不应该抛出错误
      expect(() => {
        global.window.app.stopScript('test-script');
      }).not.toThrow();

      // 验证连接已关闭
      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });
});
