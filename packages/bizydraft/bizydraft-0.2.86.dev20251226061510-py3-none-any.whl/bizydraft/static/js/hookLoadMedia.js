import { app } from "../../scripts/app.js";
import { hideWidget } from './tool.js';
import {
    getMediaNodeConfig,
    getMediaInputKeys,
    computeIsMediaNode,
    mediaNodeList,
    fetchMediaConfigWithCache,
    findMediaWidget,
    findMediaWidgets,
    updateWidgetsOptions,
    handleNewUploadedFile,
    extractUrlFromInput,
    initMaps,
    createImageNameWidgetCallbackForMediaWidget,
    createMediaWidgetCallback,
    setupVaWidgets,
    applyWorkflowImageSettings,
    fetchImageList
} from './hookLoad/media.js';

app.registerExtension({
    name: "bizyair.image.to.oss",
    beforeRegisterNodeDef(nodeType, nodeData) {
        let workflowParams = null
        document.addEventListener('workflowLoaded', (event) => {
            workflowParams = event.detail;
        })
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;

            Array.from(files).forEach((file) => {
                if (file.type === 'application/json' || file.name.endsWith('.json')) {
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        try {
                            const jsonContent = JSON.parse(event.target.result);
                            if (jsonContent && jsonContent.nodes) {
                                window.currentWorkflowData = jsonContent;
                            }
                        } catch (error) {
                            console.error('解析JSON文件失败:', error);
                        }
                    };
                    reader.readAsText(file);
                }
            });
        })
        nodeType.prototype.onNodeCreated = async function() {
            if (!(await computeIsMediaNode(nodeData.name))) {
                return;
            }

            const apiHost = 'https://bizyair.cn/api'
            // const apiHost = 'http://localhost:3000/api'

            // 获取 API 配置
            const mediaNodeConfig = await getMediaNodeConfig(nodeData.name);
            const apiInputKeys = getMediaInputKeys(mediaNodeConfig);

            // 查找媒体 widget
            const media_widget = findMediaWidget(this.widgets, apiInputKeys);
            const va_widgets = findMediaWidgets(this.widgets, apiInputKeys);
            let image_name_widget = this.widgets.find(w => w.name === 'image_name');

            // 获取文件列表
            const image_list = await fetchImageList(apiHost, nodeData.name);

            // 初始化 Map 映射
            const { urlToNameMap, nameToItemMap } = initMaps(image_list);

            // 如果找到va_widgets，处理它们
            if (va_widgets.length > 0) {
                image_name_widget = setupVaWidgets(this, va_widgets, image_list, urlToNameMap, nameToItemMap, image_name_widget, va_widgets[0]);
            }

            // 如果va_widgets没有创建image_name_widget，使用原有逻辑创建
            if (!image_name_widget && media_widget) {
                image_name_widget = this.addWidget("combo", "image_name", "",
                    createImageNameWidgetCallbackForMediaWidget(nameToItemMap, media_widget),
                    {
                        serialize: true,
                        values: image_list.map(item => item.name)
                    }
                );
            }

            // 如果进入了va_widgets分支，使用va_widgets中第一个作为media_widget的替代
            const actualMediaWidget = va_widgets.length > 0 ? va_widgets[0] : media_widget;

            if (image_name_widget && actualMediaWidget) {
                const val = urlToNameMap.get(actualMediaWidget.value) || actualMediaWidget.value;
                image_name_widget.label = actualMediaWidget.label;
                image_name_widget.value = val;

                // 调整 widget 顺序
                const currentIndex = this.widgets.indexOf(image_name_widget);
                if (currentIndex > 1) {
                    this.widgets.splice(currentIndex, 1);
                    this.widgets.splice(1, 0, image_name_widget);
                }

                // 如果没有进入va_widgets分支，才隐藏media_widget
                if (va_widgets.length === 0) {
                    hideWidget(this, media_widget.name);
                }

                // 更新 widget 选项列表
                updateWidgetsOptions([actualMediaWidget], image_list);

                // 对于va_widgets的情况，callback已经在上面重写过了，不需要再次重写
                if (va_widgets.length === 0 && media_widget) {
                    const callback = media_widget.callback;
                    media_widget.callback = createMediaWidgetCallback(
                        media_widget,
                        urlToNameMap,
                        nameToItemMap,
                        image_list,
                        image_name_widget,
                        actualMediaWidget,
                        callback
                    );
                }
            }

            // 应用工作流设置
            const workflowData = window.currentWorkflowData || workflowParams;
            if (workflowData) {
                await applyWorkflowImageSettings(workflowData, image_list, media_widget, image_name_widget, this.id, va_widgets, actualMediaWidget);
                if (window.currentWorkflowData) {
                    delete window.currentWorkflowData;
                }
            } else {
                await applyWorkflowImageSettings(workflowParams, image_list, media_widget, image_name_widget, this.id, va_widgets, actualMediaWidget);
            }

            // 发送完成消息
            window.parent.postMessage({
                type: 'functionResult',
                method: 'hookLoadImageCompleted',
                params: {}
            }, '*');
        }
    }
})

// app.api.addEventListener('graphChanged', (e) => {
//     console.log('Graph 发生变化，当前 workflow JSON:', e.detail)
//     window.parent.postMessage({
//         type: 'functionResult',
//         method: 'workflowChanged',
//         result: e.detail
//     }, '*');

//     document.dispatchEvent(new CustomEvent('workflowLoaded', {
//         detail: e.detail
//     }));
// })
