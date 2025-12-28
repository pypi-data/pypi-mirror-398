(function () {
    'use strict';

    const API_BASE = '/api/host-client';
    const LOG_POLL_INTERVAL_MS = 2000;
    const STATUS_POLL_INTERVAL_MS = 5000; // 状态轮询间隔（5秒）
    const MAX_LOG_LINES = 1500;

    const state = {
        status: 'idle',
        logCursor: 0,
        logTimer: null,
        statusTimer: null, // 状态轮询定时器
        isRunning: false,
        scriptSource: 'manager',
        directLinkPort: null,
        activeTab: 'logs' // 当前激活的 tab
    };

    const elements = {
        statusIndicator: document.querySelector('.status-indicator'),
        statusLabel: document.getElementById('runStatusLabel'),
        runBtn: document.getElementById('runHostClientBtn'),
        stopBtn: document.getElementById('stopHostClientBtn'),
        clearBtn: document.getElementById('clearLogBtn'),
        pathInput: document.getElementById('cloudFilePath'),
        managerPathInput: document.getElementById('scriptManagerPath'),
        portInput: document.getElementById('directLinkPort'),
        logStream: document.getElementById('logStream'),
        scriptSourceChips: document.querySelectorAll('[data-source-mode]'),
        localScriptGroup: document.getElementById('localScriptGroup'),
        managerScriptGroup: document.getElementById('managerScriptGroup'),
        logsTabBtn: document.getElementById('logsTabBtn'),
        webviewTabBtn: document.getElementById('webviewTabBtn'),
        helpTabBtn: document.getElementById('helpTabBtn'),
        logsTab: document.getElementById('logsTab'),
        webviewTab: document.getElementById('webviewTab'),
        helpTab: document.getElementById('helpTab'),
        helpContent: document.getElementById('helpContent'),
        helpToc: document.getElementById('helpToc'),
        tocNav: document.getElementById('tocNav'),
        hostClientIframe: document.getElementById('hostClientIframe'),
        webviewEmpty: document.getElementById('webviewEmpty'),
    };

    function init() {
        bindEvents();
        setScriptSource(state.scriptSource);
        // 初始化时先设置按钮状态（默认停止状态）
        updateButtonStates();
        // 确保 webview 在初始化时保持未加载状态（默认 tab 是 logs）
        if (elements.hostClientIframe && elements.hostClientIframe.src !== 'about:blank') {
            elements.hostClientIframe.src = 'about:blank';
        }
        // 初始化时重置日志（首次加载）
        syncStatus(true);
        initTabs();
        loadConfig();
        // 启动状态轮询，以便检测到重启
        startStatusPolling();
        // 等待 marked 库加载完成后再加载帮助文档
        waitForMarkedAndLoadHelp();
    }

    function waitForMarkedAndLoadHelp() {
        // 检查 marked 是否已加载
        if (typeof marked !== 'undefined') {
            loadHelpDocument();
        } else {
            // 如果未加载，等待一段时间后重试
            let retries = 0;
            const maxRetries = 20; // 最多等待 2 秒（20 * 100ms）
            const checkInterval = setInterval(() => {
                if (typeof marked !== 'undefined') {
                    clearInterval(checkInterval);
                    loadHelpDocument();
                } else {
                    retries++;
                    if (retries >= maxRetries) {
                        clearInterval(checkInterval);
                        if (elements.helpContent) {
                            elements.helpContent.innerHTML = '<div class="help-error">Markdown 解析库加载超时，请刷新页面重试。</div>';
                        }
                    }
                }
            }, 100);
        }
    }

    function initTabs() {
        // Tab 切换事件
        elements.logsTabBtn.addEventListener('click', () => switchTab('logs'));
        elements.webviewTabBtn.addEventListener('click', () => switchTab('webview'));
        elements.helpTabBtn.addEventListener('click', () => switchTab('help'));
    }

    function switchTab(tabName) {
        const previousTab = state.activeTab;
        state.activeTab = tabName;
        
        // 更新按钮状态
        elements.logsTabBtn.classList.toggle('active', tabName === 'logs');
        elements.webviewTabBtn.classList.toggle('active', tabName === 'webview');
        elements.helpTabBtn.classList.toggle('active', tabName === 'help');
        
        // 更新内容区域
        elements.logsTab.classList.toggle('active', tabName === 'logs');
        elements.webviewTab.classList.toggle('active', tabName === 'webview');
        elements.helpTab.classList.toggle('active', tabName === 'help');
        
        // 处理 webview tab 的加载和卸载
        if (tabName === 'webview') {
            // 进入 webview tab，加载 iframe（如果 host client 正在运行）
            if (state.isRunning && state.directLinkPort) {
                updateWebview();
            }
        } else if (previousTab === 'webview') {
            // 离开 webview tab，卸载 iframe
            unloadWebview();
        }
    }

    async function loadHelpDocument() {
        if (!elements.helpContent) {
            return;
        }
        
        try {
            const response = await fetch('/static/help.md');
            if (!response.ok) {
                throw new Error(`加载失败: ${response.status}`);
            }
            
            const markdownText = await response.text();
            
            // 检查 marked 是否可用
            if (typeof marked === 'undefined') {
                elements.helpContent.innerHTML = '<div class="help-error">Markdown 解析库未加载，请刷新页面重试。</div>';
                return;
            }
            
            // 配置 marked 选项
            marked.setOptions({
                breaks: true,
                gfm: true,
            });
            
            // 解析 markdown 为 HTML
            const html = marked.parse(markdownText);
            
            // 渲染到页面
            elements.helpContent.innerHTML = html;
            
            // 处理图片路径（将相对路径转换为绝对路径）
            processImages();
            
            // 处理状态指示器的显示（因为 markdown 中的 HTML 需要特殊处理）
            const statusIndicators = elements.helpContent.querySelectorAll('.status-indicator');
            statusIndicators.forEach(indicator => {
                if (indicator.classList.contains('status-idle')) {
                    indicator.style.background = '#94a3b8';
                    indicator.style.color = '#94a3b8';
                } else if (indicator.classList.contains('status-running')) {
                    indicator.style.background = '#4ade80';
                    indicator.style.color = '#4ade80';
                } else if (indicator.classList.contains('status-stopped')) {
                    indicator.style.background = '#f87171';
                    indicator.style.color = '#f87171';
                }
            });
            
            // 生成目录
            generateTOC();
            
            // 设置滚动监听，高亮当前章节
            setupTOCScroll();
        } catch (error) {
            elements.helpContent.innerHTML = `<div class="help-error">加载帮助文档失败: ${error.message}</div>`;
            if (elements.tocNav) {
                elements.tocNav.innerHTML = '';
            }
        }
    }

    function generateTOC() {
        if (!elements.tocNav || !elements.helpContent) {
            return;
        }
        
        const headings = elements.helpContent.querySelectorAll('h1, h2, h3, h4');
        if (headings.length === 0) {
            elements.tocNav.innerHTML = '<div class="toc-loading">暂无目录</div>';
            return;
        }
        
        const tocItems = [];
        headings.forEach((heading, index) => {
            // 为标题添加 ID（如果没有的话）
            if (!heading.id) {
                const text = heading.textContent.trim();
                const id = 'toc-' + text.toLowerCase()
                    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
                    .replace(/^-+|-+$/g, '') + '-' + index;
                heading.id = id;
            }
            
            const level = parseInt(heading.tagName.charAt(1));
            const text = heading.textContent.trim();
            const id = heading.id;
            
            tocItems.push({ level, text, id });
        });
        
        // 生成目录 HTML
        const tocHTML = tocItems.map(item => {
            const levelClass = `toc-item-h${item.level}`;
            return `<div class="toc-item ${levelClass}" data-id="${item.id}" data-level="${item.level}">${escapeHtml(item.text)}</div>`;
        }).join('');
        
        elements.tocNav.innerHTML = tocHTML;
        
        // 绑定点击事件
        const tocItemsElements = elements.tocNav.querySelectorAll('.toc-item');
        tocItemsElements.forEach(item => {
            item.addEventListener('click', () => {
                const targetId = item.dataset.id;
                const targetElement = elements.helpContent.querySelector(`#${targetId}`);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    function setupTOCScroll() {
        if (!elements.helpContent || !elements.tocNav) {
            return;
        }
        
        const headings = Array.from(elements.helpContent.querySelectorAll('h1, h2, h3, h4'));
        const tocItems = elements.tocNav.querySelectorAll('.toc-item');
        
        if (headings.length === 0 || tocItems.length === 0) {
            return;
        }
        
        let ticking = false;
        
        function updateActiveTOC() {
            if (ticking) return;
            ticking = true;
            
            requestAnimationFrame(() => {
                const contentRect = elements.helpContent.getBoundingClientRect();
                const scrollTop = elements.helpContent.scrollTop;
                const offset = 150; // 偏移量，提前激活
                
                let activeId = null;
                
                // 从下往上查找当前应该激活的标题
                for (let i = headings.length - 1; i >= 0; i--) {
                    const heading = headings[i];
                    const rect = heading.getBoundingClientRect();
                    // 计算标题相对于内容容器的位置
                    const headingTop = rect.top - contentRect.top + scrollTop;
                    
                    if (headingTop <= scrollTop + offset) {
                        activeId = heading.id;
                        break;
                    }
                }
                
                // 如果没找到，使用第一个标题
                if (!activeId && headings.length > 0) {
                    activeId = headings[0].id;
                }
                
                // 更新目录高亮
                tocItems.forEach(item => {
                    if (item.dataset.id === activeId) {
                        item.classList.add('active');
                        // 滚动目录，使当前项可见
                        item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    } else {
                        item.classList.remove('active');
                    }
                });
                
                ticking = false;
            });
        }
        
        // 监听滚动事件
        elements.helpContent.addEventListener('scroll', updateActiveTOC, { passive: true });
        
        // 初始更新一次
        updateActiveTOC();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function processImages() {
        if (!elements.helpContent) {
            return;
        }
        
        const images = elements.helpContent.querySelectorAll('img');
        images.forEach(img => {
            const src = img.getAttribute('src');
            if (!src) {
                return;
            }
            
            // 如果是相对路径，转换为基于 /static/ 的路径
            if (!src.startsWith('http://') && !src.startsWith('https://') && !src.startsWith('/')) {
                img.setAttribute('src', '/static/' + src);
            }
            
            // 添加错误处理
            img.addEventListener('error', function() {
                this.style.display = 'none';
                const errorDiv = document.createElement('div');
                errorDiv.className = 'image-error';
                errorDiv.textContent = `图片加载失败: ${this.getAttribute('src')}`;
                errorDiv.style.cssText = 'color: #f87171; padding: 8px; background: rgba(248, 113, 113, 0.1); border-radius: 4px; margin: 8px 0;';
                this.parentNode.insertBefore(errorDiv, this);
            });
            
            // 添加加载状态
            img.addEventListener('load', function() {
                this.style.opacity = '1';
            });
            
            // 初始设置为透明，加载完成后显示
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.3s ease';
        });
    }

    function updateWebview() {
        // 只在 webview tab 激活时才加载 iframe
        if (state.activeTab !== 'webview') {
            return;
        }
        
        if (state.directLinkPort && state.isRunning) {
            const url = `http://localhost:${state.directLinkPort}`;
            elements.hostClientIframe.src = url;
            elements.hostClientIframe.classList.add('loaded');
            elements.webviewEmpty.classList.add('hidden');
        } else {
            hideWebview();
        }
    }

    function hideWebview() {
        elements.hostClientIframe.src = 'about:blank';
        elements.hostClientIframe.classList.remove('loaded');
        elements.webviewEmpty.classList.remove('hidden');
    }

    function unloadWebview() {
        // 卸载 webview：清空 iframe src，释放资源
        if (elements.hostClientIframe) {
            elements.hostClientIframe.src = 'about:blank';
            elements.hostClientIframe.classList.remove('loaded');
        }
        if (elements.webviewEmpty) {
            elements.webviewEmpty.classList.remove('hidden');
        }
    }

    function bindEvents() {
        elements.runBtn.addEventListener('click', handleRun);
        elements.stopBtn.addEventListener('click', handleStop);
        elements.clearBtn.addEventListener('click', clearLogView);
        elements.scriptSourceChips.forEach(chip => {
            chip.addEventListener('click', () => setScriptSource(chip.dataset.sourceMode));
        });
        
        // 监听输入框变化，自动保存配置
        elements.pathInput.addEventListener('blur', () => {
            if (elements.pathInput.value.trim()) {
                saveConfig();
            }
        });
        elements.managerPathInput.addEventListener('blur', () => {
            if (elements.managerPathInput.value.trim()) {
                saveConfig();
            }
        });
    }

    async function syncStatus(resetLogs = false) {
        try {
            const status = await requestJSON(`${API_BASE}/status`);
            const wasRunning = state.isRunning;
            state.isRunning = Boolean(status.running);
            if (status.direct_link_port) {
                state.directLinkPort = status.direct_link_port;
            }
            
            // 检测状态变化
            const statusChanged = wasRunning !== state.isRunning;
            
            updateStatus(state.isRunning ? 'running' : 'idle');
            
            if (state.isRunning) {
                // 只有在状态从停止变为运行中，或者明确要求重置时才重置日志
                const shouldResetLogs = resetLogs || (!wasRunning && state.isRunning);
                if (shouldResetLogs) {
                    await fetchLogs(true);
                } else {
                    // 状态没变化或只是状态同步，继续从当前 cursor 获取日志
                    await fetchLogs(false);
                }
                startLogPolling();
                updateWebview();
            } else {
                if (statusChanged) {
                    // 状态从运行变为停止，清空日志显示
                    showEmptyLogs();
                }
                hideWebview();
            }
        } catch (error) {
            handleError(error);
        }
    }

    async function loadConfig() {
        try {
            const config = await requestJSON(`${API_BASE}/config`);
            if (config.local_script_path) {
                elements.pathInput.value = config.local_script_path;
            }
            if (config.manager_script_path) {
                elements.managerPathInput.value = config.manager_script_path;
            }
        } catch (error) {
            // 配置不存在或加载失败时静默处理，不显示错误
            console.debug('加载配置失败:', error);
        }
    }

    async function saveConfig() {
        try {
            const groupName = document.body.dataset.groupName || 'unknown';
            const localScriptPath = elements.pathInput.value.trim() || null;
            const managerScriptPath = elements.managerPathInput.value.trim() || null;
            
            await requestJSON(`${API_BASE}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    group_name: groupName,
                    local_script_path: localScriptPath,
                    manager_script_path: managerScriptPath
                })
            });
        } catch (error) {
            // 保存失败时静默处理，不显示错误
            console.debug('保存配置失败:', error);
        }
    }

    async function handleRun() {
        // 如果已经在运行，直接返回
        if (state.isRunning) {
            return;
        }
        
        const scriptPath = state.scriptSource === 'local'
            ? elements.pathInput.value.trim()
            : elements.managerPathInput.value.trim();
        const portValue = parseInt(elements.portInput.value, 10);
        const directLinkPort = Number.isFinite(portValue) ? portValue : 6887;

        if (!scriptPath) {
            if (state.scriptSource === 'local') {
                flashInputError(elements.pathInput);
            } else {
                flashInputError(elements.managerPathInput);
            }
            return;
        }

        try {
            toggleControls(true);
            clearLogView();
            state.logCursor = 0;

            // 从页面获取 group_name（如果可用）
            const groupName = document.body.dataset.groupName || null;
            
            const result = await requestJSON(`${API_BASE}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    script_path: scriptPath,
                    direct_link_port: directLinkPort,
                    group_name: groupName,  // 传递 group_name，如果为 null 则后端会使用配置中的值
                    script_source: state.scriptSource
                })
            });
            
            // 保存端口号
            if (result.direct_link_port) {
                state.directLinkPort = result.direct_link_port;
            } else {
                state.directLinkPort = directLinkPort;
            }

            state.isRunning = true;
            updateStatus('running');
            appendLocalLog('info', '启动请求已发送', `${scriptPath} @ ${directLinkPort}`);
            await fetchLogs(true);
            startLogPolling();
            updateWebview();
            
            // 保存配置
            saveConfig();
        } catch (error) {
            handleError(error);
            state.isRunning = false;
            updateStatus('stopped');
        } finally {
            toggleControls(false);
        }
    }

    async function handleStop() {
        // 如果已经停止，直接返回
        if (!state.isRunning) {
            return;
        }
        
        try {
            toggleControls(true);
            const response = await requestJSON(`${API_BASE}/stop`, { method: 'POST' });
            appendLocalLog('warn', '已发送停止指令', response.running ? '等待进程退出...' : '进程已结束');
            state.isRunning = Boolean(response.running);
            // 无论是否还在运行，都要更新状态和按钮
            updateStatus(state.isRunning ? 'running' : 'stopped');
            if (!state.isRunning) {
                stopLogPolling();
                hideWebview();
            }
        } catch (error) {
            handleError(error);
            // 出错时也要更新按钮状态
            updateButtonStates();
        } finally {
            toggleControls(false);
        }
    }

    async function fetchLogs(resetCursor = false) {
        if (resetCursor) {
            state.logCursor = 0;
            clearLogView();
        }

        const data = await requestJSON(`${API_BASE}/logs?cursor=${state.logCursor}`);
        if (Array.isArray(data.logs) && data.logs.length) {
            appendLogEntries(data.logs);
        }
        state.logCursor = data.cursor ?? state.logCursor;
        const wasRunning = state.isRunning;
        state.isRunning = Boolean(data.running);
        
        // 检测状态变化
        if (wasRunning !== state.isRunning) {
            // 状态发生变化，更新状态显示
            updateStatus(state.isRunning ? 'running' : 'idle');
            
            if (!wasRunning && state.isRunning) {
                // 状态从停止变为运行中，需要完整同步状态（包括 direct_link_port 等）
                // 使用 setTimeout 避免在 fetchLogs 中直接调用 syncStatus 导致的问题
                // 传递 true 表示需要重置日志（因为这是状态变化）
                setTimeout(() => {
                    syncStatus(true).catch(handleError);
                }, 100);
            } else if (wasRunning && !state.isRunning) {
                // 状态从运行变为停止
                hideWebview();
                stopLogPolling();
            }
        } else {
            // 状态没变化，只更新状态显示
            updateStatus(state.isRunning ? 'running' : 'idle');
        }
        
        if (!state.isRunning) {
            hideWebview();
            stopLogPolling();
        }
    }

    function startLogPolling() {
        if (state.logTimer || !state.isRunning) {
            return;
        }
        state.logTimer = setInterval(() => {
            fetchLogs().catch(handleError);
        }, LOG_POLL_INTERVAL_MS);
    }

    function stopLogPolling() {
        if (state.logTimer) {
            clearInterval(state.logTimer);
            state.logTimer = null;
        }
    }

    // 启动状态轮询（即使停止时也定期检查状态，以便检测到重启）
    function startStatusPolling() {
        if (state.statusTimer) {
            return;
        }
        state.statusTimer = setInterval(() => {
            // 状态轮询时不重置日志 cursor，保持当前进度
            syncStatus(false).catch(handleError);
        }, STATUS_POLL_INTERVAL_MS);
    }

    function stopStatusPolling() {
        if (state.statusTimer) {
            clearInterval(state.statusTimer);
            state.statusTimer = null;
        }
    }

    async function requestJSON(url, options = {}) {
        const response = await fetch(url, options);
        if (!response.ok) {
            let message = response.statusText;
            const text = await response.text();
            if (text) {
                try {
                    const data = JSON.parse(text);
                    if (data.detail) {
                        message = data.detail;
                    } else {
                        message = text;
                    }
                } catch {
                    message = text;
                }
            }
            throw new Error(message || '请求失败');
        }
        return response.json();
    }

    function appendLogEntries(entries) {
        if (!entries || !entries.length) {
            return;
        }
        if (elements.logStream.querySelector('.log-empty')) {
            elements.logStream.innerHTML = '';
        }

        const shouldStickBottom = isScrolledToBottom();
        const fragment = document.createDocumentFragment();
        entries.forEach(entry => {
            const lineEl = createLogLine(entry);
            if (lineEl) {
                fragment.appendChild(lineEl);
            }
        });

        elements.logStream.appendChild(fragment);
        enforceLogLimit();
        if (shouldStickBottom) {
            elements.logStream.scrollTop = elements.logStream.scrollHeight;
        }
    }

    function createLogLine(entry) {
        if (!entry || !entry.line) {
            return null;
        }

        const lineEl = document.createElement('div');
        lineEl.className = 'log-line';

        const timeEl = document.createElement('span');
        timeEl.className = 'log-time';
        timeEl.textContent = formatTimestamp(entry.timestamp);

        const contentEl = document.createElement('div');
        contentEl.className = 'log-content';

        const levelEl = document.createElement('span');
        levelEl.className = `log-level ${entry.level || 'info'}`;
        levelEl.textContent = (entry.level || 'info').toLowerCase();

        const textEl = document.createElement('span');
        textEl.textContent = entry.line;

        contentEl.appendChild(levelEl);
        contentEl.appendChild(textEl);

        if (entry.detail) {
            const detailEl = document.createElement('div');
            detailEl.className = 'log-detail';
            detailEl.textContent = entry.detail;
            contentEl.appendChild(detailEl);
        }

        lineEl.appendChild(timeEl);
        lineEl.appendChild(contentEl);
        return lineEl;
    }

    function appendLocalLog(level, message, detail) {
        appendLogEntries([{
            level,
            line: message,
            detail,
            timestamp: new Date().toISOString()
        }]);
    }

    function enforceLogLimit() {
        const stream = elements.logStream;
        if (!stream) return;
        const extra = stream.children.length - MAX_LOG_LINES;
        for (let i = 0; i < extra; i += 1) {
            stream.removeChild(stream.firstChild);
        }
    }

    function isScrolledToBottom() {
        const stream = elements.logStream;
        if (!stream) return true;
        const distance = stream.scrollHeight - stream.scrollTop - stream.clientHeight;
        return distance < 40;
    }

    function updateStatus(status) {
        state.status = status;
        elements.statusIndicator.classList.remove('status-idle', 'status-running', 'status-stopped');

        if (status === 'running') {
            elements.statusIndicator.classList.add('status-running');
            elements.statusLabel.textContent = '运行中';
        } else if (status === 'stopped') {
            elements.statusIndicator.classList.add('status-stopped');
            elements.statusLabel.textContent = '已停止';
        } else {
            elements.statusIndicator.classList.add('status-idle');
            elements.statusLabel.textContent = '空闲';
        }
        
        // 根据运行状态更新按钮的禁用状态
        updateButtonStates();
    }

    function clearLogView() {
        elements.logStream.innerHTML = `
            <div class="log-empty">
                <p>暂无日志</p>
                <p class="setting-hint">点击左侧运行按钮开始采集日志</p>
            </div>
        `;
    }

    function showEmptyLogs() {
        if (!elements.logStream.querySelector('.log-empty')) {
            clearLogView();
        }
    }

    function setScriptSource(source) {
        if (!source) {
            return;
        }
        state.scriptSource = source;
        elements.scriptSourceChips.forEach(chip => {
            const isActive = chip.dataset.sourceMode === source;
            chip.classList.toggle('active', isActive);
        });
        elements.localScriptGroup.classList.toggle('hidden', source !== 'local');
        elements.managerScriptGroup.classList.toggle('hidden', source !== 'manager');
    }

    // removed script manager list fetching

    function handleError(error) {
        appendLocalLog('error', '操作失败', (error && error.message) || '未知错误');
    }

    function flashInputError(input) {
        input.classList.add('input-error');
        setTimeout(() => input.classList.remove('input-error'), 1500);
        input.focus();
    }

    function toggleControls(disabled) {
        // 临时禁用/启用按钮（用于操作进行中）
        if (disabled) {
            elements.runBtn.disabled = true;
            elements.stopBtn.disabled = true;
        } else {
            // 操作完成后，根据实际运行状态更新按钮状态
            updateButtonStates();
        }
    }
    
    function updateButtonStates() {
        // 根据运行状态设置按钮的禁用状态
        // 运行中：禁用运行按钮，启用停止按钮
        // 停止/空闲：启用运行按钮，禁用停止按钮
        const isRunning = state.isRunning;
        elements.runBtn.disabled = isRunning;
        elements.stopBtn.disabled = !isRunning;
    }

    function formatTimestamp(isoString) {
        if (!isoString) {
            return new Date().toLocaleTimeString('zh-CN', { hour12: false });
        }
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) {
            return isoString;
        }
        const time = date.toLocaleTimeString('zh-CN', { hour12: false });
        const ms = date.getMilliseconds().toString().padStart(3, '0');
        return `${time}.${ms}`;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

