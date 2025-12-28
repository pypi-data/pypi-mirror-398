// 设备管理界面 JavaScript

(function() {
    'use strict';

    const CHANNEL_MAP_KEYS = [
        '01_AWGXY1',
        '02_AWGXY2',
        '03_AWGXY3',
        '04_AWGXY4',
        '05_AWGXY5',
        '06_AWGXY6',
        '07_AWGXY7',
        '08_AWGXY8',
        '09_AWGM1',
        '10_AWGM2',
        '11_AWGM3',
        '12_AWGM4',
        '13_AWGZ1',
        '14_AWGZ2',
        '15_AWGZ3',
        '16_AWGZ4',
        '17_AWGZ5',
        '18_AWGZ6',
        '19_AWGZ7',
        '20_AWGZ8',
        '21_ADCM1',
        '22_ADCM2',
        '23_ADCM3',
        '24_ADCM4'
    ];

    const CHANNEL_TYPES = ['M', 'ADC', 'Z', 'X', 'Y', 'ZDC'];

    const LOCAL_CHANNEL_MAP_DEFAULT = CHANNEL_MAP_KEYS.reduce((acc, key) => {
        acc[key] = '';
        return acc;
    }, {});

    // 实体列表缓存
    let entityList = [];
    let entityListPromise = null;

    // 状态管理
    const state = {
        devices: [],
        selectedDevice: null,
        discoveredDevices: [],
        discoverSelectAll: true,
        isLoadingDevices: false,
        isDeletingDevice: false,
        isAddingDiscovered: false,
        isSavingSettings: false,
        isSavingEnable: false,
        activeTab: 'status', // 'config' 或 'status'
        expandedModels: new Set(), // 展开的 model 分组
        autoRefreshEnabled: true,
        currentOperation: null, // 当前正在执行的操作信息 {operationName, deviceSn, params}
        operationsData: {}, // 存储操作数据
        pluginStatusCache: null // 缓存 plugin-status 接口的完整结果
    };

    // DOM 元素
    const elements = {
        deviceList: document.getElementById('deviceList'),
        deviceDetail: document.getElementById('deviceDetail'),
        addDeviceBtn: document.getElementById('addDeviceBtn'),
        autoDiscoverBtn: document.getElementById('autoDiscoverBtn'),
        addDeviceModal: document.getElementById('addDeviceModal'),
        closeAddDeviceModal: document.getElementById('closeAddDeviceModal'),
        cancelAddDeviceBtn: document.getElementById('cancelAddDeviceBtn'),
        confirmAddDeviceBtn: document.getElementById('confirmAddDeviceBtn'),
        addDeviceForm: document.getElementById('addDeviceForm'),
        discoverModal: document.getElementById('discoverModal'),
        closeDiscoverModal: document.getElementById('closeDiscoverModal'),
        cancelDiscoverBtn: document.getElementById('cancelDiscoverBtn'),
        confirmDiscoverBtn: document.getElementById('confirmDiscoverBtn'),
        selectAllDiscoverBtn: document.getElementById('selectAllDiscoverBtn'),
        refreshDiscoverBtn: document.getElementById('refreshDiscoverBtn'),
        refreshDiscoverBtn: document.getElementById('refreshDiscoverBtn'),
        discoverDeviceList: document.getElementById('discoverDeviceList'),
        discoverSummary: document.getElementById('discoverSummary'),
        restartHostClientBtn: document.getElementById('restartHostClientBtn'),
        restartHostClientModal: document.getElementById('restartHostClientModal'),
        closeRestartHostClientModal: document.getElementById('closeRestartHostClientModal'),
        cancelRestartHostClientBtn: document.getElementById('cancelRestartHostClientBtn'),
        confirmRestartHostClientBtn: document.getElementById('confirmRestartHostClientBtn'),
        restartHostClientConfirmStage: document.getElementById('restartHostClientConfirmStage'),
        restartHostClientExecuteStage: document.getElementById('restartHostClientExecuteStage'),
        restartStatusIcon: document.getElementById('restartStatusIcon'),
        restartStatusTitle: document.getElementById('restartStatusTitle'),
        restartCommandStatus: document.getElementById('restartCommandStatus'),
        restartHostClientStatus: document.getElementById('restartHostClientStatus'),
        restartCommandId: document.getElementById('restartCommandId'),
        restartStatusProgress: document.getElementById('restartStatusProgress'),
        restartProgressFill: document.getElementById('restartProgressFill'),
        restartProgressText: document.getElementById('restartProgressText'),
        pluginStatusBtn: document.getElementById('pluginStatusBtn'),
        pluginStatusModal: document.getElementById('pluginStatusModal'),
        closePluginStatusModal: document.getElementById('closePluginStatusModal'),
        closePluginStatusBtn: document.getElementById('closePluginStatusBtn'),
        refreshDeviceBtn: document.getElementById('refreshDeviceBtn'),
        autoRefreshCheckbox: document.getElementById('autoRefreshCheckbox'),
        channelMappingBtn: document.getElementById('channelMappingBtn'),
        channelMappingModal: document.getElementById('channelMappingModal'),
        closeChannelMappingModal: document.getElementById('closeChannelMappingModal'),
        closeChannelMappingBtn: document.getElementById('closeChannelMappingBtn'),
        saveAllChannelMappingBtn: document.getElementById('saveAllChannelMappingBtn'),
        channelMappingContent: document.getElementById('channelMappingContent'),
        channelMappingSidebar: document.getElementById('channelMappingSidebar'),
        duplicateWarningModal: document.getElementById('duplicateWarningModal'),
        closeDuplicateWarningModal: document.getElementById('closeDuplicateWarningModal'),
        duplicateWarningContent: document.getElementById('duplicateWarningContent'),
        cancelSaveBtn: document.getElementById('cancelSaveBtn'),
        confirmSaveBtn: document.getElementById('confirmSaveBtn'),
        operationModal: document.getElementById('operationModal'),
        closeOperationModal: document.getElementById('closeOperationModal'),
        cancelOperationBtn: document.getElementById('cancelOperationBtn'),
        confirmOperationBtn: document.getElementById('confirmOperationBtn'),
        operationModalTitle: document.getElementById('operationModalTitle'),
        operationModalDescription: document.getElementById('operationModalDescription'),
        operationModalParams: document.getElementById('operationModalParams'),
        editConfigFilesBtn: document.getElementById('editConfigFilesBtn'),
        editConfigFilesModal: document.getElementById('editConfigFilesModal'),
        closeEditConfigFilesModal: document.getElementById('closeEditConfigFilesModal'),
        configFilesList: document.getElementById('configFilesList'),
        refreshConfigFilesBtn: document.getElementById('refreshConfigFilesBtn'),
        addConfigFileBtn: document.getElementById('addConfigFileBtn'),
        configFileEditor: document.getElementById('configFileEditor'),
        configFileTitle: document.getElementById('configFileTitle'),
        saveConfigFileBtn: document.getElementById('saveConfigFileBtn'),
        deleteConfigFileBtn: document.getElementById('deleteConfigFileBtn'),
        formatConfigFileBtn: document.getElementById('formatConfigFileBtn'),
        configFileError: document.getElementById('configFileError')
    };

    let autoRefreshTimer = null;

    // 初始化
    function init() {
        setupEventListeners();
        loadDevices();
    }

    function renderDeviceConfig(device) {
        const configItemsRaw = device.configItems || [];
        const configItems = Array.isArray(configItemsRaw)
            ? configItemsRaw
            : Object.values(configItemsRaw);
        
        // 过滤掉 enable 和 channel_map 字段（enable 会在单独的地方显示，channel_map 已移除）
        const filteredItems = configItems.filter(item => item && item.field !== 'enable' && item.field !== 'channel_map');
        
        if (filteredItems.length === 0) {
            return `
                <div class="detail-section">
                    <div class="detail-section-content">
                        <div class="empty-config">此设备未提供额外的配置项</div>
                    </div>
                </div>
            `;
        }

        const configListHTML = filteredItems
            .filter(Boolean)
            .map(renderConfigItem)
            .join('');

        return `
            <div class="detail-section">
                <div class="detail-section-content">
                    <div class="config-item-list">
                        ${configListHTML}
                    </div>
                </div>
            </div>
        `;
    }

    function renderBasicDeviceInfo(device) {
        const configItemsRaw = device.configItems || [];
        const configItems = Array.isArray(configItemsRaw)
            ? configItemsRaw
            : Object.values(configItemsRaw);
        
        // 查找 enable 字段
        const enableItem = configItems.find(item => item && item.field === 'enable');
        
        let enableRow = '';
        if (enableItem) {
            enableRow = renderEnableInfoRow(enableItem);
        }
        
        return `
            <div class="detail-section">
                <div class="detail-section-content basic-info-grid">
                    ${renderDeviceNameRow(device)}
                    ${renderBasicInfoRow('设备型号', device.model)}
                    ${renderBasicInfoRow('设备SN', getDeviceSn(device))}
                    ${renderConnectionInfoRow(device)}
                    ${enableRow}
                </div>
            </div>
        `;
    }
    
    function renderDeviceNameRow(device) {
        const deviceName = device.name || '';
        return `
            <div class="basic-info-item basic-info-name-item">
                <span class="basic-info-label">设备名称</span>
                <div class="basic-info-name-wrapper">
                    <span class="basic-info-value basic-info-name-display" id="deviceNameDisplay">${escapeHtml(deviceName || '—')}</span>
                    <input type="text" 
                           class="basic-info-name-input" 
                           id="deviceNameInput" 
                           value="${escapeHtml(deviceName)}" 
                           maxlength="20"
                           style="display: none;">
                    <button class="basic-info-edit-btn" id="deviceNameEditBtn" title="编辑设备名称">
                        <span class="edit-icon">✏️</span>
                    </button>
                    <button class="basic-info-save-btn" id="deviceNameSaveBtn" title="保存" style="display: none;">
                        <span class="save-icon">✓</span>
                    </button>
                    <button class="basic-info-cancel-btn" id="deviceNameCancelBtn" title="取消" style="display: none;">
                        <span class="cancel-icon">✕</span>
                    </button>
                </div>
            </div>
        `;
    }

    function renderConnectionInfoRow(device) {
        const addr = getDeviceAddrOnly(device);
        const port = getDevicePort(device);
        const connectionText = addr && port ? `${addr}:${port}` : (addr || port || '—');
        
        return `
            <div class="basic-info-item">
                <span class="basic-info-label">连接信息</span>
                <span class="basic-info-value">${escapeHtml(connectionText)}</span>
            </div>
        `;
    }

    function renderEnableInfoRow(enableItem) {
        const enableValue = enableItem.value === true || enableItem.value === 'true' || enableItem.value === 1;
        const inputId = `config-enable`;
        const tooltipText = '设置 Host Client 是否识别该设备，与硬件的真实开机状态无关';
        
        return `
            <div class="basic-info-item basic-info-enable">
                <span class="basic-info-label">
                    启用状态
                    <span class="info-icon" data-tooltip="${escapeHtml(tooltipText)}">i</span>
                </span>
                <div class="basic-info-enable-control">
                    <label class="enable-switch-label-compact" for="${inputId}">
                        <input type="checkbox" 
                            id="${inputId}" 
                            class="config-input enable-switch-input-compact" 
                            data-config-field="enable" 
                            data-config-type="bool"
                            ${enableValue ? 'checked' : ''} />
                        <span class="enable-switch-slider-compact"></span>
                    </label>
                </div>
            </div>
        `;
    }

    function renderBasicInfoRow(label, value) {
        return `
            <div class="basic-info-item">
                <span class="basic-info-label">${escapeHtml(label)}</span>
                <span class="basic-info-value">${escapeHtml(value || '—')}</span>
            </div>
        `;
    }

    function renderConfigItem(item) {
        const dtype = (item.dtype || '').toLowerCase();
        if (dtype === 'text') {
            return renderConfigTextItem(item);
        }

        const defaultText = formatConfigValue(item.default);
        const optionText = formatConfigOptions(item.options);
        const requirement = item.necessary ? '必填' : '可选';
        const inputHTML = renderConfigInput(item);
        const extraClass = (dtype === 'dict' || dtype === 'text') ? ' config-item-dict' : '';

        return `
            <div class="config-item${extraClass}">
                <div class="config-item-header">
                    <div class="config-item-title-box">
                        <span class="config-item-title">${escapeHtml(item.title || item.field)}</span>
                        <span class="config-item-require">${requirement}</span>
                    </div>
                </div>
                <div class="config-item-input">
                    ${inputHTML}
                </div>
            </div>
        `;
    }

    function renderConfigTextItem(item) {
        return `
            <div class="config-item config-item-text-only">
                <div class="config-text-line">
                    <span class="config-text-label">${escapeHtml(item.title || item.field)}</span>
                </div>
            </div>
        `;
    }

    function renderConfigInput(item) {
        const field = item.field;
        const type = item.dtype || 'str';
        const value = item.value;
        const options = item.options || {};
        const inputId = `config-${field}`;
        const commonAttrs = `data-config-field="${field}" data-config-type="${type}" class="config-input"`;

        switch (type) {
            case 'bool':
            case 'boolean':
                const boolValue = value === true || value === 'true' || value === 1;
                return `
                    <select ${commonAttrs} id="${inputId}">
                        <option value="true" ${boolValue ? 'selected' : ''}>是</option>
                        <option value="false" ${!boolValue ? 'selected' : ''}>否</option>
                    </select>
                `;
            case 'enum':
                if (item.multi_choose) {
                    const selectedValues = Array.isArray(value) ? value : (value ? [value] : []);
                    const optionsHtml = Object.entries(options).map(([key, label]) => {
                        const selected = selectedValues.includes(key) ? 'selected' : '';
                        return `<option value="${escapeHtml(key)}" ${selected}>${escapeHtml(label)}</option>`;
                    }).join('');
                    return `
                        <select ${commonAttrs} data-config-multi="true" multiple id="${inputId}">
                            ${optionsHtml}
                        </select>
                    `;
                }
                const optionsHtml = Object.entries(options).map(([key, label]) => {
                    const selected = value === key ? 'selected' : '';
                    return `<option value="${escapeHtml(key)}" ${selected}>${escapeHtml(label)}</option>`;
                }).join('');
                return `
                    <select ${commonAttrs} id="${inputId}">
                        ${optionsHtml}
                    </select>
                `;
            case 'int':
            case 'integer':
                return `
                    <input ${commonAttrs} id="${inputId}" type="number" inputmode="numeric"
                        value="${value ?? ''}"
                        ${item.min !== undefined ? `min="${item.min}"` : ''}
                        ${item.max !== undefined ? `max="${item.max}"` : ''}/>
                `;
            case 'float':
                return `
                    <input ${commonAttrs} id="${inputId}" type="number" step="any"
                        value="${value ?? ''}"
                        ${item.min !== undefined ? `min="${item.min}"` : ''}
                        ${item.max !== undefined ? `max="${item.max}"` : ''}/>
                `;
            case 'list':
                return `
                    <textarea ${commonAttrs} data-config-complex="true" data-auto-resize="true" data-auto-resize-min="120" id="${inputId}">${value ? escapeHtml(JSON.stringify(value, null, 2)) : ''}</textarea>
                `;
            case 'dict':
                if (field === 'dac_replay_continue') {
                    const mapValue = getDacReplayContinueInitialValue(value, item.default);
                    const serialized = JSON.stringify(mapValue || {});
                    const escaped = escapeHtml(serialized);
                    return `
                        <div class="dac-replay-continue-editor" data-target-input="${inputId}" data-dac-replay-continue='${escaped}'>
                            <input type="hidden" data-config-field="${field}" data-config-type="${type}"
                                data-config-complex="true" class="config-input dac-replay-continue-hidden-input"
                                id="${inputId}" value='${escaped}' />
                        </div>
                    `;
                }
                return `
                    <textarea ${commonAttrs} data-config-complex="true" data-auto-resize="true" data-auto-resize-min="180" id="${inputId}" class="config-dict-textarea">${value ? escapeHtml(JSON.stringify(value, null, 2)) : ''}</textarea>
                `;
            case 'text':
                return `<div class="config-text">${escapeHtml(item.title || '')}</div>`;
            case 'str':
            case 'string':
            default:
                if (item.multi_line) {
                    return `<textarea ${commonAttrs} data-auto-resize="true" id="${inputId}">${value ? escapeHtml(value) : ''}</textarea>`;
                }
                return `<input ${commonAttrs} id="${inputId}" type="text" value="${value ? escapeHtml(value) : ''}"/>`;
        }
    }


    function getDacReplayContinueInitialValue(currentValue, defaultValue) {
        if (isPlainObject(currentValue) && Object.keys(currentValue).length > 0) {
            return currentValue;
        }
        if (typeof currentValue === 'string') {
            try {
                const parsed = JSON.parse(currentValue);
                if (isPlainObject(parsed)) {
                    return parsed;
                }
            } catch (err) {
                // ignore
            }
        }
        if (isPlainObject(defaultValue)) {
            return defaultValue;
        }
        return getDacReplayContinueDefaultTemplate();
    }

    function getDacReplayContinueDefaultTemplate() {
        if (window.DacReplayContinueEditor && typeof window.DacReplayContinueEditor.getDefaultMap === 'function') {
            return window.DacReplayContinueEditor.getDefaultMap();
        }
        return {};
    }

    function isPlainObject(value) {
        return Object.prototype.toString.call(value) === '[object Object]';
    }

    // 设置事件监听器
    function setupEventListeners() {
        // 添加设备按钮
        elements.addDeviceBtn.addEventListener('click', () => {
            showAddDeviceModal();
        });

        // 自动发现设备按钮
        elements.autoDiscoverBtn.addEventListener('click', () => {
            autoDiscoverDevices();
        });

        // 关闭模态框
        elements.closeAddDeviceModal.addEventListener('click', hideAddDeviceModal);
        elements.cancelAddDeviceBtn.addEventListener('click', hideAddDeviceModal);
        elements.closeDiscoverModal.addEventListener('click', hideDiscoverModal);
        elements.cancelDiscoverBtn.addEventListener('click', hideDiscoverModal);
        
        // 编辑配置文件按钮
        if (elements.editConfigFilesBtn) {
            elements.editConfigFilesBtn.addEventListener('click', () => {
                showEditConfigFilesModal();
            });
        }
        if (elements.closeEditConfigFilesModal) {
            elements.closeEditConfigFilesModal.addEventListener('click', hideEditConfigFilesModal);
        }
        if (elements.refreshConfigFilesBtn) {
            elements.refreshConfigFilesBtn.addEventListener('click', loadConfigFilesList);
        }
        if (elements.addConfigFileBtn) {
            elements.addConfigFileBtn.addEventListener('click', showAddConfigFileDialog);
        }
        if (elements.saveConfigFileBtn) {
            elements.saveConfigFileBtn.addEventListener('click', saveConfigFile);
        }
        if (elements.deleteConfigFileBtn) {
            elements.deleteConfigFileBtn.addEventListener('click', deleteConfigFile);
        }
        if (elements.formatConfigFileBtn) {
            elements.formatConfigFileBtn.addEventListener('click', formatConfigFile);
        }
        if (elements.configFileEditor) {
            elements.configFileEditor.addEventListener('input', () => {
                hideConfigFileError();
            });
            // 处理粘贴事件，自动格式化
            elements.configFileEditor.addEventListener('paste', (e) => {
                e.preventDefault();
                const text = (e.clipboardData || window.clipboardData).getData('text');
                try {
                    const parsed = JSON.parse(text);
                    const formatted = JSON.stringify(parsed, null, 2);
                    document.execCommand('insertText', false, formatted);
                } catch (err) {
                    document.execCommand('insertText', false, text);
                }
            });
        }
        
        // 点击模态框外部关闭
        if (elements.editConfigFilesModal) {
            elements.editConfigFilesModal.addEventListener('click', (e) => {
                if (e.target === elements.editConfigFilesModal) {
                    hideEditConfigFilesModal();
                }
            });
        }
        
        // 上位机信息按钮
        // 重启 Host Client 按钮
        if (elements.restartHostClientBtn) {
            elements.restartHostClientBtn.addEventListener('click', () => showRestartHostClientModal());
        }
        
        // 重启 Host Client 弹窗事件
        if (elements.closeRestartHostClientModal) {
            elements.closeRestartHostClientModal.addEventListener('click', hideRestartHostClientModal);
        }
        if (elements.cancelRestartHostClientBtn) {
            elements.cancelRestartHostClientBtn.addEventListener('click', hideRestartHostClientModal);
        }
        if (elements.confirmRestartHostClientBtn) {
            elements.confirmRestartHostClientBtn.addEventListener('click', () => executeRestartHostClientFromModal());
        }
        if (elements.restartHostClientModal) {
            elements.restartHostClientModal.addEventListener('click', (e) => {
                if (e.target === elements.restartHostClientModal) {
                    hideRestartHostClientModal();
                }
            });
        }

        elements.pluginStatusBtn.addEventListener('click', showPluginStatusModal);
        elements.closePluginStatusModal.addEventListener('click', hidePluginStatusModal);
        elements.closePluginStatusBtn.addEventListener('click', hidePluginStatusModal);
        
        // 上位机信息按钮hover tooltip
        setupPluginStatusTooltip();

        // 确认添加设备
        elements.confirmAddDeviceBtn.addEventListener('click', () => {
            handleAddDevice();
        });
        elements.confirmDiscoverBtn.addEventListener('click', handleAddDiscoveredDevices);
        elements.selectAllDiscoverBtn.addEventListener('click', toggleSelectAllDiscovered);
        if (elements.refreshDiscoverBtn) {
            elements.refreshDiscoverBtn.addEventListener('click', handleRefreshDiscover);
        }

        // 点击模态框外部关闭
        elements.addDeviceModal.addEventListener('click', (e) => {
            if (e.target === elements.addDeviceModal) {
                hideAddDeviceModal();
            }
        });
        elements.discoverModal.addEventListener('click', (e) => {
            if (e.target === elements.discoverModal) {
                hideDiscoverModal();
            }
        });
        elements.pluginStatusModal.addEventListener('click', (e) => {
            if (e.target === elements.pluginStatusModal) {
                hidePluginStatusModal();
            }
        });

        // 表单提交
        elements.addDeviceForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleAddDevice();
        });

        if (elements.refreshDeviceBtn) {
            elements.refreshDeviceBtn.addEventListener('click', () => loadDevices({ updateDetail: false }));
        }

        if (elements.autoRefreshCheckbox) {
            elements.autoRefreshCheckbox.checked = state.autoRefreshEnabled;
            // 如果默认启用自动刷新，启动定时器
            if (state.autoRefreshEnabled) {
                startAutoRefresh();
            }
            elements.autoRefreshCheckbox.addEventListener('change', (e) => {
                state.autoRefreshEnabled = e.target.checked;
                if (state.autoRefreshEnabled) {
                    startAutoRefresh();
                    loadDevices({ showLoading: false, updateDetail: false });
                } else {
                    stopAutoRefresh();
                }
            });
        }

        window.addEventListener('beforeunload', stopAutoRefresh);

        // 通道映射按钮事件
        if (elements.channelMappingBtn) {
            elements.channelMappingBtn.addEventListener('click', showChannelMappingModal);
        }
        if (elements.closeChannelMappingModal) {
            elements.closeChannelMappingModal.addEventListener('click', hideChannelMappingModal);
        }
        if (elements.closeChannelMappingBtn) {
            elements.closeChannelMappingBtn.addEventListener('click', hideChannelMappingModal);
        }
        if (elements.saveAllChannelMappingBtn) {
            elements.saveAllChannelMappingBtn.addEventListener('click', handleSaveAllChannelMapping);
        }
        if (elements.channelMappingModal) {
            elements.channelMappingModal.addEventListener('click', (e) => {
                if (e.target === elements.channelMappingModal) {
                    hideChannelMappingModal();
                }
            });
        }

        // 重复警告对话框事件
        if (elements.closeDuplicateWarningModal) {
            elements.closeDuplicateWarningModal.addEventListener('click', () => {
                if (elements.duplicateWarningModal && elements.duplicateWarningModal._resolvePromise) {
                    const resolve = elements.duplicateWarningModal._resolvePromise;
                    elements.duplicateWarningModal._resolvePromise = null;
                    hideDuplicateWarningModal();
                    resolve(false);
                } else {
                    hideDuplicateWarningModal();
                }
            });
        }
        if (elements.cancelSaveBtn) {
            elements.cancelSaveBtn.addEventListener('click', () => {
                if (elements.duplicateWarningModal && elements.duplicateWarningModal._resolvePromise) {
                    const resolve = elements.duplicateWarningModal._resolvePromise;
                    elements.duplicateWarningModal._resolvePromise = null;
                    hideDuplicateWarningModal();
                    resolve(false);
                } else {
                    hideDuplicateWarningModal();
                }
            });
        }
        if (elements.confirmSaveBtn) {
            elements.confirmSaveBtn.addEventListener('click', handleConfirmSaveWithDuplicates);
        }
        if (elements.duplicateWarningModal) {
            elements.duplicateWarningModal.addEventListener('click', (e) => {
                if (e.target === elements.duplicateWarningModal) {
                    hideDuplicateWarningModal();
                }
            });
        }

        // 操作模态框事件
        if (elements.closeOperationModal) {
            elements.closeOperationModal.addEventListener('click', hideOperationModal);
        }
        if (elements.cancelOperationBtn) {
            elements.cancelOperationBtn.addEventListener('click', hideOperationModal);
        }
        if (elements.confirmOperationBtn) {
            elements.confirmOperationBtn.addEventListener('click', handleConfirmOperation);
        }
        if (elements.operationModal) {
            elements.operationModal.addEventListener('click', (e) => {
                if (e.target === elements.operationModal) {
                    hideOperationModal();
                }
            });
        }
    }

    // 加载设备列表
    async function loadDevices(options = {}) {
        const { showLoading = true, updateDetail = true } = options;
        if (showLoading) {
            state.isLoadingDevices = true;
            renderDeviceList();
        }
        try {
            const response = await fetch('/api/devices');
            
            // 检查响应状态码
            if (response.status === 500) {
                const errorText = await response.text();
                let errorMessage = '服务器内部错误';
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || errorJson.message || errorMessage;
                } catch (e) {
                    errorMessage = errorText || errorMessage;
                }
                showFullScreenError(errorMessage);
                state.devices = [];
                return;
            }
            
            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.devices) {
                state.devices = result.data.devices
                    .map(normalizeDevice)
                    .filter(Boolean);
                // 如果之前有错误提示，隐藏它
                hideFullScreenError();
            } else {
                state.devices = [];
            }
        } catch (error) {
            console.error('加载设备列表失败:', error);
            // 如果是网络错误，也显示全屏错误提示
            showFullScreenError('网络连接失败: ' + (error.message || '未知错误'));
            state.devices = [];
        } finally {
            if (showLoading) {
                state.isLoadingDevices = false;
            }
        }
        
        if (state.selectedDevice) {
            const currentSn = getDeviceSn(state.selectedDevice);
            state.selectedDevice = state.devices.find(d => getDeviceSn(d) === currentSn) || null;
            // 确保选中设备所在的分组展开
            if (state.selectedDevice) {
                const model = state.selectedDevice.model || state.selectedDevice.type || 'unknown';
                state.expandedModels.add(model);
            }
        } else {
            // 如果没有选中设备，默认展开所有分组
            const models = new Set(state.devices.map(d => d.model || d.type || 'unknown'));
            models.forEach(model => state.expandedModels.add(model));
        }
        
        renderDeviceList();
        if (updateDetail) {
            renderDeviceDetail();
        }
    }

    function startAutoRefresh() {
        stopAutoRefresh();
        autoRefreshTimer = setInterval(() => {
            loadDevices({ showLoading: false, updateDetail: false });
        }, 10000); // 每10秒刷新一次
    }

    function stopAutoRefresh() {
        if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
        }
    }

    function parseJSONSafe(value) {
        try {
            return JSON.parse(value);
        } catch (error) {
            return null;
        }
    }

    // 获取设备的 channel_map 配置
    function getDeviceChannelMap(device) {
        if (!device || !device.configItems) return null;
        
        const configItems = Array.isArray(device.configItems) 
            ? device.configItems 
            : Object.values(device.configItems || {});
        
        const channelMapItem = configItems.find(item => item && item.field === 'channel_map');
        if (channelMapItem) {
            const rawValue = channelMapItem.value ?? channelMapItem.default ?? {};
            return typeof rawValue === 'string' ? parseJSONSafe(rawValue) : rawValue;
        }
        
        const paramValue = device?.parameters?.channel_map;
        if (paramValue !== undefined) {
            return typeof paramValue === 'string' ? parseJSONSafe(paramValue) : paramValue;
        }
        
        return null;
    }

    // 收集所有有 channel_map 的设备
    function collectDevicesWithChannelMap() {
        const devicesWithMap = [];
        state.devices.forEach((device) => {
            const mapValue = getDeviceChannelMap(device);
            if (mapValue !== null && typeof mapValue === 'object') {
                devicesWithMap.push({
                    device,
                    map: mapValue
                });
            }
        });
        return devicesWithMap;
    }

    // 显示通道映射弹窗
    async function showChannelMappingModal() {
        if (!elements.channelMappingModal) return;
        elements.channelMappingModal.style.display = 'flex';
        
        // 设置说明链接
        const spaceLink = document.getElementById('channelMappingSpaceLink');
        if (spaceLink) {
            // 从页面标题或设备组标题中获取 group_name
            const groupTitleElement = document.querySelector('.device-group-title a');
            let groupName = 'unknown';
            if (groupTitleElement) {
                const href = groupTitleElement.getAttribute('href');
                const match = href.match(/device_group_name=([^&]+)/);
                if (match) {
                    groupName = match[1];
                } else {
                    groupName = groupTitleElement.textContent.trim();
                }
            }
            // 构建链接URL
            const baseUrl = 'http://127.0.0.1:6886';
            const spaceUrl = `${baseUrl}/groupDetail/parameterManager?device_group_name=${encodeURIComponent(groupName)}`;
            spaceLink.href = spaceUrl;
        }
        
        await renderChannelMappingModal();
    }

    // 隐藏通道映射弹窗
    function hideChannelMappingModal() {
        if (!elements.channelMappingModal) return;
        elements.channelMappingModal.style.display = 'none';
    }

    // 加载实体列表
    async function loadEntityList() {
        if (entityListPromise) {
            return entityListPromise;
        }
        
        entityListPromise = fetch('/api/device-group/entities', {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        })
        .then((res) => {
            if (!res.ok) {
                throw new Error('请求失败');
            }
            return res.json();
        })
        .then((data) => {
            const entities = data?.data?.entities;
            if (Array.isArray(entities) && entities.length > 0) {
                entityList = entities;
            } else {
                entityList = [];
            }
            return entityList;
        })
        .catch((error) => {
            console.error('加载实体列表失败:', error);
            entityList = [];
            return [];
        })
        .finally(() => {
            entityListPromise = null;
        });
        
        return entityListPromise;
    }

    // 解析比特通道值（实体名+通道类型）
    function parseBitChannel(value) {
        // 处理 null 值（控制设备通道未绑定逻辑通道）
        if (value === null || value === undefined) {
            return { entity: '', type: '' };
        }
        if (typeof value !== 'string') {
            return { entity: '', type: '' };
        }
        const trimmed = value.trim();
        if (!trimmed) {
            return { entity: '', type: '' };
        }
        
        // 处理 ADC 类型（以 ADC 结尾）
        if (trimmed.toUpperCase().endsWith('ADC') && trimmed.length > 3) {
            return { entity: trimmed.slice(0, -3), type: 'ADC' };
        }
        
        // 处理其他类型（最后一个字符）
        const lastChar = trimmed.slice(-1).toUpperCase();
        if (CHANNEL_TYPES.includes(lastChar)) {
            return { entity: trimmed.slice(0, -1), type: lastChar };
        }
        
        // 默认类型为 X
        return { entity: trimmed, type: 'X' };
    }

    // 组合比特通道值
    function combineBitChannel(entity, type) {
        if (!entity || !entity.trim()) {
            return '';
        }
        if (type === 'ADC') {
            return `${entity.trim()}ADC`;
        }
        return `${entity.trim()}${type}`;
    }

    // 渲染通道映射表格
    async function renderChannelMappingModal() {
        const content = elements.channelMappingContent;
        const sidebar = elements.channelMappingSidebar;
        if (!content || !sidebar) return;

        // 显示加载状态
        content.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;
        sidebar.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>加载中...</p>
            </div>
        `;

        // 加载实体列表
        await loadEntityList();

        const devicesWithMap = collectDevicesWithChannelMap();
        
        if (devicesWithMap.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <p>当前没有设备包含 channel_map 配置</p>
                </div>
            `;
            sidebar.innerHTML = `
                <div class="empty-state">
                    <p>暂无设备</p>
                </div>
            `;
            return;
        }

        // 为每个设备准备通道列表
        const devicesData = devicesWithMap.map(({ device, map }) => {
            const deviceSn = getDeviceSn(device);
            const deviceName = device.name || device.model || deviceSn;
            const deviceAddr = getDeviceAddress(device);
            
            // 获取该设备的所有通道（从 map 中获取，如果没有则使用预定义的通道）
            const deviceChannels = Object.keys(map || {});
            const allChannels = deviceChannels.length > 0 
                ? deviceChannels 
                : CHANNEL_MAP_KEYS;
            const sortedChannels = Array.from(new Set(allChannels)).sort();
            
            return {
                device,
                deviceSn,
                deviceName,
                deviceAddr,
                map,
                channels: sortedChannels
            };
        });

        // 渲染左侧设备目录
        let sidebarHtml = '<div class="channel-mapping-sidebar-content">';
        sidebarHtml += '<div class="channel-mapping-sidebar-title">设备列表</div>';
        sidebarHtml += '<div class="channel-mapping-sidebar-list">';
        devicesData.forEach((deviceData, index) => {
            const { deviceSn, deviceName, deviceAddr } = deviceData;
            const deviceId = `device-${deviceSn}`;
            sidebarHtml += `
                <div class="channel-mapping-sidebar-item" 
                     data-device-id="${deviceId}"
                     data-device-index="${index}">
                    <div class="sidebar-item-addr">${escapeHtml(deviceAddr)}</div>
                    <div class="sidebar-item-name">${escapeHtml(deviceName)}</div>
                    <div class="sidebar-item-sn">SN: ${escapeHtml(deviceSn)}</div>
                </div>
            `;
        });
        sidebarHtml += '</div>';
        sidebarHtml += '</div>';
        sidebar.innerHTML = sidebarHtml;

        // 绑定目录项点击事件
        sidebar.querySelectorAll('.channel-mapping-sidebar-item').forEach(item => {
            item.addEventListener('click', () => {
                const deviceId = item.dataset.deviceId;
                scrollToDevice(deviceId);
                
                // 更新选中状态
                sidebar.querySelectorAll('.channel-mapping-sidebar-item').forEach(i => {
                    i.classList.remove('active');
                });
                item.classList.add('active');
                
                // 平滑滚动完成后，再次更新选中状态以确保同步
                const table = content.querySelector('.channel-mapping-table');
                if (table) {
                    const checkAfterScroll = () => {
                        setTimeout(() => {
                            updateSidebarActiveItem();
                        }, 500); // 等待平滑滚动完成
                    };
                    checkAfterScroll();
                }
            });
        });

        // 创建表格
        let html = '<div class="channel-mapping-table-wrapper">';
        html += '<table class="channel-mapping-table">';
        
        // 表头
        html += '<thead><tr>';
        html += '<th>设备信息</th>';
        html += '<th>控制设备通道</th>';
        html += '<th>是否绑定到量子器件通道</th>';
        html += '<th>量子器件通道</th>';
        html += '</tr></thead>';
        
        // 表体
        html += '<tbody>';
        devicesData.forEach((deviceData, deviceIndex) => {
            const { device, deviceSn, deviceName, deviceAddr, map, channels } = deviceData;
            const rowCount = channels.length;
            const deviceId = `device-${deviceSn}`;
            
            channels.forEach((channelKey, channelIndex) => {
                html += `<tr class="device-row-group" data-device-sn="${escapeHtml(deviceSn)}" data-device-id="${deviceId}">`;
                
                // 第一列：设备信息（只在第一行显示，使用 rowspan）
                if (channelIndex === 0) {
                    html += `<td class="channel-mapping-device-info" rowspan="${rowCount}" id="${deviceId}">`;
                    html += `<div class="device-info-content">`;
                    html += `<div class="device-info-addr">${escapeHtml(deviceAddr)}</div>`;
                    html += `<div class="device-info-sn">SN: ${escapeHtml(deviceSn)}</div>`;
                    html += `<div class="device-info-name">${escapeHtml(deviceName)}</div>`;
                    html += `</div>`;
                    html += `</td>`;
                }
                
                // 第二列：硬件通道
                html += `<td class="channel-mapping-hw">${escapeHtml(channelKey)}</td>`;
                
                // 第三列：是否绑定复选框
                const value = map[channelKey] !== undefined ? map[channelKey] : null;
                const isBound = value !== null && value !== '';
                const cellId = `channel-mapping-${deviceSn}-${channelKey}`;
                const bindCheckboxId = `${cellId}-bind`;
                
                html += `<td class="channel-mapping-bind-cell">`;
                html += `<label class="channel-mapping-bind-label">`;
                html += `<input 
                    type="checkbox" 
                    id="${bindCheckboxId}" 
                    class="channel-mapping-bind-checkbox" 
                    data-device-sn="${escapeHtml(deviceSn)}"
                    data-channel-key="${escapeHtml(channelKey)}"
                    ${isBound ? 'checked' : ''} />`;
                html += `<span class="channel-mapping-bind-text">绑定</span>`;
                html += `</label>`;
                html += `</td>`;
                
                // 第四列：比特通道（组合输入：实体输入 + 通道类型输入，支持选择和输入）
                const { entity, type } = parseBitChannel(value);
                const entityInputId = `${cellId}-entity`;
                const typeInputId = `${cellId}-type`;
                const entityDatalistId = `${cellId}-entity-list`;
                const typeDatalistId = `${cellId}-type-list`;
                
                html += `<td class="channel-mapping-cell">`;
                html += `<div class="channel-mapping-input-group">`;
                
                // 实体输入（带 datalist）
                html += `<input 
                    type="text" 
                    id="${entityInputId}" 
                    class="channel-mapping-entity-input" 
                    data-device-sn="${escapeHtml(deviceSn)}"
                    data-channel-key="${escapeHtml(channelKey)}"
                    data-input-type="entity"
                    list="${entityDatalistId}"
                    value="${escapeHtml(entity)}"
                    placeholder="输入或选择实体"
                    ${!isBound ? 'disabled' : ''} />`;
                html += `<datalist id="${entityDatalistId}">`;
                entityList.forEach(entityName => {
                    html += `<option value="${escapeHtml(entityName)}">${escapeHtml(entityName)}</option>`;
                });
                html += `</datalist>`;
                
                // 通道类型输入（带 datalist）
                html += `<input 
                    type="text" 
                    id="${typeInputId}" 
                    class="channel-mapping-type-input" 
                    data-device-sn="${escapeHtml(deviceSn)}"
                    data-channel-key="${escapeHtml(channelKey)}"
                    data-input-type="type"
                    list="${typeDatalistId}"
                    value="${escapeHtml(type)}"
                    placeholder="类型"
                    ${!isBound ? 'disabled' : ''} />`;
                html += `<datalist id="${typeDatalistId}">`;
                CHANNEL_TYPES.forEach(channelType => {
                    html += `<option value="${escapeHtml(channelType)}">${escapeHtml(channelType)}</option>`;
                });
                html += `</datalist>`;
                
                html += `</div>`;
                html += `</td>`;
                
                html += '</tr>';
            });
        });
        html += '</tbody>';
        // 添加占位行以填充剩余空间
        html += '<tfoot><tr class="tbody-spacer">';
        html += '<td colspan="4" style="height: 100%; padding: 0; border: none;"></td>';
        html += '</tr></tfoot>';
        html += '</table>';
        html += '</div>';

        content.innerHTML = html;

        // 绑定输入框变化事件
        content.querySelectorAll('.channel-mapping-entity-input, .channel-mapping-type-input').forEach(input => {
            input.addEventListener('input', handleBitChannelChange);
            input.addEventListener('change', handleBitChannelChange);
        });
        
        // 绑定复选框变化事件
        content.querySelectorAll('.channel-mapping-bind-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', handleBindCheckboxChange);
        });

        // 绑定表格行hover事件，实现设备级高亮
        const table = content.querySelector('.channel-mapping-table');
        
        // 动态设置 tbody 高度以占满表格
        const tbody = content.querySelector('.channel-mapping-table tbody');
        const tfoot = content.querySelector('.channel-mapping-table tfoot');
        if (table && tbody) {
            const updateTbodyHeight = () => {
                if (table && tbody) {
                    // 获取表格容器的实际高度（现在没有padding了）
                    const tableWrapper = content.querySelector('.channel-mapping-table-wrapper');
                    const wrapperHeight = tableWrapper?.clientHeight || table.parentElement?.clientHeight || 0;
                    
                    const theadHeight = table.querySelector('thead')?.offsetHeight || 0;
                    const tfootHeight = tfoot?.offsetHeight || 0;
                    const tbodyMinHeight = wrapperHeight - theadHeight - tfootHeight;
                    
                    if (tbodyMinHeight > 0) {
                        tbody.style.minHeight = `${tbodyMinHeight}px`;
                    }
                }
            };
            // 初始设置，使用多个延迟确保DOM完全渲染
            setTimeout(updateTbodyHeight, 0);
            setTimeout(updateTbodyHeight, 100);
            // 窗口大小改变时重新计算
            const resizeHandler = () => {
                setTimeout(updateTbodyHeight, 0);
            };
            window.addEventListener('resize', resizeHandler);
            // 存储resize handler以便后续清理（如果需要）
            if (!table._resizeHandler) {
                table._resizeHandler = resizeHandler;
            }
        }
        if (table) {
            const rows = table.querySelectorAll('tbody tr.device-row-group');
            rows.forEach(row => {
                row.addEventListener('mouseenter', () => {
                    const deviceSn = row.dataset.deviceSn;
                    if (deviceSn) {
                        // 为该设备的所有行添加hover类
                        rows.forEach(r => {
                            if (r.dataset.deviceSn === deviceSn) {
                                r.classList.add('device-row-hover');
                            }
                        });
                    }
                });
                row.addEventListener('mouseleave', () => {
                    const deviceSn = row.dataset.deviceSn;
                    if (deviceSn) {
                        // 移除该设备所有行的hover类
                        rows.forEach(r => {
                            if (r.dataset.deviceSn === deviceSn) {
                                r.classList.remove('device-row-hover');
                            }
                        });
                    }
                });
            });
        }

        // 监听表格滚动，更新目录选中状态
        if (table) {
            table.addEventListener('scroll', () => {
                updateSidebarActiveItem();
            });
            
            // 初始化选中状态
            setTimeout(() => {
                updateSidebarActiveItem();
                // 默认选中第一个设备
                const firstItem = sidebar.querySelector('.channel-mapping-sidebar-item');
                if (firstItem) {
                    firstItem.classList.add('active');
                }
            }, 100);
        }
    }

    // 滚动到指定设备
    function scrollToDevice(deviceId) {
        const content = elements.channelMappingContent;
        if (!content) return;
        
        const deviceElement = content.querySelector(`#${deviceId}`);
        if (!deviceElement) return;
        
        const table = content.querySelector('.channel-mapping-table');
        if (!table) return;
        
        // 计算目标位置（设备元素相对于表格容器的位置）
        const tableRect = table.getBoundingClientRect();
        const deviceRect = deviceElement.getBoundingClientRect();
        const scrollTop = table.scrollTop;
        const targetScrollTop = scrollTop + deviceRect.top - tableRect.top - 20; // 20px 偏移量
        
        table.scrollTo({
            top: targetScrollTop,
            behavior: 'smooth'
        });
    }

    // 更新目录选中状态（根据当前滚动位置）
    function updateSidebarActiveItem() {
        const content = elements.channelMappingContent;
        const sidebar = elements.channelMappingSidebar;
        if (!content || !sidebar) return;
        
        const table = content.querySelector('.channel-mapping-table');
        if (!table) return;
        
        const scrollTop = table.scrollTop;
        const tableRect = table.getBoundingClientRect();
        const viewportCenter = scrollTop + tableRect.height / 2;
        
        // 找到当前视口中心对应的设备
        const deviceElements = content.querySelectorAll('.channel-mapping-device-info[id^="device-"]');
        let activeDeviceId = null;
        
        deviceElements.forEach(element => {
            // 使用 getBoundingClientRect() 获取相对于视口的位置，然后转换为相对于滚动容器的位置
            const elementRect = element.getBoundingClientRect();
            const elementTop = scrollTop + (elementRect.top - tableRect.top);
            const elementHeight = elementRect.height;
            const elementBottom = elementTop + elementHeight;
            
            if (viewportCenter >= elementTop && viewportCenter <= elementBottom) {
                activeDeviceId = element.id;
            }
        });
        
        // 如果没有找到，找最接近的设备
        if (!activeDeviceId && deviceElements.length > 0) {
            let minDistance = Infinity;
            deviceElements.forEach(element => {
                const elementRect = element.getBoundingClientRect();
                const elementTop = scrollTop + (elementRect.top - tableRect.top);
                const distance = Math.abs(elementTop - viewportCenter);
                if (distance < minDistance) {
                    minDistance = distance;
                    activeDeviceId = element.id;
                }
            });
        }
        
        // 更新目录选中状态
        if (activeDeviceId) {
            sidebar.querySelectorAll('.channel-mapping-sidebar-item').forEach(item => {
                if (item.dataset.deviceId === activeDeviceId) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
        }
    }

    // 处理比特通道变化
    function handleBitChannelChange(event) {
        const input = event.target;
        const deviceSn = input.dataset.deviceSn;
        const channelKey = input.dataset.channelKey;
        
        // 获取同一行的另一个输入框
        const cellId = `channel-mapping-${deviceSn}-${channelKey}`;
        const entityInput = document.getElementById(`${cellId}-entity`);
        const typeInput = document.getElementById(`${cellId}-type`);
        
        if (!entityInput || !typeInput) return;
        
        // 组合值（这里只是更新，实际保存会在点击保存按钮时进行）
        // 可以在这里添加实时预览或验证逻辑
    }
    
    // 处理绑定复选框变化
    function handleBindCheckboxChange(event) {
        const checkbox = event.target;
        const deviceSn = checkbox.dataset.deviceSn;
        const channelKey = checkbox.dataset.channelKey;
        const isChecked = checkbox.checked;
        
        // 获取对应的输入框
        const cellId = `channel-mapping-${deviceSn}-${channelKey}`;
        const entityInput = document.getElementById(`${cellId}-entity`);
        const typeInput = document.getElementById(`${cellId}-type`);
        
        if (!entityInput || !typeInput) return;
        
        // 根据复选框状态启用/禁用输入框
        entityInput.disabled = !isChecked;
        typeInput.disabled = !isChecked;
        
        // 如果取消绑定，清空输入框
        if (!isChecked) {
            entityInput.value = '';
            typeInput.value = '';
        }
    }

    // 检查比特通道重复
    function checkBitChannelDuplicates(deviceMaps) {
        const bitChannelMap = {}; // 比特通道 -> [{deviceSn, channelKey}, ...]
        
        // 收集所有比特通道及其位置
        Object.entries(deviceMaps).forEach(([deviceSn, channels]) => {
            Object.entries(channels).forEach(([channelKey, bitChannel]) => {
                if (bitChannel && bitChannel.trim()) {
                    if (!bitChannelMap[bitChannel]) {
                        bitChannelMap[bitChannel] = [];
                    }
                    bitChannelMap[bitChannel].push({ deviceSn, channelKey });
                }
            });
        });
        
        // 找出重复的比特通道
        const duplicates = [];
        Object.entries(bitChannelMap).forEach(([bitChannel, locations]) => {
            if (locations.length > 1) {
                duplicates.push({
                    bitChannel,
                    locations
                });
            }
        });
        
        return duplicates;
    }

    // 保存待处理的设备映射数据（用于确认后继续保存）
    let pendingDeviceMaps = null;

    // 显示重复提示对话框
    function showDuplicateWarning(duplicates, deviceMaps) {
        if (!elements.duplicateWarningModal || !elements.duplicateWarningContent) {
            // 如果对话框元素不存在，使用简单的 confirm
            return showDuplicateWarningSimple(duplicates);
        }

        // 保存待处理的数据
        pendingDeviceMaps = deviceMaps;

        // 构建提示内容
        let html = '<div class="duplicate-warning-message">';
        html += '<p>检测到以下比特通道在多个设备通道中重复使用：</p>';
        html += '</div>';
        
        html += '<div class="duplicate-list">';
        duplicates.forEach((dup, index) => {
            html += '<div class="duplicate-item">';
            html += `<div class="duplicate-bit-channel">${index + 1}. 比特通道: <strong>${escapeHtml(dup.bitChannel)}</strong></div>`;
            html += '<div class="duplicate-locations">出现在：</div>';
            html += '<ul class="duplicate-location-list">';
            dup.locations.forEach((loc) => {
                const device = state.devices.find(d => getDeviceSn(d) === loc.deviceSn);
                const deviceName = device ? (device.name || device.model || loc.deviceSn) : loc.deviceSn;
                const deviceAddr = device ? getDeviceAddress(device) : '';
                html += `<li>`;
                html += `<span class="location-device">设备: ${escapeHtml(deviceName)} (SN: ${escapeHtml(loc.deviceSn)})</span>`;
                html += `<span class="location-addr">(${escapeHtml(deviceAddr)})</span>`;
                html += `<span class="location-channel">通道: ${escapeHtml(loc.channelKey)}</span>`;
                html += `</li>`;
            });
            html += '</ul>';
            html += '</div>';
        });
        html += '</div>';
        
        html += '<div class="duplicate-warning-footer">';
        html += '<p>⚠️ 继续保存可能会导致配置冲突，是否继续？</p>';
        html += '</div>';

        elements.duplicateWarningContent.innerHTML = html;
        elements.duplicateWarningModal.style.display = 'flex';
        
        // 返回 Promise，等待用户选择
        return new Promise((resolve) => {
            // 保存 resolve 函数，在用户选择后调用
            elements.duplicateWarningModal._resolvePromise = resolve;
        });
    }

    // 简单版本的重复警告（fallback）
    function showDuplicateWarningSimple(duplicates) {
        let message = '检测到以下比特通道在多个设备通道中重复使用：\n\n';
        
        duplicates.forEach((dup, index) => {
            message += `${index + 1}. 比特通道 "${dup.bitChannel}" 出现在：\n`;
            dup.locations.forEach((loc) => {
                const device = state.devices.find(d => getDeviceSn(d) === loc.deviceSn);
                const deviceName = device ? (device.name || device.model || loc.deviceSn) : loc.deviceSn;
                message += `   - 设备 "${deviceName}" (SN: ${loc.deviceSn}) 的通道 "${loc.channelKey}"\n`;
            });
            message += '\n';
        });
        
        message += '是否继续保存？';
        
        return confirm(message);
    }

    // 隐藏重复警告对话框
    function hideDuplicateWarningModal() {
        if (!elements.duplicateWarningModal) return;
        elements.duplicateWarningModal.style.display = 'none';
        pendingDeviceMaps = null;
    }

    // 处理确认保存（即使有重复）
    function handleConfirmSaveWithDuplicates() {
        // 如果有待处理的数据和 resolve 函数，调用 resolve(true)
        if (elements.duplicateWarningModal && elements.duplicateWarningModal._resolvePromise) {
            const resolve = elements.duplicateWarningModal._resolvePromise;
            elements.duplicateWarningModal._resolvePromise = null;
            hideDuplicateWarningModal();
            resolve(true);
        } else {
            hideDuplicateWarningModal();
        }
    }

    // 处理保存所有通道映射
    async function handleSaveAllChannelMapping() {
        const btn = elements.saveAllChannelMappingBtn;
        if (!btn) return;

        // 收集所有设备的通道映射数据
        const deviceMaps = {};
        const entityInputs = elements.channelMappingContent.querySelectorAll('.channel-mapping-entity-input');
        
        entityInputs.forEach(entityInput => {
            const deviceSn = entityInput.dataset.deviceSn;
            const channelKey = entityInput.dataset.channelKey;
            
            // 获取对应的类型输入框和复选框
            const cellId = `channel-mapping-${deviceSn}-${channelKey}`;
            const typeInput = document.getElementById(`${cellId}-type`);
            const bindCheckbox = document.getElementById(`${cellId}-bind`);
            
            if (!typeInput || !bindCheckbox) return;
            
            // 检查是否绑定
            const isBound = bindCheckbox.checked;
            
            if (!deviceMaps[deviceSn]) {
                deviceMaps[deviceSn] = {};
            }
            
            // 根据复选框状态决定保存值
            if (!isBound) {
                // 如果未绑定，设置为 null（硬件通道不绑定逻辑通道）
                deviceMaps[deviceSn][channelKey] = null;
            } else {
                // 如果绑定，组合实体和类型
                const entity = entityInput.value.trim();
                const type = typeInput.value.trim();
                if (entity) {
                    // 如果类型为空，默认使用 X
                    const finalType = type || 'X';
                    deviceMaps[deviceSn][channelKey] = combineBitChannel(entity, finalType);
                } else {
                    // 如果实体为空但复选框选中，设置为 null（避免保存空字符串）
                    deviceMaps[deviceSn][channelKey] = null;
                }
            }
        });

        if (Object.keys(deviceMaps).length === 0) {
            alert('没有需要保存的数据');
            return;
        }

        // 检查比特通道重复
        const duplicates = checkBitChannelDuplicates(deviceMaps);
        if (duplicates.length > 0) {
            const continueSave = await showDuplicateWarning(duplicates, deviceMaps);
            if (!continueSave) {
                return; // 用户取消保存
            }
            // 用户确认继续，使用保存的数据
            await executeSaveChannelMapping(deviceMaps);
        } else {
            // 没有重复，直接保存
            await executeSaveChannelMapping(deviceMaps);
        }
    }

    // 执行保存通道映射
    async function executeSaveChannelMapping(deviceMaps) {
        const btn = elements.saveAllChannelMappingBtn;
        if (!btn) return;

        // 禁用按钮并显示加载状态
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="button-spinner"></span> 保存中...';

        try {
            // 逐个保存每个设备的通道映射
            let successCount = 0;
            let failCount = 0;
            
            for (const [deviceSn, mapValue] of Object.entries(deviceMaps)) {
                try {
                    await saveChannelMapForDevice(deviceSn, mapValue);
                    successCount++;
                } catch (error) {
                    console.error(`保存设备 ${deviceSn} 的通道映射失败:`, error);
                    failCount++;
                }
            }

            if (failCount === 0) {
                alert(`成功保存 ${successCount} 个设备的通道映射`);
                hideChannelMappingModal();
                // 刷新设备列表
                await loadDevices();
                // 提示用户需要重启 Host Client 并询问是否重启
                await promptRestartHostClient();
            } else {
                alert(`保存完成：成功 ${successCount} 个，失败 ${failCount} 个`);
            }
        } catch (error) {
            console.error('保存通道映射失败:', error);
            alert('保存失败: ' + (error.message || '未知错误'));
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    // 保存单个设备的通道映射
    async function saveChannelMapForDevice(deviceSn, mapValue) {
        const response = await fetch('/api/devices', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sn: deviceSn,
                configValues: {
                    channel_map: mapValue
                }
            })
        });

        const result = await response.json();
        if (!(result.status === 'ok' && result.data && result.data.device)) {
            throw new Error(result.detail || '保存失败');
        }

        const updatedDevice = normalizeDevice(result.data.device);
        if (!updatedDevice) return;

        const deviceIndex = state.devices.findIndex(d => getDeviceSn(d) === deviceSn);
        if (deviceIndex !== -1) {
            state.devices[deviceIndex] = updatedDevice;
        }
        if (state.selectedDevice && getDeviceSn(state.selectedDevice) === deviceSn) {
            state.selectedDevice = updatedDevice;
            renderDeviceDetail();
        }
    }

    // 加载插件状态
    async function loadPluginStatus() {
        const pluginStatusContent = document.getElementById('pluginStatusContent');
        if (!pluginStatusContent) return;

        // 如果已有缓存，直接使用缓存
        if (state.pluginStatusCache) {
            renderPluginStatus(state.pluginStatusCache);
            return;
        }

        try {
            pluginStatusContent.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>加载中...</p>
                </div>
            `;

            const response = await fetch('/api/plugin-status');
            const result = await response.json();
            
            if (result.status === 'ok' && result.data) {
                // 缓存结果
                state.pluginStatusCache = result.data;
                renderPluginStatus(result.data);
            } else {
                pluginStatusContent.innerHTML = `
                    <div class="empty-state">
                        <p>获取插件状态失败</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载插件状态失败:', error);
            pluginStatusContent.innerHTML = `
                <div class="empty-state">
                    <p>加载插件状态失败</p>
                </div>
            `;
        }
    }

    // 渲染插件状态
    function renderPluginStatus(pluginStatus) {
        const pluginStatusContent = document.getElementById('pluginStatusContent');
        if (!pluginStatusContent) return;

        const systemInfo = pluginStatus.system_info || {};
        const deviceModels = pluginStatus.device_models || [];
        const plugins = pluginStatus.plugins || {};
        const networkInterfaces = pluginStatus.network_interfaces || [];

        let html = '<div class="plugin-status-info">';
        
        // 显示系统信息
        if (systemInfo && (systemInfo.pc_username || systemInfo.minjiang_user_name || systemInfo.hostname || systemInfo.main_ip)) {
            html += `
                <div class="plugin-status-item">
                    <div class="plugin-status-label">系统信息</div>
                    <div class="plugin-status-value">
                        ${systemInfo.minjiang_user_name && systemInfo.minjiang_user_name !== 'unknown' ? `
                            <div class="system-info-row">
                                <span class="system-info-label">Minjiang用户:</span>
                                <span class="system-info-value">${escapeHtml(systemInfo.minjiang_user_name)} (ID: ${escapeHtml(String(systemInfo.minjiang_user_id || 'unknown'))})</span>
                            </div>
                        ` : ''}
                        ${systemInfo.pc_username && systemInfo.pc_username !== 'unknown' ? `
                            <div class="system-info-row">
                                <span class="system-info-label">PC用户:</span>
                                <span class="system-info-value">${escapeHtml(systemInfo.pc_username)}</span>
                            </div>
                        ` : ''}
                        ${systemInfo.hostname && systemInfo.hostname !== 'unknown' ? `
                            <div class="system-info-row">
                                <span class="system-info-label">PC名称:</span>
                                <span class="system-info-value">${escapeHtml(systemInfo.hostname)}</span>
                            </div>
                        ` : ''}
                        ${systemInfo.main_ip && systemInfo.main_ip !== 'unknown' ? `
                            <div class="system-info-row">
                                <span class="system-info-label">主要IP:</span>
                                <span class="system-info-value">${escapeHtml(systemInfo.main_ip)}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        // 显示网卡信息
        if (networkInterfaces.length > 0) {
            html += `
                <div class="plugin-status-item">
                    <div class="plugin-status-label">网卡信息</div>
                    <div class="plugin-status-value">
                        ${networkInterfaces.map(iface => `
                            <div class="network-interface-row">
                                <span class="network-interface-name">${escapeHtml(iface.interface || '—')}</span>
                                <span class="network-interface-ip">${escapeHtml(iface.ip || '—')}</span>
                                ${iface.netmask ? `<span class="network-interface-netmask">${escapeHtml(iface.netmask)}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 显示设备型号列表
        if (deviceModels.length > 0) {
            html += `
                <div class="plugin-status-item">
                    <div class="plugin-status-label">支持的设备型号</div>
                    <div class="plugin-status-value">
                        ${deviceModels.map(model => `<span class="plugin-status-tag">${escapeHtml(model)}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        // 显示插件信息
        if (Object.keys(plugins).length > 0) {
            html += `
                <div class="plugin-status-item">
                    <div class="plugin-status-label">插件列表</div>
                    <div class="plugin-status-value">
                        ${Object.entries(plugins).map(([name, desc]) => {
                            let descText = '';
                            if (typeof desc === 'object' && desc !== null) {
                                // 如果是对象，提取版本号等信息
                                const version = desc.plugin_version || desc.version || '';
                                const deviceModels = desc.device_models || [];
                                const parts = [];
                                if (version) {
                                    parts.push(`版本: ${version}`);
                                }
                                if (Array.isArray(deviceModels) && deviceModels.length > 0) {
                                    parts.push(`设备型号: ${deviceModels.join(', ')}`);
                                }
                                descText = parts.length > 0 ? parts.join(' | ') : '';
                            } else if (typeof desc === 'string') {
                                descText = desc;
                            }
                            
                            return `
                                <div class="plugin-info-row">
                                    <span class="plugin-name">${escapeHtml(name)}</span>
                                    ${descText ? `<span class="plugin-desc">${escapeHtml(descText)}</span>` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }

        if (networkInterfaces.length === 0 && deviceModels.length === 0 && Object.keys(plugins).length === 0) {
            html += `
                <div class="empty-state">
                    <p>暂无上位机信息</p>
                </div>
            `;
        }

        html += '</div>';
        pluginStatusContent.innerHTML = html;
    }

    // 渲染设备列表
    function renderDeviceList() {
        if (state.isLoadingDevices) {
            elements.deviceList.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>正在加载设备列表...</p>
                </div>
            `;
            return;
        }

        if (state.devices.length === 0) {
            elements.deviceList.innerHTML = `
                <div class="empty-state">
                    <p>暂无设备</p>
                    <p class="empty-hint">点击"添加设备"或"自动发现"来添加设备</p>
                </div>
            `;
            return;
        }

        // 按 model 分组设备
        const devicesByModel = {};
        state.devices.forEach(device => {
            const model = device.model || device.type || 'unknown';
            if (!devicesByModel[model]) {
                devicesByModel[model] = [];
            }
            devicesByModel[model].push(device);
        });

        // 生成分组 HTML
        const modelGroupsHTML = Object.keys(devicesByModel).sort().map(model => {
            const devices = devicesByModel[model];
            const isExpanded = state.expandedModels.has(model);
            const deviceCount = devices.length;
            
            const devicesHTML = devices.map(device => {
                const deviceStatus = getDeviceStatusValue(device);
                const statusClass = deviceStatus === 'online' ? 'online' : 'offline';
                const deviceSn = getDeviceSn(device);
                const activeClass = state.selectedDevice && getDeviceSn(state.selectedDevice) === deviceSn ? 'active' : '';
                const deviceName = device.name || device.model || `设备 ${deviceSn}`;
                const { addr, port } = resolveDeviceAddressParts(device);
                let deviceAddrText = '—';
                if (addr && port) {
                    deviceAddrText = `${addr}:${port}`;
                } else if (addr) {
                    deviceAddrText = addr;
                } else if (port) {
                    deviceAddrText = `:${port}`;
                }
                
                return `
                    <div class="device-item ${activeClass}" data-device-sn="${deviceSn}">
                        <div class="device-item-header">
                            <div class="device-item-name-row">
                                <span class="device-item-name">${escapeHtml(deviceName)}</span>
                                <span class="device-item-sn-small">(SN/${escapeHtml(deviceSn)})</span>
                            </div>
                            <span class="device-item-status ${statusClass}"></span>
                        </div>
                        <div class="device-item-info">
                            <span class="device-item-addr">${escapeHtml(deviceAddrText)}</span>
                        </div>
                    </div>
                `;
            }).join('');

            return `
                <div class="device-model-group" data-model="${escapeHtml(model)}">
                    <div class="device-model-header" data-model="${escapeHtml(model)}">
                        <span class="device-model-icon">${isExpanded ? '▼' : '▶'}</span>
                        <span class="device-model-name">${escapeHtml(model)}</span>
                        <span class="device-model-count">(${deviceCount})</span>
                    </div>
                    <div class="device-model-content" style="display: ${isExpanded ? 'block' : 'none'}">
                        ${devicesHTML}
                    </div>
                </div>
            `;
        }).join('');

        elements.deviceList.innerHTML = modelGroupsHTML;

        // 为每个分组头部添加点击事件（展开/折叠）
        elements.deviceList.querySelectorAll('.device-model-header').forEach(header => {
            header.addEventListener('click', (e) => {
                e.stopPropagation();
                const model = header.dataset.model;
                if (state.expandedModels.has(model)) {
                    state.expandedModels.delete(model);
                } else {
                    state.expandedModels.add(model);
                }
                renderDeviceList();
            });
        });

        // 为每个设备项添加点击事件
        elements.deviceList.querySelectorAll('.device-item').forEach(item => {
            item.addEventListener('click', () => {
                const deviceSn = item.dataset.deviceSn;
                selectDevice(deviceSn);
            });
        });
    }

    // 选择设备
    function selectDevice(deviceSn) {
        const device = state.devices.find(d => getDeviceSn(d) === deviceSn);
        if (!device) return;

        state.selectedDevice = device;
        renderDeviceList();
        renderDeviceDetail();
    }

    // 渲染设备详情
    function renderDeviceDetail() {
        if (!state.selectedDevice) {
            elements.deviceDetail.innerHTML = `
                <div class="empty-detail">
                    <p>请从左侧选择一个设备</p>
                </div>
            `;
            return;
        }

        const device = state.selectedDevice;
        const configSection = renderDeviceConfig(device);
        const infoSection = renderBasicDeviceInfo(device);
        const statusSection = renderDeviceStatus(device);

        // 生成操作按钮HTML
        const actionButtonsHTML = `
            <div class="detail-section">
                <div class="setting-actions">
                    <div class="setting-actions-left">
                        ${state.isDeletingDevice ? `
                            <button class="button-secondary button-loading" disabled>
                                <span class="button-spinner"></span> 删除中...
                            </button>
                        ` : `
                            <button class="button-secondary" id="deleteDeviceBtn">删除设备</button>
                        `}
                    </div>
                    <div class="setting-actions-right">
                        ${state.isSavingSettings ? `
                            <button class="button-primary button-loading" disabled>
                                <span class="button-spinner"></span> 保存中...
                            </button>
                        ` : `
                            <button class="button-primary" id="saveDeviceSettingsBtn">
                                <span class="button-icon">💾</span> 保存配置
                            </button>
                        `}
                    </div>
                </div>
            </div>
        `;

        elements.deviceDetail.innerHTML = `
            <div class="device-detail-content">
                ${infoSection}

                <div class="tab-navigation">
                    <button class="tab-button ${state.activeTab === 'status' ? 'active' : ''}" data-tab="status">
                        <span class="tab-icon">📊</span>
                        <span class="tab-text">设备状态</span>
                    </button>
                    <button class="tab-button ${state.activeTab === 'config' ? 'active' : ''}" data-tab="config">
                        <span class="tab-icon">⚙️</span>
                        <span class="tab-text">设备配置</span>
                    </button>
                    <button class="tab-button ${state.activeTab === 'actions' ? 'active' : ''}" data-tab="actions">
                        <span class="tab-icon">🎯</span>
                        <span class="tab-text">设备操作</span>
                    </button>
                </div>

                <div class="tab-content">
                    <div class="tab-pane ${state.activeTab === 'status' ? 'active' : ''}" data-tab="status">
                        ${statusSection}
                    </div>

                    <div class="tab-pane ${state.activeTab === 'config' ? 'active' : ''}" data-tab="config">
                        ${actionButtonsHTML}
                        ${configSection}
                    </div>

                    <div class="tab-pane ${state.activeTab === 'actions' ? 'active' : ''}" data-tab="actions">
                        ${renderDeviceActions(device)}
                    </div>
                </div>
            </div>
        `;

        // 为tab按钮添加事件监听
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                switchTab(tab);
            });
        });

        // 为详情页面的按钮添加事件监听
        const saveBtn = document.getElementById('saveDeviceSettingsBtn');
        const deleteBtn = document.getElementById('deleteDeviceBtn');
        const enableSwitch = document.getElementById('config-enable');

        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                saveDeviceSettings();
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                deleteDevice();
            });
        }

        // 为 enable switch 添加即时保存功能
        if (enableSwitch) {
            enableSwitch.addEventListener('change', (e) => {
                const checked = e.target.checked;
                saveEnableStatus(checked);
            });
        }

        // 为设备名称编辑按钮添加事件监听
        setupDeviceNameEdit();

        enhanceConfigInputs();
        setupStickyActions();
        
        // 如果当前 tab 是 actions，加载操作列表
        if (state.activeTab === 'actions' && state.selectedDevice && state.selectedDevice.sn) {
            // 使用 setTimeout 确保 DOM 已完全插入
            setTimeout(() => {
                loadDeviceOperations(state.selectedDevice.sn);
            }, 0);
        }
    }

    // 切换tab
    function switchTab(tab) {
        if (tab === state.activeTab) return;
        state.activeTab = tab;
        renderDeviceDetail();
        
        // 如果切换到 actions tab，加载操作列表
        if (tab === 'actions' && state.selectedDevice && state.selectedDevice.sn) {
            // 使用 setTimeout 确保 DOM 已完全插入
            setTimeout(() => {
                loadDeviceOperations(state.selectedDevice.sn);
            }, 0);
        }
    }

    // 渲染设备状态
    function renderDeviceStatus(device) {
        // 获取设备状态值和数据
        const statusValue = getDeviceStatusValue(device);
        const statusData = getDeviceStatusData(device);
        
        const statusText = statusValue === 'online' ? '在线' : statusValue === 'offline' ? '离线' : '未知';
        const statusClass = statusValue === 'online' ? 'online' : statusValue === 'offline' ? 'offline' : 'unknown';
        
        // 获取设备连接信息
        const connectMode = getDeviceConnectMode(device);
        const address = getDeviceAddress(device);
        
        // 从状态数据中获取信息，如果没有则使用默认值
        const lastSeen = statusData.last_seen || statusData.lastSeen || device.last_seen || device.lastSeen || '—';
        const uptime = statusData.uptime || device.uptime || '—';
        const version = statusData.version || statusData.firmware_version || device.version || device.firmware_version || '—';
        
        // 渲染状态数据中的其他字段
        let statusDataRows = '';
        if (statusData && typeof statusData === 'object') {
            for (const [key, value] of Object.entries(statusData)) {
                // 跳过已经显示的字段
                if (['last_seen', 'lastSeen', 'uptime', 'version', 'firmware_version'].includes(key)) {
                    continue;
                }
                // 跳过空值
                if (value === null || value === undefined || value === '') {
                    continue;
                }
                const label = formatStatusFieldLabel(key);
                const displayValue = formatStatusValue(value);
                statusDataRows += renderStatusInfoRow(label, displayValue);
            }
        }
        
        return `
            <div class="detail-section">
                <h3 class="detail-section-title">连接状态</h3>
                <div class="detail-section-content">
                    <div class="status-card">
                        <div class="status-header">
                            <span class="status-label">设备状态</span>
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                        <div class="status-info-grid">
                            ${renderStatusInfoRow('连接模式', connectMode)}
                            ${renderStatusInfoRow('连接地址', address)}
                            ${renderStatusInfoRow('最后在线', lastSeen)}
                            ${renderStatusInfoRow('运行时长', uptime)}
                            ${renderStatusInfoRow('固件版本', version)}
                            ${statusDataRows}
                        </div>
                    </div>
                </div>
            </div>

            <div class="detail-section">
                <h3 class="detail-section-title">设备信息</h3>
                <div class="detail-section-content basic-info-grid">
                    ${renderBasicInfoRow('设备名称', device.name)}
                    ${renderBasicInfoRow('设备型号', device.model)}
                    ${renderBasicInfoRow('设备SN', getDeviceSn(device))}
                    ${renderBasicInfoRow('设备类型', device.type || '—')}
                </div>
            </div>
        `;
    }

    // 格式化状态字段标签
    function formatStatusFieldLabel(key) {
        // 将下划线命名转换为中文标签
        const labelMap = {
            'temperature': '温度',
            'humidity': '湿度',
            'voltage': '电压',
            'current': '电流',
            'power': '功率',
            'frequency': '频率',
            'error_code': '错误代码',
            'error_message': '错误信息',
            'last_update': '最后更新',
            'connection_time': '连接时间',
            'response_time': '响应时间',
            'cpu_usage': 'CPU使用率',
            'memory_usage': '内存使用率',
            'disk_usage': '磁盘使用率',
        };
        
        if (labelMap[key]) {
            return labelMap[key];
        }
        
        // 如果没有映射，将下划线转换为空格并首字母大写
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // 格式化状态值
    function formatStatusValue(value) {
        if (value === null || value === undefined) {
            return '—';
        }
        if (typeof value === 'boolean') {
            return value ? '是' : '否';
        }
        if (typeof value === 'number') {
            return String(value);
        }
        if (typeof value === 'object') {
            try {
                return JSON.stringify(value, null, 2);
            } catch (e) {
                return String(value);
            }
        }
        return String(value);
    }

    function renderStatusInfoRow(label, value) {
        return `
            <div class="status-info-item">
                <span class="status-info-label">${escapeHtml(label)}</span>
                <span class="status-info-value">${escapeHtml(value || '—')}</span>
            </div>
        `;
    }

    // 渲染设备操作
    function renderDeviceActions(device) {
        if (!device || !device.sn) {
            return `
                <div class="detail-section">
                    <div class="detail-section-content">
                        <div class="empty-config">暂无操作</div>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="detail-section">
                <div class="detail-section-content">
                    <div id="device-operations-container" class="device-operations-container">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div class="loading-spinner-small"></div>
                            <span class="loading-text">加载操作列表...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 加载设备操作列表
    async function loadDeviceOperations(deviceSn) {
        const container = document.getElementById('device-operations-container');
        if (!container) return;
        
        try {
            const response = await fetch(`/api/devices/${encodeURIComponent(deviceSn)}/operations`);
            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.operations) {
                renderOperationsList(container, result.data.operations, deviceSn);
            } else {
                container.innerHTML = '<div class="empty-config">暂无操作</div>';
            }
        } catch (error) {
            console.error('加载设备操作列表失败:', error);
            container.innerHTML = '<div class="empty-config">加载操作列表失败</div>';
        }
    }
    
    // 渲染操作列表
    function renderOperationsList(container, operations, deviceSn) {
        const operationsList = Object.keys(operations);
        
        // 保存操作数据到状态中
        state.operationsData = { operations, deviceSn };
        
        if (operationsList.length === 0) {
            container.innerHTML = '<div class="empty-config">暂无操作</div>';
            return;
        }
        
        // 分离设备操作和全局操作
        const deviceOperations = [];
        const globalOperations = [];
        
        for (const opName of operationsList) {
            const op = operations[opName];
            const source = op.source || 'device';  // 默认为设备操作
            if (source === 'device_manager') {
                globalOperations.push({ name: opName, ...op });
            } else {
                deviceOperations.push({ name: opName, ...op });
            }
        }
        
        let html = '<div class="operations-grid">';
        
        // 先渲染设备操作
        for (const opData of deviceOperations) {
            const opName = opData.name;
            const op = operations[opName];
            const params = op.params || {};
            const paramKeys = Object.keys(params);
            const hasParams = paramKeys.length > 0;
            
            // 获取操作图标
            const icon = getOperationIcon(opName);
            
            html += `
                <div class="operation-card" 
                     data-operation="${opName}" 
                     data-device-sn="${deviceSn}">
                    <div class="operation-card-content">
                        <h3 class="operation-card-title">${escapeHtml(op.title || opName)}</h3>
                        ${op.description ? (() => {
                            let desc = op.description;
                            desc = desc.replace(/需要确认才能执行关机操作[，,。.]?/gi, '');
                            desc = desc.replace(/需要确认才能执行[，,。.]?/gi, '');
                            desc = desc.replace(/需要确认[，,。.]?/gi, '');
                            desc = desc.trim();
                            return desc ? `<p class="operation-card-description">${escapeHtml(desc)}</p>` : '';
                        })() : ''}
                        ${hasParams ? `<div class="operation-card-hint">
                            <span class="operation-card-hint-icon">⚙️</span>
                            <span>需要配置参数</span>
                        </div>` : '<div class="operation-card-hint"><span>无需参数</span></div>'}
                    </div>
                </div>
            `;
        }
        
        // 再渲染全局操作（设备管理器中的操作）
        for (const opData of globalOperations) {
            const opName = opData.name;
            const op = operations[opName];
            const params = op.params || {};
            const paramKeys = Object.keys(params);
            const hasParams = paramKeys.length > 0;
            
            // 获取操作图标
            const icon = getOperationIcon(opName);
            
            html += `
                <div class="operation-card operation-card-global" 
                     data-operation="${opName}" 
                     data-device-sn="${deviceSn}">
                    <div class="operation-card-content">
                        <div class="operation-card-header">
                            <h3 class="operation-card-title">${escapeHtml(op.title || opName)}</h3>
                            <span class="operation-card-label">设备管理器</span>
                        </div>
                        ${op.description ? (() => {
                            let desc = op.description;
                            desc = desc.replace(/需要确认才能执行关机操作[，,。.]?/gi, '');
                            desc = desc.replace(/需要确认才能执行[，,。.]?/gi, '');
                            desc = desc.replace(/需要确认[，,。.]?/gi, '');
                            desc = desc.trim();
                            return desc ? `<p class="operation-card-description">${escapeHtml(desc)}</p>` : '';
                        })() : ''}
                        ${hasParams ? `<div class="operation-card-hint">
                            <span class="operation-card-hint-icon">⚙️</span>
                            <span>需要配置参数</span>
                        </div>` : '<div class="operation-card-hint"><span>无需参数</span></div>'}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
        
        // 绑定卡片点击事件
        container.querySelectorAll('.operation-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // 如果点击的是卡片本身，打开模态框
                if (e.target.closest('.operation-card')) {
                    const operationName = card.dataset.operation;
                    const deviceSn = card.dataset.deviceSn;
                    showOperationModal(operationName, deviceSn, operations);
                }
            });
        });
    }
    
    // 显示操作模态框
    function showOperationModal(operationName, deviceSn, operations) {
        if (!elements.operationModal) return;
        
        const operation = operations[operationName];
        if (!operation) return;
        
        // 设置标题
        elements.operationModalTitle.textContent = operation.title || operationName;
        
        // 设置描述（过滤掉关于确认执行关机操作的描述）
        if (operation.description) {
            let description = operation.description;
            // 移除关于确认执行关机操作的相关描述
            description = description.replace(/需要确认才能执行关机操作[，,。.]?/gi, '');
            description = description.replace(/需要确认才能执行[，,。.]?/gi, '');
            description = description.replace(/需要确认[，,。.]?/gi, '');
            description = description.trim();
            
            if (description) {
                elements.operationModalDescription.innerHTML = `<p>${escapeHtml(description)}</p>`;
                elements.operationModalDescription.style.display = 'block';
            } else {
                elements.operationModalDescription.style.display = 'none';
            }
        } else {
            elements.operationModalDescription.style.display = 'none';
        }
        
        // 渲染参数
        const params = operation.params || {};
        const paramKeys = Object.keys(params);
        
        if (paramKeys.length > 0) {
            elements.operationModalParams.innerHTML = renderOperationParams(operationName, params);
        } else {
            elements.operationModalParams.innerHTML = '<div class="operation-no-params">此操作无需配置参数</div>';
        }
        
        // 保存当前操作信息到状态
        state.currentOperation = {
            operationName,
            deviceSn,
            params
        };
        
        // 显示模态框
        elements.operationModal.style.display = 'flex';
    }
    
    // 隐藏操作模态框
    function hideOperationModal() {
        if (!elements.operationModal) return;
        elements.operationModal.style.display = 'none';
        state.currentOperation = null;
    }
    
    // 处理确认操作
    async function handleConfirmOperation() {
        if (!state.currentOperation) return;
        
        const { operationName, deviceSn } = state.currentOperation;
        
        // 收集参数
        const params = {};
        const paramInputs = elements.operationModalParams.querySelectorAll('[data-param]');
        
        let hasError = false;
        paramInputs.forEach(input => {
            const paramName = input.dataset.param;
            const paramConfig = state.currentOperation.params[paramName];
            const necessary = paramConfig && paramConfig.necessary !== false;
            let value;
            
            if (input.type === 'checkbox') {
                value = input.checked;
            } else if (input.type === 'number') {
                const numValue = input.value ? parseFloat(input.value) : undefined;
                if (necessary && (numValue === undefined || isNaN(numValue))) {
                    hasError = true;
                    input.style.borderColor = '#f87171';
                    return;
                }
                value = numValue;
            } else {
                value = input.value || undefined;
                if (necessary && !value) {
                    hasError = true;
                    input.style.borderColor = '#f87171';
                    return;
                }
            }
            
            if (value !== undefined) {
                params[paramName] = value;
            }
        });
        
        if (hasError) {
            alert('请填写所有必填参数');
            return;
        }
        
        // 禁用按钮并显示加载状态
        elements.confirmOperationBtn.disabled = true;
        const originalText = elements.confirmOperationBtn.innerHTML;
        elements.confirmOperationBtn.innerHTML = '<span class="button-spinner"></span> 执行中...';
        
        try {
            const response = await fetch(`/api/devices/${encodeURIComponent(deviceSn)}/operations/${encodeURIComponent(operationName)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ params })
            });
            
            const result = await response.json();
            
            if (result.status === 'ok' && result.data) {
                const opResult = result.data;
                if (opResult.success !== false) {
                    alert(`操作执行成功: ${opResult.message || '操作已完成'}`);
                    hideOperationModal();
                    
                    // 如果是全局操作（关机、重启、重置IP），刷新设备列表
                    const globalOperations = ['device_manager_shutdown', 'device_manager_reboot', 'device_manager_set_ip'];
                    if (globalOperations.includes(operationName)) {
                        await loadDevices({ showLoading: true, updateDetail: true });
                    } else {
                        // 其他操作，重新加载操作列表
                        if (state.selectedDevice && state.selectedDevice.sn === deviceSn) {
                            loadDeviceOperations(deviceSn);
                        }
                    }
                } else {
                    alert(`操作执行失败: ${opResult.message || '未知错误'}`);
                }
            } else {
                alert(`操作执行失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('执行操作失败:', error);
            alert(`执行操作失败: ${error.message || '网络错误'}`);
        } finally {
            elements.confirmOperationBtn.disabled = false;
            elements.confirmOperationBtn.innerHTML = originalText;
        }
    }
    
    // 获取操作图标
    function getOperationIcon(operationName) {
        const iconMap = {
            'start': '▶️',
            'stop': '⏹️',
            'reset': '🔄',
            'configure': '⚙️',
            'test': '🧪',
            'calibrate': '📐',
            'update': '⬆️',
            'download': '⬇️',
            'upload': '⬆️',
            'read': '📖',
            'write': '✍️',
            'scan': '🔍',
            'discover': '🔎'
        };
        
        const lowerName = operationName.toLowerCase();
        for (const [key, icon] of Object.entries(iconMap)) {
            if (lowerName.includes(key)) {
                return icon;
            }
        }
        
        return '🔧'; // 默认图标
    }
    
    // 渲染操作参数
    function renderOperationParams(operationName, params) {
        let html = '';
        
        for (const [paramName, paramConfig] of Object.entries(params)) {
            const fieldId = `operation-${operationName}-${paramName}`;
            const dtype = paramConfig.dtype || 'string';
            const title = paramConfig.title || paramName;
            const necessary = paramConfig.necessary !== false;
            const defaultValue = paramConfig.default;
            
            html += `<div class="operation-param-item">`;
            html += `<label for="${fieldId}" class="operation-param-label">${escapeHtml(title)}${necessary ? '<span class="required">*</span>' : ''}</label>`;
            
            if (dtype === 'bool') {
                const checked = defaultValue === true || defaultValue === 'true' || defaultValue === 1;
                html += `
                    <div class="operation-param-input">
                        <label class="enable-switch-label-compact" for="${fieldId}">
                            <input type="checkbox" 
                                id="${fieldId}" 
                                class="operation-param-checkbox enable-switch-input-compact" 
                                data-operation="${operationName}"
                                data-param="${paramName}"
                                ${checked ? 'checked' : ''} />
                            <span class="enable-switch-slider-compact"></span>
                        </label>
                    </div>
                `;
            } else if (dtype === 'enum') {
                const options = paramConfig.options || {};
                html += `
                    <select id="${fieldId}" 
                            class="operation-param-select" 
                            data-operation="${operationName}"
                            data-param="${paramName}">
                        ${Object.entries(options).map(([value, label]) => 
                            `<option value="${escapeHtml(value)}" ${value === defaultValue ? 'selected' : ''}>${escapeHtml(label)}</option>`
                        ).join('')}
                    </select>
                `;
            } else if (dtype === 'int' || dtype === 'float') {
                const min = paramConfig.min;
                const max = paramConfig.max;
                html += `
                    <input type="number" 
                           id="${fieldId}" 
                           class="operation-param-input-field" 
                           data-operation="${operationName}"
                           data-param="${paramName}"
                           ${min !== undefined ? `min="${min}"` : ''}
                           ${max !== undefined ? `max="${max}"` : ''}
                           ${defaultValue !== undefined ? `value="${defaultValue}"` : ''}
                           placeholder="${escapeHtml(title)}" />
                `;
            } else {
                // string, dict, list 等
                html += `
                    <input type="text" 
                           id="${fieldId}" 
                           class="operation-param-input-field" 
                           data-operation="${operationName}"
                           data-param="${paramName}"
                           ${defaultValue !== undefined ? `value="${escapeHtml(String(defaultValue))}"` : ''}
                           placeholder="${escapeHtml(title)}" />
                `;
            }
            
            html += `</div>`;
        }
        
        return html;
    }
    
    // 处理执行操作
    async function handleExecuteOperation(event) {
        const btn = event.currentTarget;
        const operationName = btn.dataset.operation;
        const deviceSn = btn.dataset.deviceSn;
        
        // 收集参数
        const params = {};
        const operationItem = btn.closest('.operation-item');
        if (operationItem) {
            const paramInputs = operationItem.querySelectorAll('[data-param]');
            paramInputs.forEach(input => {
                const paramName = input.dataset.param;
                let value;
                
                if (input.type === 'checkbox') {
                    value = input.checked;
                } else if (input.type === 'number') {
                    value = input.value ? parseFloat(input.value) : undefined;
                } else {
                    value = input.value || undefined;
                }
                
                if (value !== undefined) {
                    params[paramName] = value;
                }
            });
        }
        
        // 禁用按钮并显示加载状态
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.innerHTML = '<span class="loading-spinner-small"></span> 执行中...';
        
        try {
            const response = await fetch(`/api/devices/${encodeURIComponent(deviceSn)}/operations/${encodeURIComponent(operationName)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ params })
            });
            
            const result = await response.json();
            
            if (result.status === 'ok' && result.data) {
                const opResult = result.data;
                if (opResult.success) {
                    alert(`操作执行成功: ${opResult.message || '操作已完成'}`);
                    // 可以刷新设备列表或重新加载操作
                } else {
                    alert(`操作执行失败: ${opResult.message || '未知错误'}`);
                }
            } else {
                alert(`操作执行失败: ${result.detail || '未知错误'}`);
            }
        } catch (error) {
            console.error('执行操作失败:', error);
            alert(`执行操作失败: ${error.message || '网络错误'}`);
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    // 显示添加设备模态框
    async function showAddDeviceModal() {
        elements.addDeviceModal.style.display = 'flex';
        elements.addDeviceForm.reset();
        
        // 动态加载设备类型列表
        await loadDeviceTypes();
    }
    
    // 加载设备类型列表
    async function loadDeviceTypes() {
        const deviceTypeSelect = document.getElementById('deviceType');
        if (!deviceTypeSelect) return;
        
        try {
            // 先显示加载状态
            deviceTypeSelect.innerHTML = '<option value="">加载中...</option>';
            deviceTypeSelect.disabled = true;
            
            // 获取插件状态
            const response = await fetch('/api/plugin-status');
            const result = await response.json();
            
            if (result.status === 'ok' && result.data) {
                const deviceModels = result.data.device_models || [];
                
                // 清空并填充选项
                deviceTypeSelect.innerHTML = '<option value="">请选择设备类型</option>';
                
                if (deviceModels.length > 0) {
                    // 按字母顺序排序
                    deviceModels.sort().forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        deviceTypeSelect.appendChild(option);
                    });
                } else {
                    // 如果没有获取到model列表，保留默认选项
                    const defaultOptions = [
                        { value: 'controller', text: '控制器' },
                        { value: 'awg', text: 'AWG' },
                        { value: 'digitizer', text: '数字化仪' },
                        { value: 'switch', text: '开关' },
                        { value: 'other', text: '其他' }
                    ];
                    defaultOptions.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.text;
                        deviceTypeSelect.appendChild(option);
                    });
                }
            } else {
                // 如果获取失败，使用默认选项
                deviceTypeSelect.innerHTML = `
                    <option value="">请选择设备类型</option>
                    <option value="controller">控制器</option>
                    <option value="awg">AWG</option>
                    <option value="digitizer">数字化仪</option>
                    <option value="switch">开关</option>
                    <option value="other">其他</option>
                `;
            }
        } catch (error) {
            console.error('加载设备类型列表失败:', error);
            // 出错时使用默认选项
            deviceTypeSelect.innerHTML = `
                <option value="">请选择设备类型</option>
                <option value="controller">控制器</option>
                <option value="awg">AWG</option>
                <option value="digitizer">数字化仪</option>
                <option value="switch">开关</option>
                <option value="other">其他</option>
            `;
        } finally {
            deviceTypeSelect.disabled = false;
        }
    }

    // 隐藏添加设备模态框
    function hideAddDeviceModal() {
        elements.addDeviceModal.style.display = 'none';
    }

    // 处理添加设备
    async function handleAddDevice() {
        const formData = new FormData(elements.addDeviceForm);
        const deviceName = formData.get('deviceName');
        const deviceType = formData.get('deviceType');
        const deviceSn = formData.get('deviceSn');
        const deviceAddress = formData.get('deviceAddress');
        const devicePort = formData.get('devicePort');
        const deviceDescription = formData.get('deviceDescription');

        if (!deviceName || !deviceType || !deviceAddress) {
            alert('请填写所有必填项（设备名称、设备类型、设备地址）');
            return;
        }

        // 确定要使用的SN
        const finalSn = (deviceSn && deviceSn.trim()) ? deviceSn.trim() : deviceAddress;
        
        // 检查SN是否已存在
        const existingDevice = state.devices.find(d => getDeviceSn(d) === finalSn);
        if (existingDevice) {
            const existingDeviceName = existingDevice.name || existingDevice.model || finalSn;
            alert(`设备SN "${finalSn}" 已存在（设备名称: ${existingDeviceName}），无法重复添加。设备识别基于SN，请使用不同的SN。`);
            return;
        }

        // 获取确认按钮并设置loading状态
        const confirmBtn = elements.confirmAddDeviceBtn;
        const originalText = confirmBtn.textContent;
        const isSubmitting = confirmBtn.disabled;
        
        // 如果正在提交，直接返回
        if (isSubmitting) {
            return;
        }

        // 设置loading状态
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="button-loading-spinner"></span> 添加中...';
        confirmBtn.style.cursor = 'not-allowed';

        try {
            // 构建configValues，包含addr和port
            const configValues = {
                addr: deviceAddress || ''
            };
            
            // 如果提供了端口号，添加到configValues
            if (devicePort && devicePort.trim()) {
                configValues.port = devicePort.trim();
            }
            
            // 构建请求体
            const requestBody = {
                name: deviceName,
                model: deviceType,
                description: deviceDescription || '',
                configValues: configValues,
                sn: finalSn
            }

            const response = await fetch('/api/devices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.device) {
                const newDevice = normalizeDevice(result.data.device);
                if (newDevice) {
                    state.devices.push(newDevice);
                    renderDeviceList();
                    hideAddDeviceModal();
                    
                    // 自动选择新添加的设备
                    selectDevice(getDeviceSn(newDevice));
                } else {
                    alert('添加设备失败: 返回数据无效');
                }
            } else {
                alert('添加设备失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('添加设备失败:', error);
            alert('添加设备失败: ' + error.message);
        } finally {
            // 恢复按钮状态
            confirmBtn.disabled = false;
            confirmBtn.textContent = originalText;
            confirmBtn.style.cursor = '';
        }
    }

    // 执行设备发现（可被刷新按钮调用）
    async function performDiscoverDevices() {
        try {
            const response = await fetch('/api/devices/discover', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.devices) {
                const discoveredDevices = result.data.devices || [];
                showDiscoverModal(discoveredDevices);
                if (discoveredDevices.length === 0) {
                    updateDiscoverMessage('未发现任何设备', 'warning');
                } else {
                    updateDiscoverMessage('请选择要添加的设备', 'info');
                }
            } else {
                showDiscoverModal([]);
                updateDiscoverMessage('自动发现失败: ' + (result.detail || result.msg || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('自动发现失败:', error);
            showDiscoverModal([]);
            updateDiscoverMessage('自动发现失败: ' + error.message, 'error');
        }
    }

    // 自动发现设备
    async function autoDiscoverDevices() {
        // 显示加载状态
        const originalText = elements.autoDiscoverBtn.innerHTML;
        elements.autoDiscoverBtn.disabled = true;
        elements.autoDiscoverBtn.classList.add('button-loading');
        elements.autoDiscoverBtn.innerHTML = `<span class="button-spinner"></span> 发现中...`;
        
        await performDiscoverDevices();
        
        // 恢复按钮状态
        elements.autoDiscoverBtn.disabled = false;
        elements.autoDiscoverBtn.classList.remove('button-loading');
        elements.autoDiscoverBtn.innerHTML = originalText;
    }

    // 处理刷新发现设备
    async function handleRefreshDiscover() {
        const btn = elements.refreshDiscoverBtn;
        if (!btn) return;

        // 显示加载状态
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="button-spinner"></span> 刷新中...';
        
        // 清空当前消息
        updateDiscoverMessage('正在刷新设备列表...', 'info');
        
        try {
            await performDiscoverDevices();
        } finally {
            // 恢复按钮状态
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    // 设置设备名称编辑功能
    function setupDeviceNameEdit() {
        const editBtn = document.getElementById('deviceNameEditBtn');
        const saveBtn = document.getElementById('deviceNameSaveBtn');
        const cancelBtn = document.getElementById('deviceNameCancelBtn');
        const nameDisplay = document.getElementById('deviceNameDisplay');
        const nameInput = document.getElementById('deviceNameInput');
        
        if (!editBtn || !saveBtn || !cancelBtn || !nameDisplay || !nameInput) {
            return;
        }
        
        // 编辑按钮点击事件
        editBtn.addEventListener('click', () => {
            nameDisplay.style.display = 'none';
            editBtn.style.display = 'none';
            nameInput.style.display = 'inline-block';
            saveBtn.style.display = 'inline-block';
            cancelBtn.style.display = 'inline-block';
            nameInput.focus();
            nameInput.select();
        });
        
        // 保存按钮点击事件
        saveBtn.addEventListener('click', async () => {
            const newName = nameInput.value.trim();
            if (newName.length > 20) {
                alert('设备名称不能超过20个字符');
                nameInput.focus();
                return;
            }
            
            await saveDeviceName(newName);
        });
        
        // 取消按钮点击事件
        cancelBtn.addEventListener('click', () => {
            nameInput.value = state.selectedDevice ? (state.selectedDevice.name || '') : '';
            nameDisplay.style.display = 'inline';
            editBtn.style.display = 'inline-block';
            nameInput.style.display = 'none';
            saveBtn.style.display = 'none';
            cancelBtn.style.display = 'none';
        });
        
        // 输入框回车保存
        nameInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const newName = nameInput.value.trim();
                if (newName.length > 20) {
                    alert('设备名称不能超过20个字符');
                    nameInput.focus();
                    return;
                }
                await saveDeviceName(newName);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelBtn.click();
            }
        });
        
        // 限制输入长度
        nameInput.addEventListener('input', (e) => {
            if (e.target.value.length > 20) {
                e.target.value = e.target.value.substring(0, 20);
                alert('设备名称不能超过20个字符');
            }
        });
    }
    
    // 保存设备名称
    async function saveDeviceName(newName) {
        if (!state.selectedDevice) return;
        
        const deviceSn = getDeviceSn(state.selectedDevice);
        const nameInput = document.getElementById('deviceNameInput');
        const nameDisplay = document.getElementById('deviceNameDisplay');
        const editBtn = document.getElementById('deviceNameEditBtn');
        const saveBtn = document.getElementById('deviceNameSaveBtn');
        const cancelBtn = document.getElementById('deviceNameCancelBtn');
        
        // 禁用输入框和按钮
        if (nameInput) nameInput.disabled = true;
        if (saveBtn) saveBtn.disabled = true;
        if (cancelBtn) cancelBtn.disabled = true;
        
        try {
            const response = await fetch('/api/devices', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sn: deviceSn,
                    name: newName
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.device) {
                const updatedDevice = normalizeDevice(result.data.device);
                if (updatedDevice) {
                    // 更新本地设备列表
                    const deviceIndex = state.devices.findIndex(d => getDeviceSn(d) === deviceSn);
                    if (deviceIndex !== -1) {
                        state.devices[deviceIndex] = updatedDevice;
                    }
                    
                    state.selectedDevice = updatedDevice;
                    
                    // 更新显示
                    if (nameDisplay) {
                        nameDisplay.textContent = newName || '—';
                    }
                    if (nameInput) {
                        nameInput.value = newName;
                    }
                    
                    // 恢复显示状态
                    if (nameDisplay) nameDisplay.style.display = 'inline';
                    if (editBtn) editBtn.style.display = 'inline-block';
                    if (nameInput) nameInput.style.display = 'none';
                    if (saveBtn) saveBtn.style.display = 'none';
                    if (cancelBtn) cancelBtn.style.display = 'none';
                    
                    // 刷新设备列表显示
                    renderDeviceList();
                }
            } else {
                alert(`更新设备名称失败: ${result.detail || '未知错误'}`);
                // 恢复输入框和按钮
                if (nameInput) nameInput.disabled = false;
                if (saveBtn) saveBtn.disabled = false;
                if (cancelBtn) cancelBtn.disabled = false;
            }
        } catch (error) {
            console.error('保存设备名称失败:', error);
            alert(`保存设备名称失败: ${error.message || '网络错误'}`);
            // 恢复输入框和按钮
            if (nameInput) nameInput.disabled = false;
            if (saveBtn) saveBtn.disabled = false;
            if (cancelBtn) cancelBtn.disabled = false;
        }
    }

    // 保存设备设置
    async function saveDeviceSettings() {
        if (!state.selectedDevice || state.isDeletingDevice || state.isSavingSettings) return;

        let configValues;
        try {
            configValues = collectConfigValues();
        } catch (error) {
            alert(error.message);
            return;
        }

        state.isSavingSettings = true;
        renderDeviceDetail();

        try {
            const response = await fetch('/api/devices', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sn: getDeviceSn(state.selectedDevice),
                    configValues: configValues
                })
            });

            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.device) {
                const updatedDevice = normalizeDevice(result.data.device);
                if (updatedDevice) {
                    // 更新本地设备列表
                    const deviceSn = getDeviceSn(updatedDevice);
                    const deviceIndex = state.devices.findIndex(d => getDeviceSn(d) === deviceSn);
                    if (deviceIndex !== -1) {
                        state.devices[deviceIndex] = updatedDevice;
                    }
                    
                    state.selectedDevice = updatedDevice;
                }
                renderDeviceList();
                renderDeviceDetail();
                
                alert('配置已保存');
            } else {
                alert('保存配置失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('保存配置失败:', error);
            alert('保存配置失败: ' + error.message);
        } finally {
            state.isSavingSettings = false;
            renderDeviceDetail();
        }
    }

    // 保存 enable 状态（即时保存）
    async function saveEnableStatus(checked) {
        if (!state.selectedDevice || state.isSavingEnable) return;

        // 保存原始状态，以便失败时恢复
        const originalChecked = !checked;
        state.isSavingEnable = true;
        const enableSwitch = document.getElementById('config-enable');
        const enableLabel = enableSwitch ? enableSwitch.parentElement : null;
        
        if (enableSwitch) {
            enableSwitch.disabled = true;
        }
        if (enableLabel) {
            enableLabel.classList.add('enable-switch-saving');
        }

        try {
            const response = await fetch('/api/devices', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sn: getDeviceSn(state.selectedDevice),
                    configValues: {
                        enable: checked
                    }
                })
            });

            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.device) {
                const updatedDevice = normalizeDevice(result.data.device);
                if (updatedDevice) {
                    // 更新本地设备列表
                    const deviceSn = getDeviceSn(updatedDevice);
                    const deviceIndex = state.devices.findIndex(d => getDeviceSn(d) === deviceSn);
                    if (deviceIndex !== -1) {
                        state.devices[deviceIndex] = updatedDevice;
                    }
                    
                    state.selectedDevice = updatedDevice;
                }
                renderDeviceList();
                renderDeviceDetail();
            } else {
                // 保存失败，恢复原状态
                state.isSavingEnable = false;
                const currentSwitch = document.getElementById('config-enable');
                if (currentSwitch) {
                    currentSwitch.checked = originalChecked;
                    currentSwitch.disabled = false;
                }
                const currentLabel = currentSwitch ? currentSwitch.parentElement : null;
                if (currentLabel) {
                    currentLabel.classList.remove('enable-switch-saving');
                }
                alert('保存启用状态失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('保存启用状态失败:', error);
            // 保存失败，恢复原状态
            state.isSavingEnable = false;
            const currentSwitch = document.getElementById('config-enable');
            if (currentSwitch) {
                currentSwitch.checked = originalChecked;
                currentSwitch.disabled = false;
            }
            const currentLabel = currentSwitch ? currentSwitch.parentElement : null;
            if (currentLabel) {
                currentLabel.classList.remove('enable-switch-saving');
            }
            alert('保存启用状态失败: ' + error.message);
        } finally {
            if (!state.isSavingEnable) {
                // 如果已经处理过（失败情况），不再重复处理
                return;
            }
            state.isSavingEnable = false;
            const currentSwitch = document.getElementById('config-enable');
            if (currentSwitch) {
                currentSwitch.disabled = false;
            }
            const currentLabel = currentSwitch ? currentSwitch.parentElement : null;
            if (currentLabel) {
                currentLabel.classList.remove('enable-switch-saving');
            }
        }
    }


    // 删除设备
    async function deleteDevice() {
        if (!state.selectedDevice) return;

        const deviceSn = getDeviceSn(state.selectedDevice);
        const deviceName = state.selectedDevice.name || state.selectedDevice.model || deviceSn;
        if (!confirm(`确定要删除设备 "${deviceName}" (SN: ${deviceSn}) 吗？`)) {
            return;
        }

        try {
            const deviceSn = getDeviceSn(state.selectedDevice);
            state.isDeletingDevice = true;
            renderDeviceDetail();
            const response = await fetch(`/api/devices/${encodeURIComponent(deviceSn)}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.status === 'ok') {
                state.devices = state.devices.filter(d => getDeviceSn(d) !== deviceSn);
                state.selectedDevice = null;
                renderDeviceList();
                renderDeviceDetail();
                alert('设备已删除');
            } else {
                alert('删除设备失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('删除设备失败:', error);
            alert('删除设备失败: ' + error.message);
        } finally {
            state.isDeletingDevice = false;
            renderDeviceDetail();
        }
    }

    // 显示发现结果模态框
    function showDiscoverModal(devices) {
        state.discoveredDevices = devices.map((device, index) => {
            const normalized = normalizeDevice(device) || {};
            const resolvedSn = normalized.sn || `discover_${index}`;
            return {
                ...normalized,
                sn: resolvedSn,
                selected: !normalized.already_exists
            };
        });
        state.discoverSelectAll = true;
        renderDiscoverDeviceList();
        elements.discoverModal.style.display = 'flex';
    }

    function hideDiscoverModal() {
        elements.discoverModal.style.display = 'none';
        state.discoveredDevices = [];
        state.discoverSelectAll = true;
        updateDiscoverMessage('', '');
    }

    // 显示上位机信息模态框
    // 显示重启 Host Client 确认弹窗
    function showRestartHostClientModal() {
        if (!elements.restartHostClientModal) return;
        
        // 重置弹窗状态
        elements.restartHostClientConfirmStage.style.display = 'block';
        elements.restartHostClientExecuteStage.style.display = 'none';
        elements.confirmRestartHostClientBtn.style.display = 'inline-block';
        elements.cancelRestartHostClientBtn.style.display = 'inline-block';
        elements.confirmRestartHostClientBtn.disabled = false;
        
        elements.restartHostClientModal.style.display = 'flex';
    }

    // 隐藏重启 Host Client 弹窗
    function hideRestartHostClientModal() {
        if (!elements.restartHostClientModal) return;
        elements.restartHostClientModal.style.display = 'none';
    }

    // 提示用户需要重启 Host Client 并询问是否重启（用于通道映射保存后）
    async function promptRestartHostClient() {
        showRestartHostClientModal();
    }

    // 从弹窗中执行重启 Host Client
    async function executeRestartHostClientFromModal() {
        if (!elements.restartHostClientModal) return;
        
        // 切换到执行阶段
        elements.restartHostClientConfirmStage.style.display = 'none';
        elements.restartHostClientExecuteStage.style.display = 'block';
        elements.confirmRestartHostClientBtn.style.display = 'none';
        elements.cancelRestartHostClientBtn.style.display = 'none';
        
        // 更新状态显示
        updateRestartStatus('submitting', '正在提交重启指令...', '-', '检测中...', '-');
        
        try {
            // 提交重启指令
            const response = await fetch('/api/host-client/restart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.status === 'ok') {
                const commandId = result.data?.command_id || '-';
                updateRestartStatus('submitted', '重启指令已提交', '已提交', '检测中...', commandId);
                
                // 开始监控状态
                monitorRestartStatus(commandId);
            } else {
                updateRestartStatus('error', '提交重启指令失败', '失败', '未知', '-');
                elements.cancelRestartHostClientBtn.style.display = 'inline-block';
                elements.cancelRestartHostClientBtn.textContent = '关闭';
            }
        } catch (error) {
            console.error('重启 Host Client 失败:', error);
            updateRestartStatus('error', '重启失败: ' + error.message, '失败', '未知', '-');
            elements.cancelRestartHostClientBtn.style.display = 'inline-block';
            elements.cancelRestartHostClientBtn.textContent = '关闭';
        }
    }

    // 更新重启状态显示
    function updateRestartStatus(status, title, commandStatus, hostClientStatus, commandId) {
        if (elements.restartStatusTitle) {
            elements.restartStatusTitle.textContent = title;
        }
        if (elements.restartCommandStatus) {
            elements.restartCommandStatus.textContent = commandStatus;
        }
        if (elements.restartHostClientStatus) {
            elements.restartHostClientStatus.textContent = hostClientStatus;
        }
        if (elements.restartCommandId) {
            elements.restartCommandId.textContent = commandId;
        }
        
        // 更新图标
        if (elements.restartStatusIcon) {
            let iconHtml = '';
            if (status === 'submitting' || status === 'monitoring') {
                iconHtml = '<div class="spinner"></div>';
            } else if (status === 'submitted' || status === 'success') {
                iconHtml = '✅';
            } else if (status === 'error') {
                iconHtml = '❌';
            }
            elements.restartStatusIcon.innerHTML = iconHtml;
        }
    }

    // 监控重启状态
    async function monitorRestartStatus(commandId) {
        if (!commandId || commandId === '-') return;
        
        updateRestartStatus('monitoring', '正在监控重启状态...', '执行中', '检测中...', commandId);
        elements.restartStatusProgress.style.display = 'block';
        
        let checkCount = 0;
        const maxChecks = 60; // 最多检查60次（约5分钟）
        const checkInterval = 5000; // 每5秒检查一次
        
        const checkStatus = async () => {
            checkCount++;
            
            try {
                // 检查指令状态（通过插件状态接口间接判断）
                // 注意：这里我们主要通过检查 Host Client 是否在线来判断重启是否完成
                let commandStatus = '执行中';
                
                // 检查 Host Client 是否在线
                let hostClientStatus = '检测中...';
                let isOnline = false;
                try {
                    const statusResponse = await fetch('/api/plugin-status');
                    const statusResult = await statusResponse.json();
                    if (statusResult.status === 'ok' && statusResult.data) {
                        hostClientStatus = '在线';
                        isOnline = true;
                        // 如果 Host Client 在线，说明重启可能已完成
                        if (checkCount > 3) { // 至少等待几次后，如果在线则认为完成
                            commandStatus = '已完成';
                        }
                    } else {
                        hostClientStatus = '离线';
                        isOnline = false;
                    }
                } catch (error) {
                    hostClientStatus = '检测失败';
                    isOnline = false;
                }
                
                updateRestartStatus('monitoring', '正在监控重启状态...', commandStatus, hostClientStatus, commandId);
                
                // 更新进度
                const progress = Math.min((checkCount / maxChecks) * 100, 95);
                if (elements.restartProgressFill) {
                    elements.restartProgressFill.style.width = `${progress}%`;
                }
                if (elements.restartProgressText) {
                    elements.restartProgressText.textContent = `已等待 ${Math.floor(checkCount * checkInterval / 1000)} 秒...`;
                }
                
                // 如果 Host Client 在线且已等待一段时间，或者达到最大检查次数
                if ((isOnline && checkCount > 3) || checkCount >= maxChecks) {
                    if (isOnline && checkCount > 3) {
                        updateRestartStatus('success', '重启成功！Host Client 已恢复在线', '已完成', '在线', commandId);
                        if (elements.restartProgressFill) {
                            elements.restartProgressFill.style.width = '100%';
                        }
                        if (elements.restartProgressText) {
                            elements.restartProgressText.textContent = '重启完成';
                        }
                    } else {
                        updateRestartStatus('monitoring', '监控超时，请手动检查 Host Client 状态', commandStatus, hostClientStatus, commandId);
                    }
                    elements.cancelRestartHostClientBtn.style.display = 'inline-block';
                    elements.cancelRestartHostClientBtn.textContent = '关闭';
                    return;
                }
                
                // 继续监控
                if (checkCount < maxChecks) {
                    setTimeout(checkStatus, checkInterval);
                }
            } catch (error) {
                console.error('检查重启状态失败:', error);
                updateRestartStatus('error', '检查状态失败: ' + error.message, '未知', '检测失败', commandId);
                elements.cancelRestartHostClientBtn.style.display = 'inline-block';
                elements.cancelRestartHostClientBtn.textContent = '关闭';
            }
        };
        
        // 开始监控
        setTimeout(checkStatus, checkInterval);
    }

    function showPluginStatusModal() {
        elements.pluginStatusModal.style.display = 'flex';
        loadPluginStatus();
    }

    // 隐藏上位机信息模态框
    function hidePluginStatusModal() {
        elements.pluginStatusModal.style.display = 'none';
    }
    
    // 设置上位机信息按钮tooltip
    function setupPluginStatusTooltip() {
        const tooltip = document.getElementById('pluginStatusTooltip');
        const tooltipContent = tooltip ? tooltip.querySelector('.tooltip-content') : null;
        let isLoading = false;
        
        if (!tooltip || !tooltipContent) {
            return;
        }
        
        if (!elements.pluginStatusBtn) {
            return;
        }
        
        elements.pluginStatusBtn.addEventListener('mouseenter', async () => {
            // 检查全局缓存是否有效
            if (state.pluginStatusCache && 
                state.pluginStatusCache.system_info &&
                typeof state.pluginStatusCache.system_info === 'object' && 
                Object.keys(state.pluginStatusCache.system_info).length > 0) {
                // 如果已有缓存，直接显示
                updateTooltipContent(tooltip, tooltipContent, state.pluginStatusCache.system_info);
                return;
            }
            
            if (isLoading) return;
            isLoading = true;
            
            // 显示加载状态
            tooltip.classList.add('loading');
            tooltipContent.style.display = 'none';
            
            try {
                // 获取系统信息（完整数据）
                const response = await fetch('/api/plugin-status');
                const result = await response.json();
                
                if (result.status === 'ok' && result.data) {
                    // 缓存完整的结果
                    state.pluginStatusCache = result.data;
                    
                    if (result.data.system_info) {
                        updateTooltipContent(tooltip, tooltipContent, result.data.system_info);
                    } else {
                        tooltipContent.textContent = '获取系统信息失败';
                        tooltip.classList.remove('loading');
                        tooltipContent.style.display = 'block';
                    }
                } else {
                    tooltipContent.textContent = '获取系统信息失败';
                    tooltip.classList.remove('loading');
                    tooltipContent.style.display = 'block';
                }
            } catch (error) {
                console.error('获取系统信息失败:', error);
                tooltipContent.textContent = '获取系统信息失败: ' + error.message;
                tooltip.classList.remove('loading');
                tooltipContent.style.display = 'block';
            } finally {
                isLoading = false;
            }
        });
    }
    
    // 更新tooltip内容
    function updateTooltipContent(tooltip, tooltipContent, systemInfo) {
        if (!systemInfo || typeof systemInfo !== 'object') {
            tooltipContent.textContent = '系统信息无效';
            tooltip.classList.remove('loading');
            tooltipContent.style.display = 'block';
            return;
        }
        
        // 直接使用值，参考renderPluginStatus的处理方式
        // 如果值为undefined、null、'unknown'或空字符串，则显示'未知'
        const minjiangUser = (systemInfo.minjiang_user_name && 
                             systemInfo.minjiang_user_name !== 'unknown') 
            ? String(systemInfo.minjiang_user_name) 
            : '未知';
        const hostname = (systemInfo.hostname && 
                         systemInfo.hostname !== 'unknown') 
            ? String(systemInfo.hostname) 
            : '未知';
        const mainIp = (systemInfo.main_ip && 
                       systemInfo.main_ip !== 'unknown') 
            ? String(systemInfo.main_ip) 
            : '未知';
        
        tooltipContent.innerHTML = `
            <div class="tooltip-header">
                <div class="tooltip-header-icon">🌐</div>
                <div class="tooltip-header-title">远程 Host Client 信息</div>
            </div>
            <div class="tooltip-body">
                <div class="tooltip-info-item">
                    <span class="tooltip-info-label">
                        <span class="tooltip-info-icon">👤</span>
                        <span>用户</span>
                    </span>
                    <span class="tooltip-info-value">${escapeHtml(minjiangUser)}</span>
                </div>
                <div class="tooltip-info-item">
                    <span class="tooltip-info-label">
                        <span class="tooltip-info-icon">💻</span>
                        <span>计算机</span>
                    </span>
                    <span class="tooltip-info-value">${escapeHtml(hostname)}</span>
                </div>
                <div class="tooltip-info-item">
                    <span class="tooltip-info-label">
                        <span class="tooltip-info-icon">🌐</span>
                        <span>主要IP</span>
                    </span>
                    <span class="tooltip-info-value">${escapeHtml(mainIp)}</span>
                </div>
            </div>
            <div class="tooltip-footer">
                <span class="tooltip-hint">💡 继续点击可以查看详细信息</span>
            </div>
        `;
        tooltip.classList.remove('loading');
        tooltipContent.style.display = 'block';
    }
    
    // 设置上位机信息按钮tooltip

    function renderDiscoverDeviceList() {
        const total = state.discoveredDevices.length;
        const newDevices = state.discoveredDevices.filter(d => !d.already_exists);
        const hasSelectable = newDevices.length > 0;
        const allSelected = hasSelectable && newDevices.every(d => d.selected);
        const hasSelected = newDevices.some(d => d.selected);

        if (elements.discoverSummary) {
            elements.discoverSummary.textContent = total
                ? `共发现 ${total} 台设备，其中 ${newDevices.length} 台可添加`
                : '暂无发现的设备';
        }

        if (!total) {
            elements.discoverDeviceList.innerHTML = `
                <div class="empty-state">
                    <p>暂无发现的设备</p>
                    <p class="empty-hint">点击“自动发现”后将在此显示发现结果</p>
                </div>
            `;
        } else {
            const listHTML = state.discoveredDevices.map((device, index) => {
                const disabled = device.already_exists;
                const checked = device.selected && !disabled ? 'checked' : '';
                const statusClass = disabled ? 'exists' : 'new';
                const statusText = disabled ? '已存在' : '未添加';
                const description = device.description ? `<span class="label">描述</span>${escapeHtml(device.description)}` : '';
                const deviceSn = getDeviceSn(device) || `discover_${index}`;
                const connectMode = getDeviceConnectMode(device);
                const addressText = getDeviceAddress(device);

                return `
                    <div class="discover-device-item ${disabled ? 'disabled' : ''}">
                        <input type="checkbox" data-index="${index}" ${checked} ${disabled ? 'disabled' : ''}>
                        <div class="discover-device-main">
                            <div class="discover-device-title">
                                <span>${escapeHtml(device.name || `设备 ${deviceSn}`)}</span>
                                <span class="discover-status ${statusClass}">${statusText}</span>
                            </div>
                            <div class="discover-device-meta">
                                <span><span class="label">型号</span>${escapeHtml(device.model || device.type || 'other')}</span>
                                <span><span class="label">连接</span>${escapeHtml(connectMode)}</span>
                                <span><span class="label">地址</span>${escapeHtml(addressText)}</span>
                                <span><span class="label">SN</span>${escapeHtml(deviceSn)}</span>
                                ${description ? `<span>${description}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            elements.discoverDeviceList.innerHTML = listHTML;

            elements.discoverDeviceList.querySelectorAll('input[type="checkbox"]').forEach(input => {
                input.addEventListener('change', (event) => {
                    const index = parseInt(event.target.dataset.index, 10);
                    toggleDiscoverSelection(index, event.target.checked);
                });
            });
        }

        elements.selectAllDiscoverBtn.disabled = !hasSelectable || state.isAddingDiscovered;
        elements.selectAllDiscoverBtn.textContent = allSelected ? '取消全选' : '全选新设备';
        updateDiscoverConfirmButton(hasSelected);
    }

    function toggleDiscoverSelection(index, checked) {
        const device = state.discoveredDevices[index];
        if (!device || device.already_exists) return;
        state.discoveredDevices[index] = {
            ...device,
            selected: checked
        };
        renderDiscoverDeviceList();
    }

    function toggleSelectAllDiscovered() {
        const selectable = state.discoveredDevices.filter(d => !d.already_exists);
        if (selectable.length === 0) return;
        const allSelected = selectable.every(d => d.selected);
        state.discoveredDevices = state.discoveredDevices.map(device => {
            if (device.already_exists) return device;
            return {
                ...device,
                selected: !allSelected
            };
        });
        renderDiscoverDeviceList();
    }

    async function handleAddDiscoveredDevices() {
        const selectedDevices = state.discoveredDevices.filter(device => device.selected && !device.already_exists);
        if (selectedDevices.length === 0) {
            updateDiscoverMessage('请选择至少一个未添加的设备', 'warning');
            updateDiscoverConfirmButton(false);
            return;
        }

        state.isAddingDiscovered = true;
        updateDiscoverConfirmButton(true);
        updateDiscoverMessage('正在添加所选设备...', 'info');

        let successCount = 0;
        for (const device of selectedDevices) {
            try {
                const configValues = extractDeviceConfigValues(device);
                const addResponse = await fetch('/api/devices', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        sn: getDeviceSn(device),
                        name: device.name || device.model || '新设备',
                        model: device.model || device.type || 'other',
                        create_uid: device.create_uid || 0,
                        configValues
                    })
                });
                const addResult = await addResponse.json();
                if (addResult.status === 'ok' && addResult.data && addResult.data.device) {
                    successCount += 1;
                }
            } catch (error) {
                const deviceSn = getDeviceSn(device);
                console.error(`添加设备 ${device.name || deviceSn} (SN: ${deviceSn}) 失败:`, error);
            }
        }

        if (successCount > 0) {
            await loadDevices();
            updateDiscoverMessage(`成功添加 ${successCount} 个设备`, 'success');
            state.discoveredDevices = state.discoveredDevices.map(device => {
                const deviceSn = getDeviceSn(device);
                if (selectedDevices.find(selected => getDeviceSn(selected) === deviceSn)) {
                    return { ...device, already_exists: true, selected: false };
                }
                return device;
            });
            renderDiscoverDeviceList();
            setTimeout(() => {
                hideDiscoverModal();
            }, 1200);
        } else {
            updateDiscoverMessage('未能添加所选设备，请重试', 'error');
        }

        state.isAddingDiscovered = false;
        const hasSelected = state.discoveredDevices.some(device => device.selected && !device.already_exists);
        updateDiscoverConfirmButton(hasSelected);
    }

    function updateDiscoverMessage(message, type) {
        if (!elements.discoverMessage) return;
        if (!message) {
            elements.discoverMessage.textContent = '';
            elements.discoverMessage.className = 'discover-message';
            elements.discoverMessage.style.display = 'none';
            return;
        }
        elements.discoverMessage.textContent = message;
        elements.discoverMessage.className = `discover-message ${type}`;
        elements.discoverMessage.style.display = 'block';
    }
    function updateDiscoverConfirmButton(hasSelected = false) {
        const btn = elements.confirmDiscoverBtn;
        if (!btn) {
            return;
        }
        if (state.isAddingDiscovered) {
            btn.disabled = true;
            btn.classList.add('button-loading');
            btn.innerHTML = `<span class="button-spinner"></span> 添加中...`;
        } else {
            btn.disabled = !hasSelected;
            btn.classList.remove('button-loading');
            btn.innerHTML = '添加所选设备';
        }
    }

    function getDeviceSn(device) {
        if (!device) return '';
        return device.sn || device.id || '';
    }

    function normalizeDevice(device) {
        if (!device) return null;
        const sn = getDeviceSn(device);
        const configItems = normalizeConfigItems(device.configItems);
        return { ...device, sn, configItems };
    }

    function normalizeConfigItems(items) {
        if (!items) return [];
        if (Array.isArray(items)) {
            return items.map(item => ({ ...item }));
        }
        if (typeof items === 'object') {
            return Object.keys(items).map(field => ({
                field,
                ...items[field]
            }));
        }
        return [];
    }

    function formatConfigValue(value) {
        if (value === null || value === undefined) return '—';
        if (typeof value === 'boolean') {
            return value ? '是' : '否';
        }
        if (Array.isArray(value) || typeof value === 'object') {
            try {
                return JSON.stringify(value);
            } catch (error) {
                return String(value);
            }
        }
        return String(value);
    }

    function formatConfigOptions(options) {
        if (!options) return '';
        if (Array.isArray(options)) {
            return options.join(', ');
        }
        if (typeof options === 'object') {
            return Object.entries(options)
                .map(([key, label]) => `${key}:${label}`)
                .join(', ');
        }
        return String(options);
    }

    function getDeviceConnectMode(device) {
        return device.connection?.connect_mode
            || device.parameters?.connect_mode
            || getDeviceConfigValue(device, 'connect_mode')
            || 'unknown';
    }

    function extractDeviceConfigValues(device) {
        const result = {};
        if (!device) return result;
        const items = device.configItems;
        if (Array.isArray(items)) {
            items.forEach(item => {
                if (!item || !item.field) return;
                if (item.value !== undefined && item.value !== null && item.value !== '') {
                    result[item.field] = item.value;
                } else if (item.default !== undefined) {
                    result[item.field] = item.default;
                }
            });
        } else if (typeof items === 'object' && items !== null) {
            Object.keys(items).forEach(field => {
                const item = items[field];
                if (!item) return;
                if (item.value !== undefined && item.value !== null && item.value !== '') {
                    result[field] = item.value;
                } else if (item.default !== undefined) {
                    result[field] = item.default;
                }
            });
        }
        return result;
    }

    function getDeviceAddress(device) {
        const { addr, port } = resolveDeviceAddressParts(device);
        if (addr && port) {
            return `${addr}:${port}`;
        }
        if (addr) {
            return addr;
        }
        if (port) {
            return port;
        }
        return '—';
    }

    function getDeviceAddrOnly(device) {
        const { addr } = resolveDeviceAddressParts(device);
        return addr || '—';
    }

    function getDevicePort(device) {
        const { port } = resolveDeviceAddressParts(device);
        return port || '—';
    }

    function resolveDeviceAddressParts(device) {
        const addrValue = device.connection?.addr
            || device.parameters?.addr
            || device.address
            || getDeviceConfigValue(device, 'addr')
            || '';
        const portRaw = device.connection?.port
            ?? device.parameters?.port
            ?? getDeviceConfigValue(device, 'port');
        const portValue = (portRaw !== undefined && portRaw !== null && portRaw !== '') ? String(portRaw) : '';
        return {
            addr: addrValue,
            port: portValue
        };
    }

    function enhanceConfigInputs() {
        const autoResizeAreas = document.querySelectorAll('textarea[data-auto-resize="true"]');
        autoResizeAreas.forEach((area) => {
            autoResizeTextarea(area);
            area.addEventListener('input', () => autoResizeTextarea(area));
        });
        if (window.DacReplayContinueEditor && typeof window.DacReplayContinueEditor.initEditors === 'function') {
            window.DacReplayContinueEditor.initEditors();
        }
    }

    // 设置固定操作按钮
    function setupStickyActions() {
        const tabPane = document.querySelector('.tab-pane.active');
        const settingActions = document.querySelector('.setting-actions');
        
        if (!tabPane || !settingActions) return;

        // 移除之前的监听器
        const oldScrollHandler = tabPane._stickyScrollHandler;
        const oldResizeHandler = tabPane._stickyResizeHandler;
        if (oldScrollHandler) {
            tabPane.removeEventListener('scroll', oldScrollHandler);
        }
        if (oldResizeHandler) {
            window.removeEventListener('resize', oldResizeHandler);
        }

        // 获取初始位置和尺寸
        const detailSection = settingActions.closest('.detail-section');
        if (!detailSection) return;

        const actionsHeight = settingActions.offsetHeight;

        // 更新位置的函数（无动画，直接设置）
        const updatePosition = () => {
            const tabPaneRect = tabPane.getBoundingClientRect();
            
            // 计算 tab-pane 相对于视口的位置
            const tabPaneTop = tabPaneRect.top;
            
            // 始终固定在 tab 页顶部（相对于视口）
            // 直接设置，不使用 transition
            settingActions.style.transition = 'none';
            settingActions.style.position = 'fixed';
            settingActions.style.top = tabPaneTop + 'px';
            settingActions.style.left = tabPaneRect.left + 'px';
            settingActions.style.width = tabPaneRect.width + 'px';
            settingActions.style.zIndex = '100';
            
            // 添加占位元素防止内容跳动
            let placeholder = detailSection.querySelector('.sticky-placeholder');
            if (!placeholder) {
                placeholder = document.createElement('div');
                placeholder.className = 'sticky-placeholder';
                detailSection.insertBefore(placeholder, settingActions);
            }
            placeholder.style.height = actionsHeight + 'px';
        };

        // 滚动处理函数
        const handleScroll = () => {
            updatePosition();
        };

        // 窗口大小变化处理函数
        const handleResize = () => {
            updatePosition();
        };

        // 保存处理器引用以便后续移除
        tabPane._stickyScrollHandler = handleScroll;
        tabPane._stickyResizeHandler = handleResize;
        
        tabPane.addEventListener('scroll', handleScroll);
        window.addEventListener('resize', handleResize);

        // 初始设置
        updatePosition();
        
        // 使用 requestAnimationFrame 确保在布局完成后更新
        requestAnimationFrame(() => {
            updatePosition();
        });
    }

    function autoResizeTextarea(textarea) {
        const minHeightAttr = textarea.dataset.autoResizeMin;
        const minHeight = minHeightAttr ? parseInt(minHeightAttr, 10) : 60;
        textarea.style.height = 'auto';
        const newHeight = Math.max(textarea.scrollHeight, minHeight);
        textarea.style.height = `${newHeight}px`;
    }

    // 获取设备状态值（支持字符串或对象格式）
    function getDeviceStatusValue(device) {
        if (!device || !device.status) {
            return 'unknown';
        }
        if (typeof device.status === 'object' && device.status !== null) {
            return device.status.status || 'unknown';
        }
        if (typeof device.status === 'string') {
            return device.status;
        }
        return 'unknown';
    }

    // 获取设备状态数据（如果状态是对象格式）
    function getDeviceStatusData(device) {
        if (!device || !device.status) {
            return {};
        }
        if (typeof device.status === 'object' && device.status !== null) {
            return device.status.data || {};
        }
        return {};
    }

    function getDeviceConfigValue(device, field) {
        if (!device || !device.configItems) return undefined;
        const items = device.configItems;
        if (Array.isArray(items)) {
            const item = items.find(ci => ci && ci.field === field);
            if (!item) return undefined;
            if (item.value !== undefined && item.value !== null && item.value !== '') {
                return item.value;
            }
            return item.default;
        }
        if (typeof items === 'object' && items !== null) {
            const item = items[field];
            if (!item) return undefined;
            if (item.value !== undefined && item.value !== null && item.value !== '') {
                return item.value;
            }
            return item.default;
        }
        return undefined;
    }

    function collectConfigValues() {
        const inputs = document.querySelectorAll('.config-input');
        const values = {};
        inputs.forEach((input) => {
            const field = input.dataset.configField;
            const type = input.dataset.configType || 'str';
            const multi = input.dataset.configMulti === 'true';
            const isComplex = input.dataset.configComplex === 'true';
            if (!field) return;
            const value = parseConfigInputValue(input, type, multi, isComplex);
            if (value !== undefined) {
                values[field] = value;
            }
        });
        return values;
    }

    function parseConfigInputValue(input, type, multi, isComplex) {
        const rawValue = input.value;
        if (type === 'text') {
            return undefined;
        }
        if (multi) {
            const selected = Array.from(input.selectedOptions).map(option => option.value);
            return selected;
        }
        switch (type) {
            case 'bool':
            case 'boolean':
                // 对于 checkbox，使用 checked 属性
                if (input.type === 'checkbox') {
                    return input.checked;
                }
                return rawValue === 'true';
            case 'int':
            case 'integer':
                if (rawValue === '') return null;
                const intVal = parseInt(rawValue, 10);
                if (Number.isNaN(intVal)) {
                    throw new Error(`配置项 ${input.dataset.configField} 需要整数`);
                }
                return intVal;
            case 'float':
                if (rawValue === '') return null;
                const floatVal = parseFloat(rawValue);
                if (Number.isNaN(floatVal)) {
                    throw new Error(`配置项 ${input.dataset.configField} 需要浮点数`);
                }
                return floatVal;
            case 'list':
            case 'dict':
                if (!rawValue.trim()) {
                    return type === 'list' ? [] : {};
                }
                try {
                    const parsed = JSON.parse(rawValue);
                    if (type === 'list' && !Array.isArray(parsed)) {
                        throw new Error(`配置项 ${input.dataset.configField} 需要数组格式`);
                    }
                    if (type === 'dict' && (typeof parsed !== 'object' || Array.isArray(parsed))) {
                        throw new Error(`配置项 ${input.dataset.configField} 需要对象格式`);
                    }
                    return parsed;
                } catch (error) {
                    throw new Error(`配置项 ${input.dataset.configField} JSON 解析失败`);
                }
            default:
                if (isComplex) {
                    try {
                        return JSON.parse(rawValue || '{}');
                    } catch (error) {
                        throw new Error(`配置项 ${input.dataset.configField} JSON 解析失败`);
                    }
                }
                return rawValue;
        }
    }

    // 工具函数：转义HTML
    function escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeAttr(text) {
        if (text == null) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // 显示全屏错误提示
    function showFullScreenError(message) {
        let errorOverlay = document.getElementById('fullScreenErrorOverlay');
        if (!errorOverlay) {
            errorOverlay = document.createElement('div');
            errorOverlay.id = 'fullScreenErrorOverlay';
            errorOverlay.className = 'full-screen-error-overlay';
            errorOverlay.innerHTML = `
                <div class="full-screen-error-content">
                    <div class="full-screen-error-icon">⚠️</div>
                    <h2 class="full-screen-error-title">服务器错误</h2>
                    <p class="full-screen-error-message"></p>
                    <button class="button-primary full-screen-error-button" id="refreshFullScreenErrorBtn">
                        <span class="button-icon">⟳</span>
                        刷新
                    </button>
                </div>
            `;
            document.body.appendChild(errorOverlay);
            
            // 绑定刷新按钮事件
            const refreshBtn = document.getElementById('refreshFullScreenErrorBtn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    hideFullScreenError();
                    loadDevices();
                });
            }
        }
        
        const errorMessageEl = errorOverlay.querySelector('.full-screen-error-message');
        if (errorMessageEl) {
            // 支持多行错误信息，将 \n 转换为 <br>
            errorMessageEl.innerHTML = message.replace(/\n/g, '<br>');
        }
        
        errorOverlay.style.display = 'flex';
    }

    // 隐藏全屏错误提示
    function hideFullScreenError() {
        const errorOverlay = document.getElementById('fullScreenErrorOverlay');
        if (errorOverlay) {
            errorOverlay.style.display = 'none';
        }
    }

    // ==================== 配置文件编辑功能 ====================
    let currentConfigFile = null;
    let configFilesListData = [];

    // 显示编辑配置文件模态框
    function showEditConfigFilesModal() {
        if (elements.editConfigFilesModal) {
            elements.editConfigFilesModal.style.display = 'flex';
            currentConfigFile = null;
            loadConfigFilesList();
            resetConfigFileEditor();
        }
    }

    // 隐藏编辑配置文件模态框
    function hideEditConfigFilesModal() {
        if (elements.editConfigFilesModal) {
            elements.editConfigFilesModal.style.display = 'none';
            currentConfigFile = null;
            resetConfigFileEditor();
        }
    }

    // 重置编辑器
    function resetConfigFileEditor() {
        if (elements.configFileEditor) {
            elements.configFileEditor.textContent = '';
            elements.configFileEditor.contentEditable = 'false';
        }
        if (elements.configFileTitle) {
            elements.configFileTitle.textContent = '请选择一个文件';
        }
        if (elements.saveConfigFileBtn) {
            elements.saveConfigFileBtn.style.display = 'none';
        }
        if (elements.deleteConfigFileBtn) {
            elements.deleteConfigFileBtn.style.display = 'none';
        }
        if (elements.formatConfigFileBtn) {
            elements.formatConfigFileBtn.style.display = 'none';
        }
        hideConfigFileError();
    }
    
    // 格式化JSON
    function formatJSON(jsonString) {
        try {
            const parsed = JSON.parse(jsonString);
            return JSON.stringify(parsed, null, 2);
        } catch (e) {
            // 如果不是有效的JSON，返回原文本
            return jsonString;
        }
    }
    
    // 格式化配置文件
    function formatConfigFile() {
        if (!elements.configFileEditor) return;
        
        const content = elements.configFileEditor.textContent;
        if (!content.trim()) {
            showConfigFileError('文件内容为空');
            return;
        }
        
        try {
            const formatted = formatJSON(content);
            elements.configFileEditor.textContent = formatted;
            hideConfigFileError();
        } catch (e) {
            showConfigFileError('JSON 格式错误: ' + e.message);
        }
    }

    // 加载配置文件列表
    async function loadConfigFilesList() {
        if (!elements.configFilesList) return;
        
        elements.configFilesList.innerHTML = '<div class="empty-state"><p>加载中...</p></div>';
        
        try {
            const response = await fetch('/api/config-files');
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = '获取文件列表失败';
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || errorJson.message || errorMessage;
                } catch (e) {
                    errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`;
                }
                elements.configFilesList.innerHTML = `<div class="empty-state"><p>${escapeHtml(errorMessage)}</p></div>`;
                console.error('获取文件列表失败:', errorMessage);
                return;
            }
            
            const result = await response.json();
            
            if (result.status === 'ok' && result.data) {
                if (result.data.files) {
                    configFilesListData = result.data.files;
                    renderConfigFilesList();
                } else {
                    elements.configFilesList.innerHTML = '<div class="empty-state"><p>获取文件列表失败: 返回数据格式错误</p></div>';
                    console.error('获取文件列表失败: 返回数据格式错误', result);
                }
            } else {
                const errorMsg = result.detail || result.message || '获取文件列表失败';
                elements.configFilesList.innerHTML = `<div class="empty-state"><p>${escapeHtml(errorMsg)}</p></div>`;
                console.error('获取文件列表失败:', result);
            }
        } catch (error) {
            console.error('加载配置文件列表失败:', error);
            elements.configFilesList.innerHTML = '<div class="empty-state"><p>加载失败: ' + escapeHtml(error.message || '网络错误') + '</p></div>';
        }
    }

    // 渲染配置文件列表
    function renderConfigFilesList() {
        if (!elements.configFilesList) return;
        
        if (configFilesListData.length === 0) {
            elements.configFilesList.innerHTML = '<div class="empty-state"><p>暂无 JSON 文件</p></div>';
            return;
        }
        
        const html = configFilesListData.map(file => {
            const isActive = currentConfigFile === file.filename;
            const sizeKB = (file.size / 1024).toFixed(2);
            const modifiedDate = new Date(file.modified * 1000).toLocaleString('zh-CN');
            
            return `
                <div class="config-file-item ${isActive ? 'active' : ''}" data-filename="${escapeHtml(file.filename)}">
                    <div class="config-file-item-name">${escapeHtml(file.filename)}</div>
                    <div class="config-file-item-meta">
                        <span>${sizeKB} KB</span>
                        <span>${modifiedDate}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        elements.configFilesList.innerHTML = html;
        
        // 添加点击事件
        elements.configFilesList.querySelectorAll('.config-file-item').forEach(item => {
            item.addEventListener('click', () => {
                const filename = item.dataset.filename;
                selectConfigFile(filename);
            });
        });
    }

    // 选择配置文件
    async function selectConfigFile(filename) {
        currentConfigFile = filename;
        renderConfigFilesList();
        
        if (elements.configFileTitle) {
            elements.configFileTitle.textContent = filename;
        }
        if (elements.configFileEditor) {
            elements.configFileEditor.textContent = '加载中...';
            elements.configFileEditor.contentEditable = 'false';
        }
        if (elements.saveConfigFileBtn) {
            elements.saveConfigFileBtn.style.display = 'none';
        }
        if (elements.deleteConfigFileBtn) {
            elements.deleteConfigFileBtn.style.display = 'none';
        }
        if (elements.formatConfigFileBtn) {
            elements.formatConfigFileBtn.style.display = 'none';
        }
        hideConfigFileError();
        
        try {
            const response = await fetch(`/api/config-files/${encodeURIComponent(filename)}`);
            const result = await response.json();
            
            if (result.status === 'ok' && result.data && result.data.content !== undefined) {
                if (elements.configFileEditor) {
                    // 格式化并显示JSON
                    const formatted = formatJSON(result.data.content);
                    elements.configFileEditor.textContent = formatted;
                    elements.configFileEditor.contentEditable = 'true';
                }
                if (elements.saveConfigFileBtn) {
                    elements.saveConfigFileBtn.style.display = 'inline-flex';
                }
                if (elements.deleteConfigFileBtn) {
                    elements.deleteConfigFileBtn.style.display = 'inline-flex';
                }
                if (elements.formatConfigFileBtn) {
                    elements.formatConfigFileBtn.style.display = 'inline-flex';
                }
            } else {
                showConfigFileError('获取文件内容失败');
                if (elements.configFileEditor) {
                    elements.configFileEditor.textContent = '';
                }
            }
        } catch (error) {
            console.error('加载文件内容失败:', error);
            showConfigFileError('加载失败: ' + error.message);
            if (elements.configFileEditor) {
                elements.configFileEditor.textContent = '';
            }
        }
    }

    // 保存配置文件
    async function saveConfigFile() {
        if (!currentConfigFile || !elements.configFileEditor) return;
        
        const content = elements.configFileEditor.textContent;
        
        // 验证 JSON 语法
        try {
            JSON.parse(content);
        } catch (e) {
            showConfigFileError('JSON 语法错误: ' + e.message);
            return;
        }
        
        const saveBtn = elements.saveConfigFileBtn;
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="button-loading-spinner"></span> 保存中...';
        
        try {
            const response = await fetch('/api/config-files', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: currentConfigFile,
                    content: content
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'ok') {
                hideConfigFileError();
                // 刷新文件列表
                await loadConfigFilesList();
                alert('文件保存成功');
            } else {
                showConfigFileError('保存失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('保存文件失败:', error);
            showConfigFileError('保存失败: ' + error.message);
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }

    // 删除配置文件
    async function deleteConfigFile() {
        if (!currentConfigFile) return;
        
        if (!confirm(`确定要删除文件 "${currentConfigFile}" 吗？此操作不可恢复。`)) {
            return;
        }
        
        const deleteBtn = elements.deleteConfigFileBtn;
        const originalText = deleteBtn.innerHTML;
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<span class="button-loading-spinner"></span> 删除中...';
        
        try {
            const response = await fetch(`/api/config-files/${encodeURIComponent(currentConfigFile)}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.status === 'ok') {
                currentConfigFile = null;
                resetConfigFileEditor();
                await loadConfigFilesList();
                alert('文件删除成功');
            } else {
                alert('删除失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('删除文件失败:', error);
            alert('删除失败: ' + error.message);
        } finally {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = originalText;
        }
    }

    // 显示添加文件对话框
    function showAddConfigFileDialog() {
        const filename = prompt('请输入新文件名（仅支持 .json 文件）:', 'new_file.json');
        if (!filename) return;
        
        if (!filename.endsWith('.json')) {
            alert('文件名必须以 .json 结尾');
            return;
        }
        
        // 检查文件名是否已存在
        if (configFilesListData.some(f => f.filename === filename)) {
            alert('文件已存在');
            return;
        }
        
        // 创建新文件
        createNewConfigFile(filename);
    }

    // 创建新配置文件
    async function createNewConfigFile(filename) {
        const saveBtn = elements.addConfigFileBtn;
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="button-loading-spinner"></span> 创建中...';
        
        try {
            const response = await fetch('/api/config-files', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: filename,
                    content: '{}'
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'ok') {
                await loadConfigFilesList();
                selectConfigFile(filename);
            } else {
                alert('创建文件失败: ' + (result.detail || '未知错误'));
            }
        } catch (error) {
            console.error('创建文件失败:', error);
            alert('创建文件失败: ' + error.message);
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }

    // 显示错误信息
    function showConfigFileError(message) {
        if (elements.configFileError) {
            elements.configFileError.textContent = message;
            elements.configFileError.style.display = 'block';
        }
    }

    // 隐藏错误信息
    function hideConfigFileError() {
        if (elements.configFileError) {
            elements.configFileError.style.display = 'none';
        }
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

