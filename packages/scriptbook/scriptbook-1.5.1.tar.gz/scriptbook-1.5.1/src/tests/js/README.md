# SOP Online JavaScript 单元测试

本目录包含 SOP Online 前端 JavaScript 代码的单元测试。

## 测试结构

```
src/tests/js/
├── app.test.js           # app.js 的单元测试
├── package.json          # 测试依赖和脚本
├── setup.js              # Jest 设置文件
├── __mocks__/
│   └── styleMock.js      # 样式文件模拟
└── README.md             # 本文档
```

## 测试覆盖范围

### App 类测试
- ✅ 初始化测试
- ✅ `bindEvents()` 方法
- ✅ `loadFileList()` 方法
- ✅ `updateFileSelect()` 方法
- ✅ `selectFile()` 方法
- ✅ `addScriptOutput()` 方法
- ✅ `formatFileSize()` 方法

### 全局函数测试
- ✅ `executeScript()` 函数
  - WebSocket 连接创建
  - 代码发送
  - 输入容器显示
  - 现有连接关闭
  - 错误处理
- ✅ `copyCode()` 函数
  - 代码复制到剪贴板
- ✅ `sendInput()` 函数
  - 输入发送
  - 空输入处理
  - WebSocket 连接检查
  - 输入框清空

### WebSocket 事件测试
- ✅ 消息接收处理
- ✅ 退出消息处理
- ✅ 错误消息处理
- ✅ 输入容器显示/隐藏

## 运行测试

### 安装依赖

```bash
cd src/tests/js
npm install
```

### 运行所有测试

```bash
npm test
```

### 监视模式

```bash
npm run test:watch
```

### 生成覆盖率报告

```bash
npm run test:coverage
```

## 测试技术栈

- **Jest 29.7.0**: JavaScript 测试框架
- **babel-jest**: Babel 集成
- **jest-environment-jsdom**: DOM 环境模拟
- **@babel/preset-env**: ES6+ 支持

## 测试环境配置

### JSDOM
测试使用 JSDOM 模拟浏览器环境，包括：
- DOM 操作
- 事件处理
- WebSocket 模拟
- Clipboard API 模拟

### Mock 功能
- `fetch()` API
- `WebSocket` 构造器
- `navigator.clipboard`
- 样式文件

## 测试用例示例

### 基本测试结构

```javascript
describe('功能名称', () => {
  test('应该执行预期行为', () => {
    // 准备测试数据
    // 执行被测试的代码
    // 验证结果
    expect(actualResult).toBe(expectedResult);
  });
});
```

### 异步测试

```javascript
test('应该处理异步操作', async () => {
  const result = await someAsyncFunction();
  expect(result).toBe(expectedValue);
});
```

### DOM 测试

```javascript
test('应该更新DOM', () => {
  document.body.innerHTML = '<div id="test"></div>';
  updateElement('test', '新内容');
  expect(document.getElementById('test').textContent).toBe('新内容');
});
```

## 最佳实践

### 1. 测试隔离
- 每个测试使用独立的 DOM
- 在 `beforeEach` 中清理状态
- 使用 `jest.clearAllMocks()` 重置模拟

### 2. 描述性测试名称
- 使用清晰的测试描述
- 包含预期行为和条件

### 3. 单一职责
- 每个测试只验证一个功能点
- 避免过度测试实现细节

### 4. 模拟外部依赖
- 模拟 API 调用
- 模拟 WebSocket 连接
- 模拟浏览器 API

## 持续集成

测试可以在 CI/CD 流水线中运行：

```yaml
# .github/workflows/js-tests.yml
name: JavaScript Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd src/tests/js && npm install
      - name: Run tests
        run: cd src/tests/js && npm test
```

## 故障排除

### 常见问题

1. **模块加载错误**
   - 检查 `require()` 路径是否正确
   - 确保 `setup.js` 正确配置

2. **DOM 相关错误**
   - 确认在测试前设置了 DOM
   - 检查元素选择器是否正确

3. **异步测试超时**
   - 使用 `async/await` 和 `await`
   - 增加超时时间或使用 `done` 回调

4. **Mock 不工作**
   - 检查 `jest.clearAllMocks()` 调用位置
   - 确认模拟在测试前设置

### 调试技巧

```javascript
// 启用详细日志
console.log = console.error = console.warn = console.info = console.debug = console.trace = console.dir = console.dirxml = console.table = console.assert = console.count = console.countReset = console.time = console.timeEnd = console.timeLog = console.profile = console.profileEnd = console.command = console.error = console.warn = console.info = console.debug = console.trace = console.assert = console.count = console.countReset = console.time = console.timeEnd = console.timeLog = console.profileEnd = (msg) => {
  throw new Error(msg);
};
```

## 添加新测试

1. 确定要测试的功能
2. 创建新的 `describe` 块
3. 编写测试用例
4. 运行测试确保通过
5. 更新覆盖率报告

## 性能考虑

- 避免在测试中进行大量 DOM 操作
- 使用 `beforeAll` 而不是 `beforeEach` 当可能时
- 合理使用 `mockClear()` 和 `mockReset()`