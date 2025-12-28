// 媒体节点配置获取与工具函数（与 hookLoad/model.js 结构一致，面向 media_load_nodes）
import { fetchMediaConfig } from './configLoader.js'
import { getCookie, computeExt, hideWidget } from '../tool.js'

// 动态配置缓存（仅缓存媒体部分）
let mediaConfigCache = null;
let mediaConfigLoadPromise = null;

export const mediaNodeList = [
    'LoadImage',
    'LoadImageMask',
    'LoadAudio',
    'LoadVideo',
    'Load3D',
    'VHS_LoadVideo',
    'VHS_LoadAudioUpload'
]
// 常见的媒体输入字段名（作为回退匹配）
export const possibleMediaWidgetNames = [
    "image",
    "file",
    "audio",
    "video",
    "model_file"
];

// 获取媒体配置的API函数（使用共享配置加载器）
export async function fetchMediaConfigWithCache() {
    if (mediaConfigCache) return mediaConfigCache;
    if (mediaConfigLoadPromise) return mediaConfigLoadPromise;

    mediaConfigLoadPromise = (async () => {
        const config = await fetchMediaConfig();
        if (config) {
            mediaConfigCache = config;
        }
        return config;
    })();

    return mediaConfigLoadPromise;
}

// 根据节点名称获取媒体节点配置（仅使用缓存，不阻塞返回；触发后台预取）
export async function getMediaNodeConfig(nodeName) {
    // 后台触发一次预取
    if (!mediaConfigLoadPromise) { try { void fetchMediaConfigWithCache(); } catch (e) {} }

    if (mediaConfigCache && mediaConfigCache[nodeName]) {
        return { nodeName, config: mediaConfigCache[nodeName] };
    }
    return null;
}

// 从媒体配置中提取此节点的输入键（过滤 disable_comfyagent）
export function getMediaInputKeys(mediaNodeConfig) {
    if (!mediaNodeConfig || !mediaNodeConfig.config || !mediaNodeConfig.config.inputs) return [];
    const inputs = mediaNodeConfig.config.inputs;
    const keys = [];
    for (const key of Object.keys(inputs)) {
        const cfg = inputs[key];
        if (cfg && !cfg.disable_comfyagent) keys.push(key);
    }
    return keys;
}


export async function computeIsMediaNode(nodeName) {
    if (mediaNodeList.includes(nodeName)) {
        return true;
    }

    // 2. 检查media_load_nodes的keys
    const config = await fetchMediaConfigWithCache();
    if (config) {
        if (config.hasOwnProperty(nodeName)) {
            return true;
        }
    }

    return false;
}

// 启动时后台预取（不阻塞后续逻辑）
try { void fetchMediaConfigWithCache(); } catch (e) {}

// ==================== 媒体 Widget 处理函数 ====================

/**
 * 查找单个媒体 widget（用于 media_widget）
 */
export function findMediaWidget(nodeWidgets, apiInputKeys) {
    // 优先使用 API 配置的 keys
    if (apiInputKeys && apiInputKeys.length > 0) {
        for (const key of apiInputKeys) {
            const w = nodeWidgets.find(x => x.name === key);
            if (w) return w;
        }
    }
    // 回退到常见媒体 widget 名称
    return nodeWidgets.find(w => possibleMediaWidgetNames.includes(w.name)) || null;
}

/**
 * 查找所有媒体 widget（用于 va_widgets）
 */
export function findMediaWidgets(nodeWidgets, apiInputKeys) {
    const widgets = [];

    // 优先使用 API 配置的 keys
    if (apiInputKeys && apiInputKeys.length > 0) {
        for (const key of apiInputKeys) {
            const w = nodeWidgets.find(x => x.name === key);
            if (w) widgets.push(w);
        }
    }

    // 如果 API 配置没找到，使用回退逻辑
    if (widgets.length === 0) {
        for (const widgetName of possibleMediaWidgetNames) {
            const w = nodeWidgets.find(x => x.name === widgetName);
            if (w) widgets.push(w);
        }
    }

    return widgets;
}

/**
 * 添加新文件到列表并更新相关数据
 */
export function addNewFileToList(url, image_list, urlToNameMap, nameToItemMap) {
    const fileName = url.split('/').pop();
    const newItem = { name: fileName, url: url };
    image_list.push(newItem);
    urlToNameMap.set(url, fileName);
    nameToItemMap.set(fileName, newItem);
    return fileName;
}

/**
 * 更新所有相关 widget 的选项列表
 */
export function updateWidgetsOptions(widgets, image_list) {
    const names = image_list.map(item => item.name);
    widgets.forEach(widget => {
        if (widget && widget.options) {
            widget.options.values = names;
        }
    });
}

/**
 * 处理新上传的文件：添加到列表并更新所有 widget
 */
export function handleNewUploadedFile(url, image_list, urlToNameMap, nameToItemMap, image_name_widget, actualMediaWidget) {
    const fileName = addNewFileToList(url, image_list, urlToNameMap, nameToItemMap);

    // 更新所有相关 widget 的选项列表
    const widgetsToUpdate = [image_name_widget, actualMediaWidget].filter(Boolean);
    updateWidgetsOptions(widgetsToUpdate, image_list);

    return fileName;
}

/**
 * 从输入中提取 URL（支持 string 和 array 格式）
 */
export function extractUrlFromInput(input) {
    if (typeof input === 'string') {
        return input;
    } else if (Array.isArray(input) && input.length > 0) {
        return typeof input[0] === 'string' ? input[0] : input[0];
    }
    return null;
}

/**
 * 初始化 Map 映射
 */
export function initMaps(image_list) {
    const urlToNameMap = new Map();
    const nameToItemMap = new Map();
    image_list.forEach(item => {
        urlToNameMap.set(item.url, item.name);
        nameToItemMap.set(item.name, item);
    });
    return { urlToNameMap, nameToItemMap };
}

/**
 * 创建 image_name_widget 的 callback（用于 va_widgets）
 */
export function createImageNameWidgetCallbackForVaWidgets(nameToItemMap, va_widgets, isBatchUpdating) {
    return function(e) {
        const item = nameToItemMap.get(e);
        if (item) {
            const image_url = decodeURIComponent(item.url);
            isBatchUpdating.value = true;
            va_widgets.forEach(va_widget => {
                va_widget.value = image_url;
                if (va_widget.callback) {
                    va_widget.callback(image_url);
                }
            });
            isBatchUpdating.value = false;
        }
    };
}

/**
 * 创建 image_name_widget 的 callback（用于 media_widget）
 */
export function createImageNameWidgetCallbackForMediaWidget(nameToItemMap, media_widget) {
    return function(e) {
        const item = nameToItemMap.get(e);
        if (item) {
            const image_url = decodeURIComponent(item.url);
            media_widget.value = image_url;
            if (media_widget.callback) {
                media_widget.callback(image_url);
            }
        }
    };
}

/**
 * 创建 value setter（用于 va_widget）
 */
export function createVaWidgetValueSetter(va_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, isBatchUpdating) {
    let _value = va_widget.value;

    return {
        get: () => _value,
        set: function(newValue) {
            const oldValue = _value;
            _value = newValue;
            console.log(`[hookLoadMedia] va_widget.value 被设置, widget.name=${va_widget.name}, oldValue=`, oldValue, ', newValue=', newValue);

            // 批量更新时跳过监听逻辑
            if (isBatchUpdating.value) {
                console.log(`[hookLoadMedia] 批量更新中，跳过处理, widget.name=${va_widget.name}`);
                return;
            }

            // 如果值没有变化，不需要处理
            if (oldValue === newValue) {
                console.log(`[hookLoadMedia] 值未变化，跳过处理, widget.name=${va_widget.name}`);
                return;
            }

            // 使用 Map 快速查找（O(1)）
            const name = urlToNameMap.get(newValue);
            if (name && image_name_widget) {
                console.log(`[hookLoadMedia] 找到匹配的name, widget.name=${va_widget.name}, name=`, name);
                image_name_widget.value = name;
            } else if (image_name_widget && newValue && typeof newValue === 'string' && newValue.includes('/')) {
                // 如果没找到，可能是新上传的文件，需要添加到列表
                const fileName = newValue.split('/').pop();
                console.log(`[hookLoadMedia] 未找到匹配的name, widget.name=${va_widget.name}, 可能是新文件, fileName=${fileName}`);

                // 检查是否真的是新文件（URL格式）
                if (newValue.startsWith('http') || newValue.startsWith('/')) {
                    handleNewUploadedFile(newValue, image_list, urlToNameMap, nameToItemMap, image_name_widget, actualMediaWidget);
                    console.log(`[hookLoadMedia] 新文件已通过value setter添加到列表, 当前列表长度=${image_list.length}`);
                }

                image_name_widget.value = fileName;
            }
        }
    };
}

/**
 * 创建 va_widget 的 callback
 */
export function createVaWidgetCallback(va_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, originalVaCallback) {
    return function(e) {
        console.log(`[hookLoadMedia] va_widget.callback 被触发, widget.name=${va_widget.name}, e=`, e);

        if (image_name_widget) {
            const url = extractUrlFromInput(e);
            if (url) {
                const name = urlToNameMap.get(url);
                if (name) {
                    image_name_widget.value = name;
                } else {
                    // 如果没找到，可能是新上传的文件
                    if (typeof e === 'string' && !e.startsWith('http') && !e.startsWith('/')) {
                        // 不是 URL 格式，直接使用文件名
                        image_name_widget.value = e.split('/').pop();
                    } else {
                        // 是新上传的文件，添加到列表
                        const fileName = handleNewUploadedFile(url, image_list, urlToNameMap, nameToItemMap, image_name_widget, actualMediaWidget);
                        console.log(`[hookLoadMedia] 检测到新上传的文件, url=${url}, fileName=${fileName}, 当前列表长度=${image_list.length}`);
                        image_name_widget.value = fileName;
                    }
                }
            }
        }

        // 调用原始callback
        if (originalVaCallback) {
            console.log(`[hookLoadMedia] 调用原始callback, widget.name=${va_widget.name}`);
            originalVaCallback(e);
        } else {
            console.log(`[hookLoadMedia] 原始callback不存在, widget.name=${va_widget.name}`);
        }
    };
}

/**
 * 创建 media_widget 的 callback
 */
export function createMediaWidgetCallback(media_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, originalCallback) {
    return function(e) {
        console.log('media_widget.callback', e);
        if (typeof e == 'string') {
            // 使用 Map 快速查找（O(1)）
            const item = e.includes('http') ?
                (urlToNameMap.has(e) ? {url: e, name: urlToNameMap.get(e)} : null) :
                (nameToItemMap ? nameToItemMap.get(e) : null);

            const image_url = item ? decodeURIComponent(item.url) : e;

            image_name_widget.value = item ? item.name : e;
            media_widget.value = image_url;
            if (originalCallback) {
                originalCallback([image_url])
            }
        } else {
            // 处理数组格式的输入（如文件上传）
            const url = extractUrlFromInput(e);
            if (url) {
                const existingName = urlToNameMap.get(url);

                if (existingName) {
                    // 如果已经在列表中，直接使用
                    image_name_widget.value = existingName;
                    media_widget.value = url;
                } else {
                    // 如果不在列表中，说明是新上传的文件，需要添加到列表
                    const fileName = handleNewUploadedFile(url, image_list, urlToNameMap, nameToItemMap, image_name_widget, actualMediaWidget);
                    console.log(`[hookLoadMedia] 检测到新上传的文件（media_widget分支）, url=${url}, fileName=${fileName}, 当前列表长度=${image_list.length}`);
                    image_name_widget.value = fileName;
                    media_widget.value = url;
                }
            }

            if (originalCallback) {
                originalCallback(e)
            }
        }
    };
}

/**
 * 设置 va_widget 的 value setter
 */
export function setupVaWidgetValueSetter(va_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, isBatchUpdating) {
    const existingDescriptor = Object.getOwnPropertyDescriptor(va_widget, 'value');

    if (existingDescriptor && !existingDescriptor.configurable) {
        return; // 跳过不可配置的属性
    }

    if (existingDescriptor) {
        delete va_widget.value;
    }

    const valueSetter = createVaWidgetValueSetter(va_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, isBatchUpdating);

    Object.defineProperty(va_widget, 'value', {
        get: valueSetter.get,
        set: valueSetter.set,
        enumerable: true,
        configurable: true
    });
}

/**
 * 处理 va_widgets
 */
export function setupVaWidgets(node, va_widgets, image_list, urlToNameMap, nameToItemMap, image_name_widget, actualMediaWidget) {
    const isBatchUpdating = { value: false };

    // 创建 image_name_widget
    if (!image_name_widget) {
        image_name_widget = node.addWidget("combo", "image_name", "",
            createImageNameWidgetCallbackForVaWidgets(nameToItemMap, va_widgets, isBatchUpdating),
            {
                serialize: true,
                values: image_list.map(item => item.name)
            }
        );
    }

    // 隐藏所有 va_widgets 并设置监听
    va_widgets.forEach(va_widget => {
        hideWidget(node, va_widget.name);
        setupVaWidgetValueSetter(va_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, isBatchUpdating);

        // 重写 callback
        const originalVaCallback = va_widget.callback;
        console.log(`[hookLoadMedia] 重写 va_widget.callback, widget.name=${va_widget.name}, 原始callback=${originalVaCallback ? '存在' : '不存在'}`);
        va_widget.callback = createVaWidgetCallback(va_widget, urlToNameMap, nameToItemMap, image_list, image_name_widget, actualMediaWidget, originalVaCallback);
    });

    return image_name_widget;
}

/**
 * 应用工作流图像设置
 */
export async function applyWorkflowImageSettings(workflowParams, image_list, media_widget, image_name_widget, currentNodeId, va_widgets, actualMediaWidget) {
    if (workflowParams && workflowParams.nodes) {
        // 先获取配置，然后将 mediaNodeList 和配置的 keys 合并
        const config = await fetchMediaConfigWithCache();
        const allMediaNodeTypes = new Set(mediaNodeList);
        if (config) {
            // 将配置中的 keys 添加到集合中
            for (const key of Object.keys(config)) {
                allMediaNodeTypes.add(key);
            }
        }

        // 使用同步的 includes 查找匹配的节点（完全避免循环中的异步）
        const imageNode = workflowParams.nodes.find(item =>
            item.id === currentNodeId && allMediaNodeTypes.has(item.type)
        )

        if (imageNode && imageNode.widgets_values && imageNode.widgets_values[0]) {
            const item = imageNode.widgets_values[0].split('/')
            image_list.push({
                name: item[item.length - 1],
                url: imageNode.widgets_values[0]
            })

            // 使用 actualMediaWidget 而不是 media_widget
            const targetWidget = actualMediaWidget || media_widget;

            if (targetWidget) {
                targetWidget.value = imageNode.widgets_values[0]

                if (targetWidget.options) {
                    targetWidget.options.values = image_list.map(item => item.url)
                }

                if (image_name_widget) {
                    image_name_widget.options.values = image_list.map(item => item.name)
                }

                // 触发 callback
                if (targetWidget.callback) {
                    targetWidget.callback(imageNode.widgets_values[0])
                }

                // 如果是 va_widgets 的情况，需要同步更新所有 va_widgets
                if (va_widgets && va_widgets.length > 0) {
                    va_widgets.forEach(va_widget => {
                        if (va_widget !== targetWidget) {
                            va_widget.value = imageNode.widgets_values[0];
                            if (va_widget.callback) {
                                va_widget.callback(imageNode.widgets_values[0]);
                            }
                        }
                    });
                }
            }
        }
    }
}

/**
 * 获取文件列表数据
 */
export async function fetchImageList(apiHost, nodeName) {
    const res = await fetch(`${apiHost}/special/community/commit_input_resource?${
        new URLSearchParams({
            ext: computeExt(nodeName),
            current: 1,
            page_size: 100
        }).toString()
    }`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getCookie('bizy_token')}`
        }
    });

    const {data} = await res.json();
    const list = (data && data.data && data.data.data && data.data.data.list) || [];
    return list.filter(item => item.name).map(item => ({
        url: item.url,
        id: item.id,
        name: item.name
    }));
}
