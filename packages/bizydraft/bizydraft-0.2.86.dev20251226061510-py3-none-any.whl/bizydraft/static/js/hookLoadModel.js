import { app } from "../../scripts/app.js";
import '../BizyAir/bizyair_frontend.js'
import {
    getNodeConfig,
    createSetWidgetCallback,
    setupNodeMouseBehavior,
    addBadge,
    possibleWidgetNames
} from './hookLoad/model.js'

// 存储清理标志
let storageClearedOnce = false;
app.registerExtension({
    name: "bizyair.hook.load.model",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {

        if (!storageClearedOnce) {
            // localStorage.removeItem('workflow')
            localStorage.clear()
            sessionStorage.clear()
            storageClearedOnce = true;
        }
        const interval = setInterval(() => {
            if (window.switchLanguage) {
                window.switchLanguage('zh')
                clearInterval(interval)
            }
        }, 100)

        // 异步获取节点配置
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        const nodeConfig = await getNodeConfig(nodeData.name);
        if (nodeConfig) {
            nodeType.prototype.onNodeCreated = function() {
                try {
                    const inputs = nodeConfig.config.inputs;
                    const inputKeys = Object.keys(inputs);

                    // 计算需处理的目标widgets（按禁用过滤后再确定数量和索引）
                    let targetWidgets = [];
                    // 优先按API字段名匹配
                    inputKeys.forEach((key) => {
                        const cfg = inputs[key];
                        if (cfg && !cfg.disable_comfyagent) {
                            const w = this.widgets.find(x => x.name === key);
                            if (w) targetWidgets.push(w);
                        }
                    });
                    // 如果一个都没匹配到，使用fallback列表
                    if (targetWidgets.length === 0) {
                        const fallback = this.widgets.filter(w => possibleWidgetNames.includes(w.name));
                        // fallback 不再过滤 disable 标记，因为此路径说明API key未命中
                        targetWidgets = fallback;
                    }

                    // 按目标widgets数量创建隐藏字段（model_version_id, model_version_id2...）
                    targetWidgets.forEach((_, idx) => {
                        const fieldName = idx === 0 ? "model_version_id" : `model_version_id${idx + 1}`;
                        let mv = this.widgets.find(w => w.name === fieldName);
                        if (!mv) {
                            mv = this.addWidget("hidden", fieldName, "", function(){}, { serialize: true, values: [] });
                        }
                    });

                    // 如果没有找到匹配的输入字段，使用兼容性逻辑
                    if (inputKeys.length === 0) {
                        const targetWidget = this.widgets.filter(widget => possibleWidgetNames.includes(widget.name));
                        targetWidget.forEach((widget, index) => {
                            let model_version_id;
                            if (index === 0) {
                                model_version_id = this.widgets.find(w => w.name === "model_version_id");
                                if (!model_version_id) {
                                    model_version_id = this.addWidget("hidden", "model_version_id", "", function(){
                                    }, {
                                        serialize: true,
                                        values: []
                                    });
                                }
                            } else {
                                const fieldName = `model_version_id${index + 1}`;
                                model_version_id = this.widgets.find(w => w.name === fieldName);
                                if (!model_version_id) {
                                    model_version_id = this.addWidget("hidden", fieldName, "", function(){
                                    }, {
                                        serialize: true,
                                        values: []
                                    });
                                }
                            }
                        });
                    }

                    const result = onNodeCreated?.apply(this, arguments);
                    let selectedBaseModels = [];

                    // 检查是否需要添加徽章（与targetWidgets一致的索引规则）
                    targetWidgets.forEach((widget, idx) => {
                        const fieldName = idx === 0 ? "model_version_id" : `model_version_id${idx + 1}`;
                        const mv = this.widgets.find(w => w.name === fieldName);
                        if (mv) {
                            setTimeout(() => {
                                if (widget.value != 'NONE' && !mv.value) addBadge(this);
                            }, 200);
                        }
                    });

                    // 如果没有找到匹配的输入字段，使用兼容性逻辑检查徽章
                    if (inputKeys.length === 0) {
                        const targetWidget = this.widgets.filter(widget => possibleWidgetNames.includes(widget.name));
                        targetWidget.forEach((widget, index) => {
                            let model_version_id;
                            if (index === 0) {
                                model_version_id = this.widgets.find(w => w.name === "model_version_id");
                            } else {
                                const fieldName = `model_version_id${index + 1}`;
                                model_version_id = this.widgets.find(w => w.name === fieldName);
                            }

                            if (model_version_id) {
                                setTimeout(() => {
                                    if (widget.value != 'NONE' && !model_version_id.value) {
                                        addBadge(this);
                                    }
                                }, 200);
                            }
                        });
                    }

                    createSetWidgetCallback(nodeConfig, selectedBaseModels).call(this);
                    return result;
                } catch (error) {
                    console.error("Error in node creation:", error);
                }
            };
        }
    },
    async nodeCreated(node) {
        const nodeConfig = await getNodeConfig(node?.comfyClass);

        if (nodeConfig) {
            setupNodeMouseBehavior(node, nodeConfig);
        }
    },
    async setup() {
        const app = document.querySelector('#vue-app').__vue_app__
        const pinia = app.config.globalProperties.$pinia
        const settingStore = pinia._s.get('setting')
        await settingStore.set('Comfy.Workflow.ShowMissingModelsWarning', false)




        // 获取 toastStore
        const toastStore = pinia._s.get('toast');

        // 保存原始的 add 方法
        const originalAdd = toastStore.add;

        // 重写 add 方法，添加过滤逻辑
        toastStore.add = function(message) {
            const detail = (message.detail || '').toLowerCase();
            const summary = (message.summary || '').toLowerCase();
            const text = `${summary} ${detail}`;

            // 检查是否包含阻止的关键词
            const blockedKeywords = [
                'missing dependencies',
                'comfyui logs',
                'comfyullogs',
                'refer to the comfyui',
                'you may be missing'
            ];

            const shouldBlock = blockedKeywords.some(keyword =>
                text.includes(keyword.toLowerCase())
            );

            // 如果包含阻止的关键词，则不添加 toast
            if (shouldBlock) {
                console.log('Blocked toast:', message);
                return;
            }

            // 否则正常添加
            return originalAdd.call(this, message);
        };

        console.log('Toast blocker activated!');
    }
})
