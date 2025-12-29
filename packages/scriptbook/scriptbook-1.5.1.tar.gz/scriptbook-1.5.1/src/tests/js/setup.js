// Jest 设置文件
// 在每个测试之前设置全局环境

// 模拟 DOM 环境
document.body.innerHTML = `
  <div id="file-select"></div>
  <div id="current-file"></div>
  <div id="markdown-content"></div>
`;

// 模拟 fetch
global.fetch = jest.fn();

// 模拟 WebSocket
global.WebSocket = jest.fn(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1,
  OPEN: 1,
}));

// 模拟 Clipboard API
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn(),
  },
  writable: true,
});

// 模拟 console
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
};

// 模拟 xterm.js 的 Terminal 类
global.Terminal = jest.fn().mockImplementation(() => ({
  open: jest.fn(),
  write: jest.fn(),
  writeln: jest.fn(),
  clear: jest.fn(),
  reset: jest.fn(),
  dispose: jest.fn(),
  onData: jest.fn(),
  getContent: jest.fn().mockReturnValue(''),
  rows: 10,
  options: {},
}));

// 模拟 TerminalManager 类
window.TerminalManager = class TerminalManager {
  constructor() {
    this.terminals = new Map();
  }

  createTerminal(scriptId, container) {
    const term = {
      open: jest.fn(),
      write: jest.fn(),
      writeln: jest.fn(),
      clear: jest.fn(),
      reset: jest.fn(),
      dispose: jest.fn(),
      onData: jest.fn(),
      getContent: jest.fn().mockReturnValue(''),
      rows: 10,
      options: {},
    };
    this.terminals.set(scriptId, { term });
    return term;
  }

  getTerminal(scriptId) {
    const terminal = this.terminals.get(scriptId);
    return terminal ? terminal.term : null;
  }

  write(scriptId, content) {
    const term = this.getTerminal(scriptId);
    if (term) term.write(content);
  }

  writeln(scriptId, content, type) {
    const term = this.getTerminal(scriptId);
    if (term) term.writeln(content, type);
  }

  clear(scriptId) {
    const term = this.getTerminal(scriptId);
    if (term) term.clear();
  }

  reset(scriptId) {
    const term = this.getTerminal(scriptId);
    if (term) term.reset();
  }

  disposeTerminal(scriptId) {
    this.terminals.delete(scriptId);
  }

  disposeAll() {
    this.terminals.clear();
  }
};