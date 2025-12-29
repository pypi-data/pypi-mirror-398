/**
 * TerminalManager 单元测试
 * 测试 xterm.js 终端管理器功能
 */

// 设置全局环境
document.body.innerHTML = `
  <div id="file-select"></div>
  <div id="current-file"></div>
  <div id="markdown-content"></div>
`;

global.fetch = jest.fn();

global.WebSocket = jest.fn(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1,
  OPEN: 1,
}));

Object.defineProperty(navigator, 'clipboard', {
  value: { writeText: jest.fn() },
  writable: true,
});

global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
};

// 模拟 ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// 模拟 xterm.js
global.Terminal = jest.fn().mockImplementation(() => {
  const mockTerm = {
    open: jest.fn(),
    write: jest.fn(),
    writeln: jest.fn(),
    clear: jest.fn(),
    reset: jest.fn(),
    dispose: jest.fn(),
    getContent: jest.fn().mockReturnValue(''),
    rows: 10,
    options: {},
    on: jest.fn(),
    onData: jest.fn(),
  };
  return mockTerm;
});

// 加载 TerminalManager
require('../../scriptbook/static/js/terminal-manager.js');

describe('TerminalManager', () => {
  let tm;

  beforeEach(() => {
    tm = new window.TerminalManager();
  });

  afterEach(() => {
    tm.disposeAll();
  });

  describe('初始化', () => {
    test('应该正确创建实例', () => {
      expect(tm).toBeInstanceOf(window.TerminalManager);
      expect(tm.terminals).toBeInstanceOf(Map);
      expect(tm.terminals.size).toBe(0);
    });
  });

  describe('createTerminal', () => {
    test('应该为指定脚本创建终端', () => {
      const container = document.createElement('div');
      const term = tm.createTerminal('script-1', container);

      expect(term).toBeDefined();
      expect(tm.terminals.has('script-1')).toBe(true);
    });

    test('应该调用终端的 open 方法', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-2', container);

      const term = tm.getTerminal('script-2');
      expect(term.open).toHaveBeenCalledWith(container);
    });

    test('应该写入占位符文本', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-3', container);

      const term = tm.getTerminal('script-3');
      expect(term.write).toHaveBeenCalled();
    });

    test('重复创建同一脚本应该先销毁旧终端', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-4', container);

      const firstTerm = tm.getTerminal('script-4');
      const disposeSpy = jest.spyOn(firstTerm, 'dispose');

      tm.createTerminal('script-4', container);

      expect(disposeSpy).toHaveBeenCalled();
    });
  });

  describe('getTerminal', () => {
    test('应该返回已创建的终端', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-5', container);

      const term = tm.getTerminal('script-5');
      expect(term).toBeDefined();
    });

    test('未创建的脚本应该返回 null', () => {
      const term = tm.getTerminal('nonexistent');
      expect(term).toBeNull();
    });
  });

  describe('write', () => {
    test('应该向终端写入内容', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-6', container);

      tm.write('script-6', 'test content');

      const term = tm.getTerminal('script-6');
      // write 现在接收 (content, callback)
      expect(term.write).toHaveBeenCalledWith('test content', expect.any(Function));
    });

    test('未创建的脚本应该不写入', () => {
      expect(() => tm.write('nonexistent', 'content')).not.toThrow();
    });
  });

  describe('writeln', () => {
    test('应该写入一行内容', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-7', container);

      const term = tm.getTerminal('script-7');
      expect(term).not.toBeNull();

      // 调用 TerminalManager 的 writeln
      tm.writeln('script-7', 'hello', 'stdout');

      // 验证终端的 write 被调用（writeln 内部使用 write）
      expect(term.write).toHaveBeenCalled();
      // 验证写入的内容格式正确（包含颜色前缀和换行）
      const writeCall = term.write.mock.calls[term.write.mock.calls.length - 1];
      expect(writeCall[0]).toContain('hello');
      expect(writeCall[0]).toContain('\r\n');
    });

    test('应该使用默认类型 stdout', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-8', container);

      const term = tm.getTerminal('script-8');
      expect(term).not.toBeNull();

      tm.writeln('script-8', 'text');

      // stdout 类型不添加颜色前缀
      expect(term.write).toHaveBeenCalled();
      const writeCall = term.write.mock.calls[term.write.mock.calls.length - 1];
      expect(writeCall[0]).toContain('text');
    });

    test('stderr 类型应该添加红色前缀', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-8a', container);

      const term = tm.getTerminal('script-8a');
      expect(term).not.toBeNull();

      tm.writeln('script-8a', 'error message', 'stderr');

      expect(term.write).toHaveBeenCalled();
      const writeCall = term.write.mock.calls[term.write.mock.calls.length - 1];
      expect(writeCall[0]).toContain('\x1b[31m'); // 红色前缀
      expect(writeCall[0]).toContain('error message');
      expect(writeCall[0]).toContain('\x1b[0m'); // 重置颜色
    });

    test('exit 类型应该添加黄色前缀', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-8b', container);

      const term = tm.getTerminal('script-8b');
      expect(term).not.toBeNull();

      tm.writeln('script-8b', '进程退出，返回码: 0', 'exit');

      expect(term.write).toHaveBeenCalled();
      const writeCall = term.write.mock.calls[term.write.mock.calls.length - 1];
      expect(writeCall[0]).toContain('\x1b[33m'); // 黄色前缀
      expect(writeCall[0]).toContain('\x1b[0m'); // 重置颜色
    });

    test('未创建的脚本应该不写入', () => {
      expect(() => tm.writeln('nonexistent', 'content')).not.toThrow();
    });
  });

  describe('clear', () => {
    test('应该清除终端内容', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-9', container);

      tm.clear('script-9');

      const term = tm.getTerminal('script-9');
      expect(term.clear).toHaveBeenCalled();
    });

    test('未创建的脚本应该不报错', () => {
      expect(() => tm.clear('nonexistent')).not.toThrow();
    });
  });

  describe('reset', () => {
    test('应该重置终端', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-10', container);

      tm.reset('script-10');

      const term = tm.getTerminal('script-10');
      expect(term.reset).toHaveBeenCalled();
    });
  });

  describe('disposeTerminal', () => {
    test('应该销毁终端并从 Map 中移除', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-11', container);

      const term = tm.getTerminal('script-11');
      const disposeSpy = jest.spyOn(term, 'dispose');

      tm.disposeTerminal('script-11');

      expect(disposeSpy).toHaveBeenCalled();
      expect(tm.terminals.has('script-11')).toBe(false);
    });

    test('销毁不存在的终端应该不报错', () => {
      expect(() => tm.disposeTerminal('nonexistent')).not.toThrow();
    });
  });

  describe('disposeAll', () => {
    test('应该销毁所有终端', () => {
      const container1 = document.createElement('div');
      const container2 = document.createElement('div');

      tm.createTerminal('script-12', container1);
      tm.createTerminal('script-13', container2);

      const term1 = tm.getTerminal('script-12');
      const term2 = tm.getTerminal('script-13');
      const disposeSpy1 = jest.spyOn(term1, 'dispose');
      const disposeSpy2 = jest.spyOn(term2, 'dispose');

      tm.disposeAll();

      expect(disposeSpy1).toHaveBeenCalled();
      expect(disposeSpy2).toHaveBeenCalled();
      expect(tm.terminals.size).toBe(0);
    });
  });

  describe('getContent', () => {
    test('应该返回终端内容', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-14', container);

      const content = tm.getContent('script-14');

      const term = tm.getTerminal('script-14');
      expect(term.getContent).toHaveBeenCalled();
      expect(content).toBe('');
    });

    test('未创建的终端返回空字符串', () => {
      const content = tm.getContent('nonexistent');
      expect(content).toBe('');
    });
  });

  describe('getRows', () => {
    test('应该返回终端行数', () => {
      const container = document.createElement('div');
      tm.createTerminal('script-15', container);

      const rows = tm.getRows('script-15');

      const term = tm.getTerminal('script-15');
      expect(term.rows).toBe(10);
      expect(rows).toBe(10);
    });

    test('未创建的终端返回 0', () => {
      const rows = tm.getRows('nonexistent');
      expect(rows).toBe(0);
    });
  });

  describe('多终端管理', () => {
    test('应该同时管理多个终端', () => {
      const container1 = document.createElement('div');
      const container2 = document.createElement('div');
      const container3 = document.createElement('div');

      tm.createTerminal('script-16', container1);
      tm.createTerminal('script-17', container2);
      tm.createTerminal('script-18', container3);

      expect(tm.terminals.size).toBe(3);

      expect(tm.getTerminal('script-16')).toBeDefined();
      expect(tm.getTerminal('script-17')).toBeDefined();
      expect(tm.getTerminal('script-18')).toBeDefined();
    });

    test('应该能独立操作每个终端', () => {
      const container1 = document.createElement('div');
      const container2 = document.createElement('div');

      tm.createTerminal('script-19', container1);
      tm.createTerminal('script-20', container2);

      tm.write('script-19', 'content1');
      tm.write('script-20', 'content2');

      const term1 = tm.getTerminal('script-19');
      const term2 = tm.getTerminal('script-20');

      expect(term1.write).toHaveBeenCalledWith('content1', expect.any(Function));
      expect(term2.write).toHaveBeenCalledWith('content2', expect.any(Function));
    });
  });
});
