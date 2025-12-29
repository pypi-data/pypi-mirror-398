// 调试测试
const { JSDOM } = require('jsdom');

const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`);
global.window = dom.window;
global.document = dom.window.document;

// 设置 WebSocket 常量
global.WebSocket = {
  OPEN: 1,
  CONNECTING: 0,
  CLOSED: 3,
};

// 加载 app.js
require('../../scriptbook/static/js/app.js');

console.log('window.executeScript:', typeof window.executeScript);
console.log('window.sendInput:', typeof window.sendInput);
console.log('window.WebSocket.OPEN:', window.WebSocket.OPEN);

// 测试 sendInput
document.body.innerHTML = '<input type="text" id="input-test" value="test" />';

window.app.activeConnections.set('test', {
  send: function(msg) { console.log('Send called with:', msg); },
  readyState: 1,
});

window.sendInput('test');

console.log('Input value after sendInput:', document.getElementById('input-test').value);
