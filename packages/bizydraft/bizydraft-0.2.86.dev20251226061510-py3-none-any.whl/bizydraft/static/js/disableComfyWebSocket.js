// 保存原始的 WebSocket 构造函数
const OriginalWebSocket = window.WebSocket;

// 保存原始的 fetch 函数
const OriginalFetch = window.fetch;

// 需要跳过的 URL 数组
const skipFetchUrls = [
  'manager/badge_mode',
  'pysssss/autocomplete'
];

class FakeWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;  // 核心：保持 CONNECTING 状态
    console.warn('[BizyDraft] 已阻止 WebSocket 连接:', url);
  }
  send() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
}

window.WebSocket = function(url, protocols) {
  //精确拦截/ws请求
  if (typeof url === 'string' && /^wss?:\/\/[^/]+\/ws(\?.*)?$/.test(url)) {
    return new FakeWebSocket(url);
  }
  // 其他连接正常创建，不影响
  return new OriginalWebSocket(url, protocols);
};

// 保留 WebSocket 的静态属性和原型
Object.setPrototypeOf(window.WebSocket, OriginalWebSocket);
window.WebSocket.prototype = OriginalWebSocket.prototype;

// 复制静态常量（使用 defineProperty 避免只读属性错误）
['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'].forEach(prop => {
  Object.defineProperty(window.WebSocket, prop, {
    value: OriginalWebSocket[prop],
    writable: false,
    enumerable: true,
    configurable: true
  });
});

// 拦截 fetch 请求
window.fetch = function(url) {
  // 将 URL 转换为字符串进行比较
  const urlString = typeof url === 'string' ? url : url.toString();
  // 检查 URL 是否在跳过列表中
  if (skipFetchUrls.some(skipUrl => urlString.includes(skipUrl))) {
    console.warn('[BizyDraft] 已阻止 fetch 请求:', urlString);
    // 返回一个模拟的 Response 对象，状态为 200
    return Promise.resolve(new Response(null, {
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'Content-Type': 'application/json' })
    }));
  }

  // 其他请求正常发送
  return OriginalFetch.apply(this, arguments);
};
