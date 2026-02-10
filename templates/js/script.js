// 配置数据
let configData = {{CONFIG_DATA}};
const chineseLabels = {{CHINESE_LABELS}};

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    renderConfigForm();
    
    // 获取当前配置
    fetch('/config')
        .then(response => response.json())
        .then(data => {
            configData = data;
            renderConfigForm();
        })
        .catch(error => {
            showStatus('获取配置失败: ' + error, false);
        });
});

// 显示指定页面
function showPage(pageId) {
    console.log('=== showPage called ===');
    console.log('Page ID:', pageId);
    
    // 1. 移除所有导航项的激活状态
    console.log('1. Removing active class from all nav items');
    const navItems = document.querySelectorAll('.nav-item');
    console.log('Number of nav items:', navItems.length);
    navItems.forEach((item, index) => {
        console.log('Removing active from nav item', index, ':', item.textContent.trim());
        item.classList.remove('active');
    });
    
    // 2. 隐藏所有页面
    console.log('\n2. Hiding all page content');
    const pageContents = document.querySelectorAll('.page-content');
    console.log('Number of page content:', pageContents.length);
    pageContents.forEach((page, index) => {
        console.log('Hiding page content', index, ':', page.id);
        page.style.display = 'none';
    });
    
    // 3. 激活当前导航项
    console.log('\n3. Activating current nav item');
    try {
        // 遍历所有导航项，找到匹配的项
        navItems.forEach((item, index) => {
            // 检查onclick属性是否包含showPage(pageId)
            const onclick = item.getAttribute('onclick');
            console.log('Checking nav item', index, 'onclick:', onclick);
            if (onclick && onclick.includes(`showPage('${pageId}')`)) {
                console.log('Found matching nav item:', pageId);
                item.classList.add('active');
            }
        });
    } catch (error) {
        console.error('Error activating nav item:', error);
    }
    
    // 4. 显示当前页面
    console.log('\n4. Showing current page content');
    try {
        const pageContent = document.getElementById(pageId);
        console.log('Found page content:', pageContent);
        if (pageContent) {
            console.log('Showing page content:', pageId);
            pageContent.style.display = 'block';
            console.log('Page content displayed successfully');
        } else {
            console.error('Page content not found:', pageId);
        }
    } catch (error) {
        console.error('Error displaying page content:', error);
    }
    
    console.log('=== showPage completed ===');
}

// 兼容旧的switchPage函数
function switchPage(pageId) {
    console.log('=== switchPage called (compatibility) ===');
    showPage(pageId);
}

// 初始化选项卡
function initTabs() {
    const tabsContainer = document.getElementById('configTabs');
    const tabsContent = document.getElementById('tabContents');
    
    const tabNames = {
        'file_paths': '文件路径',
        'program_paths': '程序路径',
        'email': '邮箱设置',
        'process_names': '进程名称',
        'timing': '时间设置',
        'gitee': 'Gitee设置',
        'completion': '完成操作'
    };
    
    let firstTab = true;
    for (const [tabId, tabName] of Object.entries(tabNames)) {
        // 创建选项卡按钮
        const tabBtn = document.createElement('button');
        tabBtn.className = `tab-btn ${firstTab ? 'active' : ''}`;
        tabBtn.textContent = tabName;
        tabBtn.dataset.tab = tabId;
        tabBtn.onclick = function() {
            switchTab(tabId);
        };
        tabsContainer.appendChild(tabBtn);
        
        // 创建选项卡内容
        const tabContent = document.createElement('div');
        tabContent.className = `tab-content ${firstTab ? 'active' : ''}`;
        tabContent.id = `tab-${tabId}`;
        tabsContent.appendChild(tabContent);
        
        firstTab = false;
    }
}

// 切换选项卡
function switchTab(tabId) {
    // 移除所有激活状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 激活当前选项卡
    document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active');
}

// 渲染配置表单
function renderConfigForm() {
    // 渲染各个选项卡内容
    renderTabContent('file_paths', '文件路径设置', '不建议修改');
    renderTabContent('program_paths', '程序路径设置', '请根据您的系统设置正确路径');
    renderTabContent('email', '邮箱设置', '用于接收BAAH完成邮件的邮箱配置');
    renderTabContent('process_names', '进程名称设置', '不建议修改');
    renderTabContent('timing', '时间设置', '各项任务的时间间隔配置');
    renderTabContent('gitee', 'Gitee设置', '用于上传报告的Gitee配置');
    renderCompletionTab();
}

// 渲染选项卡内容
function renderTabContent(tabId, title, description) {
    const tabContent = document.getElementById(`tab-${tabId}`);
    const configSection = configData[tabId] || {};
    const labels = chineseLabels[tabId] || {};
    
    let html = `
        <div class="config-group">
            <h3>${title} <span class="field-tip">${description}</span></h3>
            <div class="field-row">
    `;
    
    for (const [key, value] of Object.entries(configSection)) {
        const label = labels[key] || key;
        const fieldId = `${tabId}.${key}`;
        const fieldValue = value === null ? '' : String(value);
        const isReadonly = tabId === 'file_paths' || tabId === 'process_names';
        
        html += `
            <div class="field-group">
                <label for="${fieldId}">
                    ${label}
                    ${isReadonly ? '<span class="field-tip">(只读)</span>' : ''}
                </label>
                <input type="text" 
                       id="${fieldId}" 
                       name="${fieldId}" 
                       value="${escapeHtml(fieldValue)}"
                       ${isReadonly ? 'readonly' : ''}>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
    `;
    
    tabContent.innerHTML = html;
}

// 渲染完成操作选项卡
function renderCompletionTab() {
    const tabContent = document.getElementById('tab-completion');
    const globalAction = configData.task_completion_action || 'none';
    const scheduledActions = configData.scheduled_completion_actions || [];
    
    const actions = [
        {value: 'none', label: '不执行任何操作', icon: 'fas fa-times-circle'},
        {value: 'logout', label: '注销系统', icon: 'fas fa-sign-out-alt'},
        {value: 'shutdown', label: '关闭计算机', icon: 'fas fa-power-off'},
        {value: 'restart', label: '重新启动', icon: 'fas fa-redo'}
    ];
    
    let html = `
        <div class="config-group">
            <h3>全局默认操作 <span class="field-tip">当时间段未匹配时执行的操作</span></h3>
            <div class="field-row">
    `;
    
    actions.forEach(actionItem => {
        html += `
            <div class="field-group">
                <label style="flex-direction: row; align-items: center;">
                    <input type="radio" 
                           name="task_completion_action" 
                           value="${actionItem.value}"
                           ${globalAction === actionItem.value ? 'checked' : ''}
                           style="margin-right: 10px;">
                    <i class="${actionItem.icon}" style="margin-right: 8px;"></i>
                    ${actionItem.label}
                </label>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
        
        <div class="config-group">
            <h3>时间段操作配置 <span class="field-tip">根据时间段执行不同的操作（支持跨午夜）</span></h3>
            <div id="scheduledActionsContainer">
    `;
    
    // 渲染时间段配置
    if (scheduledActions.length === 0) {
        html += `
            <div class="no-schedule" style="text-align: center; padding: 20px; color: #666;">
                <i class="fas fa-clock fa-2x" style="margin-bottom: 10px;"></i>
                <p>未配置时间段，将使用全局默认操作</p>
                <button type="button" onclick="addNewSchedule()" class="action-btn save" style="margin-top: 10px;">
                    <i class="fas fa-plus"></i> 添加时间段
                </button>
            </div>
        `;
    } else {
        html += `
            <div style="margin-bottom: 15px;">
                <button type="button" onclick="addNewSchedule()" class="action-btn save" style="padding: 10px 15px;">
                    <i class="fas fa-plus"></i> 添加新时间段
                </button>
            </div>
        `;
        
        scheduledActions.forEach((schedule, index) => {
            const name = schedule.name || `时间段${index + 1}`;
            const startTime = schedule.start_time || '00:00';
            const endTime = schedule.end_time || '23:59';
            const action = schedule.action || 'none';
            const enabled = schedule.enabled !== false;
            
            html += `
                <div class="schedule-item" data-index="${index}" style="
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background: ${enabled ? '#f8f9fa' : '#f0f0f0'};
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #333;">
                            ${enabled ? '✓' : '✗'} ${name}
                        </h4>
                        <div>
                            <button type="button" onclick="toggleSchedule(${index})" style="
                                background: ${enabled ? '#4CAF50' : '#f44336'};
                                color: white;
                                border: none;
                                padding: 5px 10px;
                                border-radius: 4px;
                                margin-right: 5px;
                                cursor: pointer;
                            ">
                                ${enabled ? '禁用' : '启用'}
                            </button>
                            <button type="button" onclick="removeSchedule(${index})" style="
                                background: #ff9800;
                                color: white;
                                border: none;
                                padding: 5px 10px;
                                border-radius: 4px;
                                cursor: pointer;
                            ">
                                删除
                            </button>
                        </div>
                    </div>
                    
                    <div class="field-row" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                        <div class="field-group">
                            <label>名称</label>
                            <input type="text" 
                                   class="schedule-name" 
                                   value="${escapeHtml(name)}"
                                   placeholder="例如：工作时间">
                        </div>
                        
                        <div class="field-group">
                            <label>开始时间</label>
                            <input type="time" 
                                   class="schedule-start" 
                                   value="${startTime}"
                                   step="60">
                        </div>
                        
                        <div class="field-group">
                            <label>结束时间</label>
                            <input type="time" 
                                   class="schedule-end" 
                                   value="${endTime}"
                                   step="60">
                        </div>
                        
                        <div class="field-group">
                            <label>执行操作</label>
                            <select class="schedule-action">
                `;
                
                actions.forEach(actionItem => {
                    html += `
                        <option value="${actionItem.value}" ${action === actionItem.value ? 'selected' : ''}>
                            ${actionItem.label}
                        </option>
                    `;
                });
                
                html += `
                            </select>
                        </div>
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                        提示：如果要配置跨午夜的时间段（如 22:00 到 06:00），结束时间应小于开始时间
                    </div>
                </div>
            `;
        });
    }
    
    html += `
            </div>
        </div>
    `;
    
    tabContent.innerHTML = html;
}

// 转义HTML特殊字符
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>'"]/g, function(m) { return map[m]; });
}

// 显示状态消息
function showStatus(message, isSuccess) {
    const statusDiv = document.getElementById('status');
    const icon = isSuccess ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
    const type = isSuccess ? 'success' : 'error';
    
    statusDiv.innerHTML = `${icon} ${message}`;
    statusDiv.className = `status ${type}`;
    statusDiv.style.display = 'flex';
    
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

// 运行命令
function runCommand(command, params = {}) {
    const button = document.querySelector(`.command-btn.${command}`);
    const originalText = button ? button.innerHTML : '';
    
    if (button) {
        // 显示加载状态
        button.classList.add('loading');
        button.disabled = true;
    }
    
    fetch('/command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({command: command, ...params})
    })
    .then(response => response.json())
    .then(data => {
        if (button) {
            // 恢复按钮状态
            button.classList.remove('loading');
            button.innerHTML = originalText;
            button.disabled = false;
        }
        
        if (data.success) {
            showStatus(`命令执行成功: ${command}`, true);
        } else {
            showStatus(`命令执行失败: ${data.message}`, false);
        }
    })
    .catch(error => {
        if (button) {
            // 恢复按钮状态
            button.classList.remove('loading');
            button.innerHTML = originalText;
            button.disabled = false;
        }
        
        showStatus('请求失败: ' + error, false);
    });
}

// 运行高级命令
function runAdvancedCommand() {
    const command = document.getElementById('commandSelect').value;
    const date = document.getElementById('dateInput').value;
    const only = document.getElementById('onlyFlag').checked;
    
    const params = {};
    if (only) {
        params.only = true;
    }
    if (date) {
        params.date = date;
    }
    
    // 显示执行状态
    showStatus(`正在执行命令: ${command}`, true);
    
    // 执行命令
    runCommand(command, params);
}

// 添加新时间段
function addNewSchedule() {
    const container = document.getElementById('scheduledActionsContainer');
    const index = document.querySelectorAll('.schedule-item').length;
    
    const newSchedule = `
        <div class="schedule-item" data-index="${index}" style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #333;">
                    ✓ 新时间段
                </h4>
                <div>
                    <button type="button" onclick="toggleSchedule(${index})" style="
                        background: #4CAF50;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 4px;
                        margin-right: 5px;
                        cursor: pointer;
                    ">
                        禁用
                    </button>
                    <button type="button" onclick="removeSchedule(${index})" style="
                        background: #ff9800;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">
                        删除
                    </button>
                </div>
            </div>
            
            <div class="field-row" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                <div class="field-group">
                    <label>名称</label>
                    <input type="text" 
                           class="schedule-name" 
                           value="新时间段"
                           placeholder="例如：工作时间">
                </div>
                
                <div class="field-group">
                    <label>开始时间</label>
                    <input type="time" 
                           class="schedule-start" 
                           value="09:00"
                           step="300">
                </div>
                
                <div class="field-group">
                    <label>结束时间</label>
                    <input type="time" 
                           class="schedule-end" 
                           value="17:00"
                           step="300">
                </div>
                
                <div class="field-group">
                    <label>执行操作</label>
                    <select class="schedule-action">
                        <option value="none">不执行任何操作</option>
                        <option value="logout">注销系统</option>
                        <option value="shutdown" selected>关闭计算机</option>
                        <option value="restart">重新启动</option>
                    </select>
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #666;">
                提示：如果要配置跨午夜的时间段（如 22:00 到 06:00），结束时间应小于开始时间
            </div>
        </div>
    `;
    
    if (container.querySelector('.no-schedule')) {
        container.innerHTML = `
            <div style="margin-bottom: 15px;">
                <button type="button" onclick="addNewSchedule()" class="action-btn save" style="padding: 10px 15px;">
                    <i class="fas fa-plus"></i> 添加新时间段
                </button>
            </div>
            ${newSchedule}
        `;
    } else {
        container.insertAdjacentHTML('beforeend', newSchedule);
    }
}

// 切换时间段启用/禁用状态
function toggleSchedule(index) {
    const scheduleItem = document.querySelector(`.schedule-item[data-index="${index}"]`);
    if (!scheduleItem) return;
    
    const title = scheduleItem.querySelector('h4');
    const toggleBtn = scheduleItem.querySelector('button[onclick^="toggleSchedule"]');
    const isEnabled = !title.textContent.includes('✗');
    
    if (isEnabled) {
        title.innerHTML = title.innerHTML.replace('✓', '✗');
        scheduleItem.style.background = '#f0f0f0';
        toggleBtn.textContent = '启用';
        toggleBtn.style.background = '#f44336';
    } else {
        title.innerHTML = title.innerHTML.replace('✗', '✓');
        scheduleItem.style.background = '#f8f9fa';
        toggleBtn.textContent = '禁用';
        toggleBtn.style.background = '#4CAF50';
    }
}

// 删除时间段
function removeSchedule(index) {
    const scheduleItem = document.querySelector(`.schedule-item[data-index="${index}"]`);
    if (!scheduleItem) return;
    
    if (confirm('确定要删除这个时间段配置吗？')) {
        scheduleItem.remove();
        
        // 重新索引
        const items = document.querySelectorAll('.schedule-item');
        items.forEach((item, newIndex) => {
            item.setAttribute('data-index', newIndex);
            
            const toggleBtn = item.querySelector('button[onclick^="toggleSchedule"]');
            const removeBtn = item.querySelector('button[onclick^="removeSchedule"]');
            
            toggleBtn.setAttribute('onclick', `toggleSchedule(${newIndex})`);
            removeBtn.setAttribute('onclick', `removeSchedule(${newIndex})`);
        });
        
        // 如果没有时间段了，显示空状态
        if (items.length === 0) {
            const container = document.getElementById('scheduledActionsContainer');
            container.innerHTML = `
                <div class="no-schedule" style="text-align: center; padding: 20px; color: #666;">
                    <i class="fas fa-clock fa-2x" style="margin-bottom: 10px;"></i>
                    <p>未配置时间段，将使用全局默认操作</p>
                    <button type="button" onclick="addNewSchedule()" class="action-btn save" style="margin-top: 10px;">
                        <i class="fas fa-plus"></i> 添加时间段
                    </button>
                </div>
            `;
        }
    }
}

// 表单提交
document.getElementById('configForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {};
    
    // 收集所有表单数据
    for (let [key, value] of formData.entries()) {
        // 处理嵌套对象
        const keys = key.split('.');
        let current = data;
        
        for (let i = 0; i < keys.length - 1; i++) {
            if (!current[keys[i]]) {
                current[keys[i]] = {};
            }
            current = current[keys[i]];
        }
        
        current[keys[keys.length - 1]] = value;
    }
    
    // 添加全局默认操作
    const globalAction = document.querySelector('input[name="task_completion_action"]:checked');
    if (globalAction) {
        data.task_completion_action = globalAction.value;
    }
    
    // 收集时间段配置
    const scheduledActions = [];
    const scheduleItems = document.querySelectorAll('.schedule-item');
    
    scheduleItems.forEach((item, index) => {
        const nameInput = item.querySelector('.schedule-name');
        const startInput = item.querySelector('.schedule-start');
        const endInput = item.querySelector('.schedule-end');
        const actionSelect = item.querySelector('.schedule-action');
        const title = item.querySelector('h4');
        
        const isEnabled = !title.textContent.includes('✗');
        
        scheduledActions.push({
            name: nameInput.value || `时间段${index + 1}`,
            start_time: startInput.value || '00:00',
            end_time: endInput.value || '23:59',
            action: actionSelect.value || 'none',
            enabled: isEnabled
        });
    });
    
    data.scheduled_completion_actions = scheduledActions;
    
    // 显示保存状态
    const saveBtn = document.querySelector('.action-btn.save');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
    saveBtn.disabled = true;
    
    fetch('/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        // 恢复按钮状态
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
        
        if (data.success) {
            showStatus('配置保存成功！', true);
            // 重新加载配置
            fetch('/config')
                .then(response => response.json())
                .then(newConfig => {
                    configData = newConfig;
                    // 重新渲染表单以反映保存的数据
                    renderConfigForm();
                });
        } else {
            showStatus('保存失败: ' + data.message, false);
        }
    })
    .catch(error => {
        // 恢复按钮状态
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
        
        showStatus('请求失败: ' + error, false);
    });
});

// 重置表单
function resetForm() {
    if (confirm('确定要重置表单吗？所有更改将丢失。')) {
        fetch('/config')
            .then(response => response.json())
            .then(data => {
                configData = data;
                renderConfigForm();
                showStatus('表单已重置为当前配置', true);
            })
            .catch(error => {
                showStatus('重置失败: ' + error, false);
            });
    }
}