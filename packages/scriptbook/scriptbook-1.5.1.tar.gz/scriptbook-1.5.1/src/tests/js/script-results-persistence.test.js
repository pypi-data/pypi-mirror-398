/**
 * Scriptbook - 脚本执行结果持久化测试
 * 测试页面刷新后脚本执行结果是否保留
 */

describe('脚本执行结果持久化', () => {
  beforeEach(() => {
    // 清空所有模拟和localStorage
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
      <div class="script-block" data-script-id="script-1">
        <pre class="script-code"><code>echo "Hello World"</code></pre>
        <div id="output-script-1"></div>
        <button class="execute-btn">执行脚本</button>
        <button class="stop-btn" disabled>停止</button>
      </div>
      <div class="script-block" data-script-id="script-2">
        <pre class="script-code"><code>ls -la</code></pre>
        <div id="output-script-2"></div>
        <button class="execute-btn">执行脚本</button>
        <button class="stop-btn" disabled>停止</button>
      </div>
    `;
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('页面刷新后结果保留测试', () => {
    test('应该证明当前实现：页面刷新后脚本执行结果会丢失', () => {
      // 模拟脚本执行结果
      const outputElement1 = document.getElementById('output-script-1');
      const outputElement2 = document.getElementById('output-script-2');

      outputElement1.innerHTML = '<div class="output-line stdout"><span class="content">Hello World</span></div>';
      outputElement2.innerHTML = '<div class="output-line stdout"><span class="content">total 8</span></div>';

      // 验证结果存在
      expect(outputElement1.innerHTML).toContain('Hello World');
      expect(outputElement2.innerHTML).toContain('total 8');

      // 模拟页面刷新（重新加载 DOM）
      document.body.innerHTML = `
        <div class="script-block" data-script-id="script-1">
          <pre class="script-code"><code>echo "Hello World"</code></pre>
          <div id="output-script-1"><div class="output-placeholder">等待脚本执行...</div></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
        <div class="script-block" data-script-id="script-2">
          <pre class="script-code"><code>ls -la</code></pre>
          <div id="output-script-2"><div class="output-placeholder">等待脚本执行...</div></div>
          <button class="execute-btn">执行脚本</button>
          <button class="stop-btn" disabled>停止</button>
        </div>
      `;

      // 重新获取输出元素
      const newOutputElement1 = document.getElementById('output-script-1');
      const newOutputElement2 = document.getElementById('output-script-2');

      // 验证结果丢失（现在是空或只有占位符）
      expect(newOutputElement1.innerHTML).not.toContain('Hello World');
      expect(newOutputElement2.innerHTML).not.toContain('total 8');
      expect(newOutputElement1.innerHTML).toContain('output-placeholder');
      expect(newOutputElement2.innerHTML).toContain('output-placeholder');
    });

    test('应该证明localStorage可以实现结果保留', () => {
      // 模拟脚本执行结果
      const scriptResults = {
        'script-1': [
          { type: 'stdout', content: 'Hello World', timestamp: '2025-12-22T10:00:00' },
        ],
        'script-2': [
          { type: 'stdout', content: 'total 8', timestamp: '2025-12-22T10:00:00' },
        ],
      };

      // 保存到localStorage
      localStorage.setItem(
        `scriptResults_${global.window.app.currentFile}`,
        JSON.stringify(scriptResults)
      );

      // 验证localStorage中保存了数据
      const saved = localStorage.getItem(`scriptResults_${global.window.app.currentFile}`);
      expect(saved).toBeTruthy();
      expect(JSON.parse(saved)).toEqual(scriptResults);

      // 模拟页面刷新后恢复数据
      const restoredResults = JSON.parse(
        localStorage.getItem(`scriptResults_${global.window.app.currentFile}`)
      );

      // 验证数据可以恢复
      expect(restoredResults['script-1']).toEqual([
        { type: 'stdout', content: 'Hello World', timestamp: '2025-12-22T10:00:00' },
      ]);
      expect(restoredResults['script-2']).toEqual([
        { type: 'stdout', content: 'total 8', timestamp: '2025-12-22T10:00:00' },
      ]);
    });

    test('应该验证localStorage的存储键格式', () => {
      const testFile = 'example.md';
      const key = `scriptResults_${testFile}`;

      // 测试键名格式
      expect(key).toBe('scriptResults_example.md');

      // 测试不同文件名
      const key2 = `scriptResults_test-file.md`;
      expect(key2).toBe('scriptResults_test-file.md');

      // 测试中文文件名
      const key3 = `scriptResults_测试文档.md`;
      expect(key3).toBe('scriptResults_测试文档.md');
    });

    test('应该验证localStorage的数据结构', () => {
      const fileName = 'test.md';
      const scriptId1 = 'script-1';
      const scriptId2 = 'script-2';

      // 构建结果数据结构
      const results = {
        [scriptId1]: [
          { type: 'stdout', content: '输出1', timestamp: '2025-12-22T10:00:00' },
          { type: 'stderr', content: '错误1', timestamp: '2025-12-22T10:01:00' },
        ],
        [scriptId2]: [
          { type: 'exit', content: '退出码: 0', timestamp: '2025-12-22T10:02:00' },
        ],
      };

      // 保存数据
      localStorage.setItem(`scriptResults_${fileName}`, JSON.stringify(results));

      // 恢复数据
      const restored = JSON.parse(localStorage.getItem(`scriptResults_${fileName}`));

      // 验证数据结构
      expect(restored).toHaveProperty(scriptId1);
      expect(restored).toHaveProperty(scriptId2);
      expect(Array.isArray(restored[scriptId1])).toBe(true);
      expect(restored[scriptId1].length).toBe(2);
      expect(restored[scriptId1][0]).toHaveProperty('type');
      expect(restored[scriptId1][0]).toHaveProperty('content');
      expect(restored[scriptId1][0]).toHaveProperty('timestamp');
    });

    test('应该验证空结果的保存和恢复', () => {
      const fileName = 'empty.md';
      const emptyResults = {};

      // 保存空结果
      localStorage.setItem(`scriptResults_${fileName}`, JSON.stringify(emptyResults));

      // 恢复并验证
      const restored = JSON.parse(localStorage.getItem(`scriptResults_${fileName}`));
      expect(restored).toEqual({});
      expect(Object.keys(restored).length).toBe(0);
    });

    test('应该验证不同文件的结果独立保存', () => {
      const file1 = 'file1.md';
      const file2 = 'file2.md';

      const results1 = { 'script-1': [{ type: 'stdout', content: 'File1 Output' }] };
      const results2 = { 'script-1': [{ type: 'stdout', content: 'File2 Output' }] };

      // 分别保存两个文件的结果
      localStorage.setItem(`scriptResults_${file1}`, JSON.stringify(results1));
      localStorage.setItem(`scriptResults_${file2}`, JSON.stringify(results2));

      // 验证数据独立
      const restored1 = JSON.parse(localStorage.getItem(`scriptResults_${file1}`));
      const restored2 = JSON.parse(localStorage.getItem(`scriptResults_${file2}`));

      expect(restored1['script-1'][0].content).toBe('File1 Output');
      expect(restored2['script-1'][0].content).toBe('File2 Output');
      expect(restored1['script-1'][0].content).not.toBe(restored2['script-1'][0].content);
    });
  });

  describe('localStorage 兼容性测试', () => {
    test('应该验证localStorage在测试环境中可用', () => {
      // 验证 localStorage 存在
      expect(localStorage).toBeDefined();
      expect(typeof localStorage.setItem).toBe('function');
      expect(typeof localStorage.getItem).toBe('function');
      expect(typeof localStorage.removeItem).toBe('function');

      // 测试基本操作
      localStorage.setItem('test', 'value');
      expect(localStorage.getItem('test')).toBe('value');
      localStorage.removeItem('test');
      expect(localStorage.getItem('test')).toBeNull();
    });

    test('应该验证JSON序列化', () => {
      const data = {
        nested: { value: 123 },
        array: [1, 2, 3],
        string: 'test',
        boolean: true,
        nullValue: null,
      };

      const serialized = JSON.stringify(data);
      const deserialized = JSON.parse(serialized);

      expect(deserialized).toEqual(data);
      expect(deserialized.nested.value).toBe(123);
      expect(deserialized.array).toEqual([1, 2, 3]);
      expect(deserialized.boolean).toBe(true);
      expect(deserialized.nullValue).toBeNull();
    });

    test('应该验证存储限制和清理', () => {
      // 存储大量数据
      const largeData = 'x'.repeat(10000);
      localStorage.setItem('large', largeData);

      expect(localStorage.getItem('large').length).toBe(10000);

      // 清理数据
      localStorage.removeItem('large');
      expect(localStorage.getItem('large')).toBeNull();

      // 清空所有数据
      localStorage.setItem('key1', 'value1');
      localStorage.setItem('key2', 'value2');
      localStorage.clear();

      expect(localStorage.getItem('key1')).toBeNull();
      expect(localStorage.getItem('key2')).toBeNull();
    });
  });
});
