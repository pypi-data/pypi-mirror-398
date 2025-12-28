import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

window.CLIPSPACE_TO_OSS_MAP = window.CLIPSPACE_TO_OSS_MAP || {};

// ═══════════════════════════════════════════════════════════════════════════
// 工具函数：查找 clipspace 文件名对应的 OSS URL
// ═══════════════════════════════════════════════════════════════════════════
function findOssUrl(filename) {
    return window.CLIPSPACE_TO_OSS_MAP[filename]
        || window.CLIPSPACE_TO_OSS_MAP[`${filename} [input]`]
        || window.CLIPSPACE_TO_OSS_MAP[`${filename} [output]`];
}

// 去掉末尾的 " [input]" 或 " [output]" 后缀
function stripTypeSuffix(value) {
    if (!value || typeof value !== 'string') return value;
    return value.replace(/\s\[(input|output)\]$/i, '');
}
// ═══════════════════════════════════════════════════════════════════════════
// 工具函数：替换 clipspace URL 为 OSS URL
// ═══════════════════════════════════════════════════════════════════════════
function replaceClipspaceUrl(urlString) {
    if (!urlString || typeof urlString !== 'string') return urlString;
    if (!urlString.includes('/view?') || !urlString.includes('clipspace')) return urlString;

    try {
        const url = new URL(urlString, window.location.origin);
        const filename = url.searchParams.get('filename');
        const subfolder = url.searchParams.get('subfolder');

        if (subfolder === 'clipspace' && filename) {
            const ossUrl = findOssUrl(filename);
            if (ossUrl) {
                url.searchParams.set('filename', ossUrl);
                url.searchParams.set('subfolder', '');
                return url.pathname + url.search;
            }
        }
    } catch (e) {
        console.error('[BizyDraft] Error replacing clipspace URL:', e);
    }

    return urlString;
}

// ═══════════════════════════════════════════════════════════════════════════
// 拦截图片加载请求，将 clipspace URL 替换为 OSS URL
// ═══════════════════════════════════════════════════════════════════════════
(function interceptImageLoading() {
    const originalSrcDescriptor = Object.getOwnPropertyDescriptor(Image.prototype, 'src');

    Object.defineProperty(Image.prototype, 'src', {
        get() {
            return originalSrcDescriptor.get.call(this);
        },
        set(value) {
            const modifiedValue = replaceClipspaceUrl(value);
            originalSrcDescriptor.set.call(this, modifiedValue);
        },
        configurable: true
    });

    const originalSetAttribute = HTMLImageElement.prototype.setAttribute;
    HTMLImageElement.prototype.setAttribute = function (name, value) {
        if (name === 'src') {
            const modifiedValue = replaceClipspaceUrl(value);
            return originalSetAttribute.call(this, name, modifiedValue);
        }
        return originalSetAttribute.call(this, name, value);
    };
})();

// ═══════════════════════════════════════════════════════════════════════════
// 拦截上传响应，保存映射并篡改返回值
// ═══════════════════════════════════════════════════════════════════════════
const originalFetchApi = api.fetchApi;
api.fetchApi = async function (url, options) {
    const response = await originalFetchApi.call(this, url, options);

    const isUploadApi = url === '/upload/image' || url === '/upload/mask'
        || url === '/api/upload/image' || url === '/api/upload/mask';

    if (!isUploadApi || !response.ok) {
        return response;
    }
    try {
        const data = await response.clone().json();

        // 检查是否是 OSS 上传响应
        const isOssUpload = data.subfolder?.includes('http://') || data.subfolder?.includes('https://')
            || data.name?.startsWith('http://') || data.name?.startsWith('https://');

        if (!isOssUpload) return response;

        // 构造完整的 OSS URL
        const ossUrl = data.subfolder?.includes('http')
            ? `${data.subfolder}/${data.name}`
            : data.name;

        // 处理映射逻辑
        let finalUrl = ossUrl;

        if (options?.body instanceof FormData) {
            const imageFile = options.body.get('image');
            if (imageFile?.name) {
                const filename = imageFile.name;
                const idMatch = filename.match(/(\d+)/);
                const baseId = idMatch?.[1];

                // 第一次 /upload/mask 的结果是涂改后的完整图片
                if (baseId && url.includes('/upload/mask')) {
                    const firstMaskKey = `__FIRST_MASK_${baseId}__`;

                    if (!window.CLIPSPACE_TO_OSS_MAP[firstMaskKey]) {
                        // 首次 mask 上传，保存到所有变体
                        window.CLIPSPACE_TO_OSS_MAP[firstMaskKey] = ossUrl;
                        finalUrl = ossUrl;

                        [`clipspace-mask-${baseId}.png`, `clipspace-paint-${baseId}.png`,
                        `clipspace-painted-${baseId}.png`, `clipspace-painted-masked-${baseId}.png`
                        ].forEach(v => window.CLIPSPACE_TO_OSS_MAP[v] = ossUrl);

                    } else {
                        // 后续 mask 上传，使用首次的 URL
                        finalUrl = window.CLIPSPACE_TO_OSS_MAP[firstMaskKey];
                    }
                } else if (baseId) {
                    // /upload/image 的上传，如果已有 mask 则使用 mask 的 URL
                    const firstMaskUrl = window.CLIPSPACE_TO_OSS_MAP[`__FIRST_MASK_${baseId}__`];
                    if (firstMaskUrl) {
                        finalUrl = firstMaskUrl;
                    }
                }

                // 保存映射
                [filename, `${filename} [input]`, `${filename} [output]`].forEach(key => {
                    window.CLIPSPACE_TO_OSS_MAP[key] = finalUrl;
                });

                const filenameWithoutSuffix = filename.replace(/ \[(input|output)\]$/, '');
                if (filenameWithoutSuffix !== filename) {
                    window.CLIPSPACE_TO_OSS_MAP[filenameWithoutSuffix] = finalUrl;
                }

            }
        }

        // 同时保存后端返回的文件名映射
        window.CLIPSPACE_TO_OSS_MAP[data.name] = finalUrl;

        // 🔧 修改 ComfyApp.clipspace，让它使用 OSS URL 而不是 clipspace 路径
        if (window.app?.constructor?.clipspace) {
            const clipspace = window.app.constructor.clipspace;

            // 修改 clipspace.images
            if (clipspace.images && clipspace.images.length > 0) {
                const clipImage = clipspace.images[clipspace.selectedIndex || 0];
                if (clipImage && clipImage.subfolder === 'clipspace') {
                    clipspace.images[clipspace.selectedIndex || 0] = {
                        filename: finalUrl,
                        subfolder: ''
                    };
                }
            }

            // 修改 clipspace.widgets
            if (clipspace.widgets) {
                const imageWidgetIndex = clipspace.widgets.findIndex(w => w.name === 'image');
                if (imageWidgetIndex >= 0) {
                    const widgetValue = clipspace.widgets[imageWidgetIndex].value;
                    if (widgetValue && typeof widgetValue === 'object' && widgetValue.subfolder === 'clipspace') {
                        clipspace.widgets[imageWidgetIndex].value = {
                            filename: finalUrl,
                            subfolder: ''
                        };
                    }
                }
            }
        }

        // 篡改响应，让 ComfyUI 使用完整的 OSS URL
        const modifiedData = { ...data, name: finalUrl, subfolder: '' };
        return new Response(JSON.stringify(modifiedData), {
            status: response.status,
            statusText: response.statusText,
            headers: response.headers
        });

    } catch (e) {
        console.error('[BizyDraft Upload] Error:', e);
        return response;
    }
};

// 转换 prompt 中的 clipspace 路径为 OSS URL
function convertClipspacePathsInPrompt(prompt) {
    if (!prompt || typeof prompt !== 'object') {
        return prompt;
    }

    for (const [nodeId, node] of Object.entries(prompt)) {
        if (!node?.inputs) continue;

        for (const [inputKey, inputValue] of Object.entries(node.inputs)) {
            if (typeof inputValue === 'string' && inputValue.includes('clipspace')) {
                // 1) 特殊情况：clipspace/https://... 或 clipspace/http://...
                const ossUrlMatch = inputValue.match(/clipspace\/(https?:\/\/[^\s]+)/i);
                if (ossUrlMatch) {
                    // 移除可能的 [input] 或 [output] 后缀
                    let cleanUrl = ossUrlMatch[1].replace(/\s*\[(input|output)\]$/i, '');
                    node.inputs[inputKey] = cleanUrl;

                    if (inputKey === 'image' && node.inputs['image_name']) {
                        node.inputs['image_name'] = cleanUrl.split('/').pop();
                    }
                } else {
                    // 2) 常规情况：clipspace/xxx.png
                    const match = inputValue.match(/clipspace\/([\w-]+\.(?:png|jpg|jpeg|webp|gif))/i);
                    if (match) {
                        const filename = match[1];
                        const ossUrl = findOssUrl(filename);

                        if (ossUrl) {
                            node.inputs[inputKey] = ossUrl;

                            if (inputKey === 'image' && node.inputs['image_name']) {
                                node.inputs['image_name'] = ossUrl.split('/').pop();
                            }
                        }
                    }
                }
            }
        }
    }

    return prompt;
}

// ═══════════════════════════════════════════════════════════════════════════
// 拦截 pasteFromClipspace，确保 widget.value 使用 OSS URL
// ═══════════════════════════════════════════════════════════════════════════
function interceptPasteFromClipspace() {
    const ComfyApp = window.app?.constructor;
    if (!ComfyApp || !ComfyApp.pasteFromClipspace) return;

    const originalPasteFromClipspace = ComfyApp.pasteFromClipspace;
    ComfyApp.pasteFromClipspace = function (node) {
        // 调用原始函数
        originalPasteFromClipspace.call(this, node);

        // 修正 widget.value
        if (node.widgets) {
            const imageWidget = node.widgets.find(w => w.name === 'image');
            if (imageWidget && typeof imageWidget.value === 'string') {
                const value = imageWidget.value;

                // 1) 如果是 clipspace 路径格式，替换为 OSS URL
                if (value.includes('clipspace/')) {
                    // 1.1) 特殊情况：clipspace/https://... 或 clipspace/http://...
                    //      这种情况是 OSS URL 被错误地加了 clipspace/ 前缀，直接移除前缀
                    const ossUrlMatch = value.match(/clipspace\/(https?:\/\/[^\s]+)/i);
                    if (ossUrlMatch) {
                        // 移除可能的 [input] 或 [output] 后缀
                        let cleanUrl = ossUrlMatch[1].replace(/\s*\[(input|output)\]$/i, '');
                        imageWidget.value = cleanUrl;
                    } else {
                        // 1.2) 常规情况：clipspace/xxx.png，提取文件名并查找映射
                        const match = value.match(/clipspace\/([\w-]+\.(?:png|jpg|jpeg|webp|gif))(\s\[(input|output)\])?/i);
                        if (match) {
                            const filename = match[1];
                            const ossUrl = findOssUrl(filename);

                            if (ossUrl) {
                                imageWidget.value = ossUrl;
                            }
                        }
                    }
                }
                // 2) 如果是 "https://... [input]" 这样的字符串，移除后缀
                else if (/https?:\/\/.*\.(png|jpg|jpeg|webp|gif)\s\[(input|output)\]$/i.test(value)) {
                    const cleaned = stripTypeSuffix(value);
                    if (cleaned !== value) {
                        imageWidget.value = cleaned;
                    }
                }
            }
        }
    };
}
// 注册 ComfyUI 扩展
app.registerExtension({
    name: "bizyair.clipspace.to.oss",

    async setup() {
        const originalGraphToPrompt = app.graphToPrompt;

        // 在构建 Prompt 之前，先清理所有 widget 的值，去掉多余的后缀和错误的 clipspace 前缀
        function sanitizeGraphWidgets(graph) {
            const nodes = graph?._nodes || [];
            for (const node of nodes) {
                if (!node?.widgets) continue;
                for (const widget of node.widgets) {
                    if (typeof widget?.value === 'string') {
                        let value = widget.value;
                        // 先处理 clipspace/https://... 格式
                        if (value.includes('clipspace/')) {
                            const ossUrlMatch = value.match(/clipspace\/(https?:\/\/[^\s]+)/i);
                            if (ossUrlMatch) {
                                value = ossUrlMatch[1];
                            }
                        }
                        // 再移除类型后缀
                        widget.value = stripTypeSuffix(value);
                    }
                }
            }
        }

        app.graphToPrompt = async function (...args) {
            // 预清理，避免 workflow.widgets_values 和 prompt 输入里包含 [input]/[output]
            try { sanitizeGraphWidgets(app.graph); } catch (e) { }

            const result = await originalGraphToPrompt.apply(this, args);

            if (result?.output) {
                // 二次清理并转换 clipspace
                const cleaned = convertClipspacePathsInPrompt(result.output);
                // 额外移除任何字符串输入中的类型后缀
                for (const nodeId of Object.keys(cleaned || {})) {
                    const node = cleaned[nodeId];
                    if (!node?.inputs) continue;
                    for (const key of Object.keys(node.inputs)) {
                        const v = node.inputs[key];
                        node.inputs[key] = typeof v === 'string' ? stripTypeSuffix(v) : v;
                    }
                }
                result.output = cleaned;
            }

            return result;
        };

        // 拦截 pasteFromClipspace
        interceptPasteFromClipspace();
    }
});
