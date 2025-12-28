// 统一的配置加载器 - 合并 model.js 和 media.js 的配置请求
// 只发送一次 API 请求，同时获取 weight_load_nodes 和 media_load_nodes

// 统一的配置缓存
let fullConfigCache = null;
let configLoadPromise = null;

// API配置（统一使用一个域名，根据实际需要调整）
const CONFIG_API_URL = 'https://bizyair.cn/api/special/comfyagent_node_config?t=' + Math.floor(Date.now() / 60000);

// 获取完整配置的API函数（返回包含 weight_load_nodes 和 media_load_nodes 的完整对象）
export async function fetchFullConfig() {
    if (fullConfigCache) {
        return fullConfigCache;
    }

    if (configLoadPromise) {
        return configLoadPromise;
    }

    configLoadPromise = (async () => {
        try {
            console.log('正在从API获取完整节点配置...');
            const response = await fetch(CONFIG_API_URL, { credentials: 'include' });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.code === 20000 && result.data) {
                fullConfigCache = {
                    weight_load_nodes: result.data.weight_load_nodes || {},
                    media_load_nodes: result.data.media_load_nodes || {}
                };
                console.log('完整配置加载成功:', {
                    weight_nodes: Object.keys(fullConfigCache.weight_load_nodes).length,
                    media_nodes: Object.keys(fullConfigCache.media_load_nodes).length
                });
                return fullConfigCache;
            } else {
                throw new Error('API返回数据格式不正确');
            }
        } catch (error) {
            console.error('获取完整配置失败:', error);
            fullConfigCache = null;
            return null;
        }
    })();

    return configLoadPromise;
}

// 获取模型节点配置（从完整配置中提取 weight_load_nodes）
export async function fetchNodeConfig() {
    const fullConfig = await fetchFullConfig();
    return fullConfig ? fullConfig.weight_load_nodes : null;
}

// 获取媒体节点配置（从完整配置中提取 media_load_nodes）
export async function fetchMediaConfig() {
    const fullConfig = await fetchFullConfig();
    return fullConfig ? fullConfig.media_load_nodes : null;
}

// 启动时后台预取（不阻塞后续逻辑）
try { void fetchFullConfig(); } catch (e) { /* noop */ }
