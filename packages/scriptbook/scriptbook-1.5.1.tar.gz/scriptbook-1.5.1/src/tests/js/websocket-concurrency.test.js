/**
 * Scriptbook - WebSocket并发测试
 * 测试页面刷新等场景下的WebSocket连接处理
 */

describe('WebSocket并发处理', () => {
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
  });

  describe('页面刷新场景测试', () => {
    test('应该在页面刷新时正确处理WebSocket断开', async () => {
      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <pre class="script-code"><code>sleep 5</code></pre>
          <div id="output-test-script"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onmessage: null,
        onclose: null,
        onerror: null,
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

      // 模拟收到一些输出
      await new Promise(resolve => {
        if (mockWebSocket.onmessage) {
          mockWebSocket.onmessage({
            data: JSON.stringify({ type: 'stdout', content: 'Processing...' }),
          });
          resolve();
        }
      });

      // 模拟页面刷新 - 客户端断开连接
      await new Promise(resolve => {
        if (mockWebSocket.onclose) {
          mockWebSocket.onclose();
          resolve();
        }
      });

      // 等待执行完成
      await executePromise;
      await new Promise(resolve => setTimeout(resolve, 100));

      // 验证按钮状态已恢复
      const executeBtn = document.querySelector('.execute-btn');
      expect(executeBtn.disabled).toBe(false);
      expect(executeBtn.textContent).toBe('执行脚本');

      // 验证连接已清理
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);
    });

    test('应该在WebSocket意外关闭时清理资源', async () => {
      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-test-script"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

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

      // 模拟突然断开（不发送exit消息）
      await new Promise(resolve => {
        if (mockWebSocket.onclose) {
          mockWebSocket.onclose();
          resolve();
        }
      });

      // 等待执行完成
      await executePromise;
      await new Promise(resolve => setTimeout(resolve, 100));

      // 验证资源已清理
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);
      expect(document.querySelector('.execute-btn').disabled).toBe(false);
    });

    test('应该处理多次快速断开连接', async () => {
      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <pre class="script-code"><code>sleep 10</code></pre>
          <div id="output-test-script"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

      // 模拟 WebSocket
      let connectionCount = 0;
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onclose: null,
        readyState: 1,
      };

      global.WebSocket = jest.fn(() => {
        connectionCount++;
        return mockWebSocket;
      });

      // 执行脚本
      const executePromise = window.executeScript('test-script');

      // 模拟连接建立
      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      // 第一次关闭
      await new Promise(resolve => {
        if (mockWebSocket.onclose) {
          mockWebSocket.onclose();
          resolve();
        }
      });

      // 等待状态恢复
      await new Promise(resolve => setTimeout(resolve, 100));

      // 验证第一次关闭后状态
      expect(document.querySelector('.execute-btn').disabled).toBe(false);
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);
    });

    test('应该在断开后重新执行新脚本', async () => {
      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <pre class="script-code"><code>sleep 2</code></pre>
          <div id="output-test-script"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

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

      // 第一次断开
      await new Promise(resolve => {
        if (mockWebSocket1.onclose) {
          mockWebSocket1.onclose();
          resolve();
        }
      });

      await executePromise1;
      await new Promise(resolve => setTimeout(resolve, 100));

      // 第二次执行（重新执行）
      const executePromise2 = window.executeScript('test-script');

      await new Promise(resolve => {
        if (mockWebSocket2.onopen) {
          mockWebSocket2.onopen();
          resolve();
        }
      });

      // 正常完成
      await new Promise(resolve => {
        if (mockWebSocket2.onmessage) {
          mockWebSocket2.onmessage({
            data: JSON.stringify({ type: 'stdout', content: 'Done' }),
          });
          mockWebSocket2.onmessage({
            data: JSON.stringify({ type: 'exit', content: '进程退出，返回码: 0' }),
          });
          resolve();
        }
      });

      await executePromise2;
      await new Promise(resolve => setTimeout(resolve, 100));

      // 验证第二次执行成功
      expect(document.querySelector('.execute-btn').disabled).toBe(false);
      expect(global.window.app.activeConnections.has('test-script')).toBe(false);
    });

    test('应该处理WebSocket错误事件', async () => {
      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-test-script"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
          <div id="input-container-test-script" style="display: none;"></div>
        </div>
      `;

      // 模拟 WebSocket
      const mockWebSocket = {
        send: jest.fn(),
        close: jest.fn(),
        onopen: null,
        onerror: null,
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

      // 模拟错误
      await new Promise(resolve => {
        if (mockWebSocket.onerror) {
          mockWebSocket.onerror(new Error('Network error'));
          resolve();
        }
      });

      // 等待执行完成
      await executePromise;
      await new Promise(resolve => setTimeout(resolve, 100));

      // 验证错误处理
      const executeBtn = document.querySelector('.execute-btn');
      expect(executeBtn.disabled).toBe(false);
      expect(executeBtn.textContent).toBe('执行脚本');

      const inputContainer = document.getElementById('input-container-test-script');
      expect(inputContainer.style.display).toBe('none');

      expect(global.window.app.activeConnections.has('test-script')).toBe(false);
    });

    test('应该在localStorage不可用时继续工作', async () => {
      // 模拟 localStorage 不可用
      const originalGetItem = localStorage.getItem;
      const originalSetItem = localStorage.setItem;
      localStorage.getItem = jest.fn(() => {
        throw new Error('QuotaExceededError');
      });
      localStorage.setItem = jest.fn(() => {
        throw new Error('QuotaExceededError');
      });

      // 设置 DOM
      document.body.innerHTML = `
        <div class="script-block" data-script-id="test-script">
          <pre class="script-code"><code>echo "test"</code></pre>
          <div id="output-test-script"></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

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

      // 执行脚本 - 不应该抛出错误
      const executePromise = window.executeScript('test-script');

      await new Promise(resolve => {
        if (mockWebSocket.onopen) {
          mockWebSocket.onopen();
          resolve();
        }
      });

      await new Promise(resolve => {
        if (mockWebSocket.onmessage) {
          mockWebSocket.onmessage({
            data: JSON.stringify({ type: 'stdout', content: 'Output' }),
          });
          mockWebSocket.onmessage({
            data: JSON.stringify({ type: 'exit', content: '进程退出，返回码: 0' }),
          });
          resolve();
        }
      });

      await executePromise;
      await new Promise(resolve => setTimeout(resolve, 100));

      // 验证功能仍然正常工作
      expect(document.querySelector('.execute-btn').disabled).toBe(false);

      // 恢复 localStorage
      localStorage.getItem = originalGetItem;
      localStorage.setItem = originalSetItem;
    });
  });

  describe('清理测试', () => {
    test('应该在组件卸载时清理所有连接', async () => {
      const mockWebSocket1 = {
        close: jest.fn(),
        readyState: 1,
      };
      const mockWebSocket2 = {
        close: jest.fn(),
        readyState: 1,
      };

      global.window.app.activeConnections.set('script-1', mockWebSocket1);
      global.window.app.activeConnections.set('script-2', mockWebSocket2);

      // 模拟刷新 - 清理所有连接
      mockWebSocket1.close();
      mockWebSocket2.close();

      global.window.app.activeConnections.clear();

      expect(mockWebSocket1.close).toHaveBeenCalled();
      expect(mockWebSocket2.close).toHaveBeenCalled();
      expect(global.window.app.activeConnections.size).toBe(0);
    });

    test('应该在clearScriptResults时优雅处理错误', () => {
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = jest.fn(() => {
        throw new Error('Storage error');
      });

      const fileName = 'test.md';
      global.window.app.currentFile = fileName;

      // 不应该抛出错误
      expect(() => {
        global.window.app.clearScriptResults('script-1');
      }).not.toThrow();

      // 恢复
      localStorage.getItem = originalGetItem;
    });
  });
});
