/**
 * PluginLoader JavaScript Unit Tests
 * 测试 plugin-loader.js 中的主题管理功能
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

describe('PluginLoader 类', () => {
  beforeEach(() => {
    // 清空所有模拟
    jest.clearAllMocks();
    localStorageMock.clear();

    // 加载 plugin-loader.js (这会创建 window.pluginLoader)
    require('../../scriptbook/static/js/plugin-loader.js');
  });

  describe('初始化', () => {
    test('应该创建 PluginLoader 实例', () => {
      expect(global.window.pluginLoader).toBeDefined();
      expect(global.window.pluginLoader).toBeInstanceOf(Object);
    });

    test('应该从 localStorage 读取保存的主题', () => {
      localStorageMock.setItem('scriptbook_theme', 'theme-dark');
      // 重新加载模块以测试构造函数
      jest.resetModules();
      require('../../scriptbook/static/js/plugin-loader.js');

      expect(global.window.pluginLoader.activeTheme).toBe('theme-dark');
    });

    test('应该在没有保存的主题时使用默认主题', () => {
      jest.resetModules();
      require('../../scriptbook/static/js/plugin-loader.js');

      expect(global.window.pluginLoader.activeTheme).toBe('theme-light');
    });

    test('应该初始化 plugins 为空数组', () => {
      expect(global.window.pluginLoader.plugins).toEqual([]);
    });

    test('应该初始化 loadedStylesheets 为空数组', () => {
      expect(global.window.pluginLoader.loadedStylesheets).toEqual([]);
    });
  });

  describe('restoreTheme 方法', () => {
    test('应该恢复保存的主题', () => {
      localStorageMock.setItem('scriptbook_theme', 'theme-dark');

      const switchThemeSpy = jest.spyOn(global.window.pluginLoader, 'switchTheme');

      global.window.pluginLoader.restoreTheme();

      expect(switchThemeSpy).toHaveBeenCalledWith('theme-dark');
    });

    test('应该在没有保存的主题时恢复默认主题', () => {
      const switchThemeSpy = jest.spyOn(global.window.pluginLoader, 'switchTheme');

      global.window.pluginLoader.restoreTheme();

      expect(switchThemeSpy).toHaveBeenCalledWith('theme-light');
    });

    test('应该更新选择器的值', () => {
      // 创建 mock select 元素
      const mockSelect = {
        value: '',
        appendChild: jest.fn(),
      };
      document.getElementById = jest.fn(() => mockSelect);

      localStorageMock.setItem('scriptbook_theme', 'theme-dark');

      global.window.pluginLoader.restoreTheme();

      expect(mockSelect.value).toBe('theme-dark');
    });
  });

  describe('switchTheme 方法', () => {
    test('应该保存主题到 localStorage', () => {
      global.window.pluginLoader.switchTheme('theme-dark');

      expect(localStorage.setItem).toHaveBeenCalledWith('scriptbook_theme', 'theme-dark');
    });

    test('应该切换到默认主题时保存 theme-light', () => {
      global.window.pluginLoader.switchTheme('theme-light');

      expect(localStorage.setItem).toHaveBeenCalledWith('scriptbook_theme', 'theme-light');
    });

    test('应该更新 activeTheme 属性为暗色主题', () => {
      // 先设置一个不同的主题
      global.window.pluginLoader.activeTheme = 'theme-light';
      // 设置 plugins 数组
      global.window.pluginLoader.plugins = [{ name: 'theme-dark', description: '暗色主题' }];

      // 设置 mock DOM 方法
      const mockLink = { setAttribute: jest.fn(), parentNode: { removeChild: jest.fn() } };
      const mockHead = { appendChild: jest.fn() };
      document.createElement = jest.fn(() => mockLink);
      document.querySelectorAll = jest.fn(() => []);
      Object.defineProperty(document, 'head', { value: mockHead, writable: true });
      Object.defineProperty(document, 'body', { value: { style: {} }, writable: true });
      const mainEl = { style: {} };
      document.querySelector = jest.fn(() => mainEl);

      global.window.pluginLoader.switchTheme('theme-dark');

      expect(global.window.pluginLoader.activeTheme).toBe('theme-dark');
    });
  });

  describe('loadPlugins 方法', () => {
    test('应该成功加载插件列表', async () => {
      const mockPlugins = [
        { name: 'theme-light', description: '默认主题' },
        { name: 'theme-dark', description: '暗色主题' },
      ];

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlugins,
      });

      const plugins = await global.window.pluginLoader.loadPlugins();

      expect(fetch).toHaveBeenCalledWith('/api/plugins');
      expect(plugins).toEqual(mockPlugins);
      expect(global.window.pluginLoader.plugins).toEqual(mockPlugins);
    });

    test('应该在加载失败时返回空数组', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const plugins = await global.window.pluginLoader.loadPlugins();

      expect(plugins).toEqual([]);
    });
  });

  describe('bindEvents 方法', () => {
    test('应该为选择器绑定 change 事件', () => {
      const mockSelect = {
        addEventListener: jest.fn(),
      };
      document.getElementById = jest.fn(() => mockSelect);

      global.window.pluginLoader.bindEvents();

      expect(mockSelect.addEventListener).toHaveBeenCalledWith('change', expect.any(Function));
    });
  });
});

describe('PluginLoader 主题持久化集成', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
  });

  test('页面刷新后应该恢复之前选择的主题', () => {
    // 第一次选择暗色主题
    localStorageMock.setItem('scriptbook_theme', 'theme-dark');

    jest.resetModules();
    require('../../scriptbook/static/js/plugin-loader.js');

    // 验证构造函数读取了 localStorage
    expect(global.window.pluginLoader.activeTheme).toBe('theme-dark');
  });

  test('切换主题后应该保存新的选择', () => {
    jest.resetModules();
    require('../../scriptbook/static/js/plugin-loader.js');

    // 设置 mock DOM 方法
    const mockLink = { setAttribute: jest.fn(), parentNode: { removeChild: jest.fn() } };
    document.createElement = jest.fn(() => mockLink);
    document.querySelectorAll = jest.fn(() => []);
    document.head = { appendChild: jest.fn() };
    document.body.style = {};
    const mainEl = { style: {} };
    document.querySelector = jest.fn(() => mainEl);

    global.window.pluginLoader.switchTheme('theme-dark');

    expect(localStorage.setItem).toHaveBeenCalledWith('scriptbook_theme', 'theme-dark');
  });

  test('主题选择应该持久化并在下次访问时恢复', () => {
    // 模拟用户切换到暗色主题
    jest.resetModules();
    require('../../scriptbook/static/js/plugin-loader.js');

    // 设置 mock
    const mockLink = { setAttribute: jest.fn(), parentNode: { removeChild: jest.fn() } };
    document.createElement = jest.fn(() => mockLink);
    document.querySelectorAll = jest.fn(() => []);
    document.head = { appendChild: jest.fn() };
    document.body.style = {};
    const mainEl = { style: {} };
    document.querySelector = jest.fn(() => mainEl);

    // 切换主题
    global.window.pluginLoader.switchTheme('theme-dark');

    // 验证 localStorage 被设置
    expect(localStorage.getItem('scriptbook_theme')).toBe('theme-dark');

    // 模拟刷新 - 重新加载模块
    jest.resetModules();
    require('../../scriptbook/static/js/plugin-loader.js');

    // 验证构造函数读取了保存的主题
    expect(global.window.pluginLoader.activeTheme).toBe('theme-dark');
  });
});
