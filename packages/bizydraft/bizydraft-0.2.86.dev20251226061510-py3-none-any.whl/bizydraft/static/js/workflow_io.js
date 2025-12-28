// 基础类型检查
const BASIC_TYPES = ['number', 'string', 'boolean'];

/**
 * 检查值是否为基础类型
 * @param {any} val - 要检查的值
 * @returns {boolean} 是否为基础类型
 */
function isBasicType(val) {
    const type = typeof val;
    return BASIC_TYPES.includes(type);
}

/**
 * 遍历所有节点inputs，保留基础类型参数
 * @param {Object} prompt - prompt对象
 * @returns {Array} 输入参数数组
 */
function getInputParams(prompt) {
    const inputParams = [];

    for (const [nodeId, node] of Object.entries(prompt)) {
        const classType = node.class_type;
        const inputs = node.inputs || {};

        for (const [k, v] of Object.entries(inputs)) {
            if (isBasicType(v)) {
                inputParams.push({
                    node_id: nodeId,
                    class_type: classType,
                    param_name: k,
                    param_value: v
                });
            }
        }
    }

    return inputParams;
}

/**
 * 通过prompt参数推断叶子节点（即没有被其他节点inputs引用的节点）
 * @param {Object} prompt - prompt对象
 * @returns {Set} 叶子节点id集合
 */
function getLeafNodesFromPrompt(prompt) {
    const referenced = new Set();

    for (const [nodeId, node] of Object.entries(prompt)) {
        const inputs = node.inputs || {};

        for (const v of Object.values(inputs)) {
            // 如果是引用（如["4", 1]），则v为array且第一个元素为节点id
            if (Array.isArray(v) && v.length > 0 && typeof v[0] === 'string') {
                referenced.add(v[0]);
            }
        }
    }

    const allNodes = new Set(Object.keys(prompt));
    const leafNodes = new Set([...allNodes].filter(x => !referenced.has(x)));

    return leafNodes;
}

/**
 * 从工作流节点中查找指定节点id的节点
 * @param {Array} wfNodes - 工作流节点数组
 * @param {string} nodeId - 节点id
 * @returns {Object|null} 找到的节点或null
 */
function getNodeIdFromWfNodes(wfNodes, nodeId) {
    for (const wfNode of wfNodes) {
        if (String(wfNode.id || 0) === nodeId) {
            return wfNode;
        }
    }
    return null;
}

/**
 * 按节点类型和参数名整理参数信息
 * @param {Array} inputParams - 输入参数数组
 * @param {Set} excludeNodeIds - 需要排除的节点id集合
 * @param {Array} wfNodes - 工作流节点数组
 * @returns {Array} 整理后的参数信息
 */
function summarizeParams(inputParams, excludeNodeIds, wfNodes) {
    const summary = {};

    for (const param of inputParams) {
        const nodeId = param.node_id;

        if (excludeNodeIds.has(nodeId)) {
            continue;
        }

        const wfNode = getNodeIdFromWfNodes(wfNodes, nodeId);
        let title = param.class_type;

        if (wfNode && wfNode.title) {
            title = wfNode.title;
        }

        const key = `${param.class_type}_${nodeId}`;

        if (!summary[key]) {
            summary[key] = {
                name: param.class_type,
                displayName: param.class_type,
                nodeId: nodeId,
                params: [],
                title: title
            };
        }

        // 获取参数值的类型
        let paramType = typeof param.param_value;
        if (paramType === 'number') {
            paramType = Number.isInteger(param.param_value) ? 'INT' : 'FLOAT';
        } else {
            paramType = paramType.toUpperCase();
        }

        summary[key].params.push({
            name: param.param_name,
            displayName: param.param_name,
            type: paramType,
            defaultValue: param.param_value
        });
    }

    return Object.values(summary);
}

/**
 * 解析工作流IO数据
 * @param {Object} requestData - 请求数据
 * @returns {Object} 解析结果
 */
function parseWorkflowIO(requestData) {
    const prompt = requestData.prompt || {};
    const extraData = requestData.extra_data || {};

    const extraPnginfo = extraData.extra_pnginfo || {};
    const workflow = extraPnginfo.workflow || {};
    const wfNodes = workflow.nodes || [];

    // 1. 输出参数（推断叶子节点）
    const leafNodes = getLeafNodesFromPrompt(prompt);
    const outputNodes = [];

    for (const nodeId of leafNodes) {
        const node = prompt[nodeId];
        const classType = node.class_type;
        const wfNode = getNodeIdFromWfNodes(wfNodes, nodeId);

        let title = classType;
        if (wfNode && wfNode.title) {
            title = wfNode.title;
        }

        outputNodes.push({
            nodeId: nodeId,
            name: classType,
            displayName: classType,
            title: title,
            params: []
        });
    }

    // 2. 输入参数（排除已作为输出的节点）
    const inputParams = getInputParams(prompt);
    const inputSummary = summarizeParams(inputParams, leafNodes, wfNodes);

    // 3. 构造response格式
    return {
        data: {
            inputs: inputSummary,
            outputs: outputNodes
        }
    };
}

// 导出函数
export {
    parseWorkflowIO,
    isBasicType,
    getInputParams,
    getLeafNodesFromPrompt,
    summarizeParams,
    getNodeIdFromWfNodes
};
