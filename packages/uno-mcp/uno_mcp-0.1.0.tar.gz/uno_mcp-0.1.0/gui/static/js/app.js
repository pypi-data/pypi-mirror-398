/**
 * Uno Tools Inspector - 前端交互逻辑
 * 
 * 使用 OAuth 2.0 Authorization Code Flow with PKCE
 * mcpmarket 作为认证服务器（类似 Gmail 登录）
 */

// 全局状态
let toolsData = [];
let selectedTool = null;
let accessToken = null;
let currentUser = null;

// mcpmarket OAuth 配置（从后端动态获取）
let MCPMARKET_URL = 'http://localhost:8090';  // 默认值，将从服务器获取
let OAUTH_CONFIG = {
    authorizationEndpoint: `${MCPMARKET_URL}/oauth/authorize`,
    tokenEndpoint: `${MCPMARKET_URL}/oauth/token`,
    clientId: 'uno-gui',  // GUI 客户端 ID
    redirectUri: `${window.location.origin}/gui/callback`,
    scope: 'read write'
};

// Token 存储 key
const TOKEN_STORAGE_KEY = 'uno_access_token';
const USER_STORAGE_KEY = 'uno_user';
const PKCE_VERIFIER_KEY = 'uno_pkce_verifier';
const OAUTH_STATE_KEY = 'uno_oauth_state';

/**
 * 从后端加载配置
 */
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            MCPMARKET_URL = config.mcpmarket_url;
            // 更新 OAuth 配置
            OAUTH_CONFIG = {
                authorizationEndpoint: `${MCPMARKET_URL}/oauth/authorize`,
                tokenEndpoint: `${MCPMARKET_URL}/oauth/token`,
                clientId: 'uno-gui',
                redirectUri: `${window.location.origin}/gui/callback`,
                scope: 'read write'
            };
            console.log('配置已加载:', { MCPMARKET_URL });
        }
    } catch (error) {
        console.error('加载配置失败，使用默认配置:', error);
    }
}

/**
 * 初始化
 */
document.addEventListener('DOMContentLoaded', async () => {
    // 1. 先加载配置
    await loadConfig();
    
    // 2. 搜索切换
    document.getElementById('search-toggle').addEventListener('click', toggleSearch);
    
    // 3. 检查是否是 OAuth 回调
    if (await handleOAuthCallback()) {
        return;  // 回调处理中，等待完成
    }
    
    // 4. 检查登录状态
    checkLoginStatus();
});

// ============= OAuth 2.0 认证流程 =============

/**
 * 生成随机字符串（用于 state 和 code_verifier）
 */
function generateRandomString(length = 64) {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('').slice(0, length);
}

/**
 * 生成 PKCE code_challenge（SHA-256）
 */
async function generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    
    // Base64 URL encode
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

/**
 * 开始 OAuth 登录流程
 */
async function login() {
    try {
        // 1. 生成 state（防 CSRF）
        const state = generateRandomString(32);
        sessionStorage.setItem(OAUTH_STATE_KEY, state);
        
        // 2. 生成 PKCE code_verifier 和 code_challenge
        const codeVerifier = generateRandomString(64);
        sessionStorage.setItem(PKCE_VERIFIER_KEY, codeVerifier);
        const codeChallenge = await generateCodeChallenge(codeVerifier);
        
        // 3. 构建授权 URL
        const params = new URLSearchParams({
            response_type: 'code',
            client_id: OAUTH_CONFIG.clientId,
            redirect_uri: OAUTH_CONFIG.redirectUri,
            scope: OAUTH_CONFIG.scope,
            state: state,
            code_challenge: codeChallenge,
            code_challenge_method: 'S256'
        });
        
        const authUrl = `${OAUTH_CONFIG.authorizationEndpoint}?${params.toString()}`;
        
        console.log('开始 OAuth 登录, 跳转到:', authUrl);
        
        // 4. 跳转到授权页面
        window.location.href = authUrl;
        
    } catch (error) {
        console.error('OAuth 登录失败:', error);
        showError('登录失败: ' + error.message);
    }
}

/**
 * 处理 OAuth 回调
 * 
 * 当用户从 mcpmarket 授权后返回时调用
 */
async function handleOAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');
    
    // 检查是否是回调
    if (!code && !error) {
        return false;
    }
    
    console.log('处理 OAuth 回调...');
    
    // 处理错误
    if (error) {
        console.error('OAuth 错误:', error, urlParams.get('error_description'));
        showError('授权失败: ' + (urlParams.get('error_description') || error));
        // 清理 URL 参数
        window.history.replaceState({}, document.title, window.location.pathname);
        disableUI();
        return true;
    }
    
    // 验证 state
    const savedState = sessionStorage.getItem(OAUTH_STATE_KEY);
    if (state !== savedState) {
        console.error('State 不匹配');
        showError('安全验证失败，请重新登录');
        window.history.replaceState({}, document.title, window.location.pathname);
        disableUI();
        return true;
    }
    
    // 获取 code_verifier
    const codeVerifier = sessionStorage.getItem(PKCE_VERIFIER_KEY);
    if (!codeVerifier) {
        console.error('未找到 code_verifier');
        showError('登录状态丢失，请重新登录');
        window.history.replaceState({}, document.title, window.location.pathname);
        disableUI();
        return true;
    }
    
    try {
        // 用 code 换取 access_token（通过后端代理）
        const tokenResponse = await fetch('/api/oauth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                code_verifier: codeVerifier,
                redirect_uri: OAUTH_CONFIG.redirectUri
            })
        });
        
        if (!tokenResponse.ok) {
            const errorData = await tokenResponse.json();
            throw new Error(errorData.error || '获取 token 失败');
        }
        
        const tokenData = await tokenResponse.json();
        
        // 保存 token
        accessToken = tokenData.access_token;
        localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
        
        // 获取用户信息
        await fetchUserInfo();
        
        // 清理 session storage
        sessionStorage.removeItem(OAUTH_STATE_KEY);
        sessionStorage.removeItem(PKCE_VERIFIER_KEY);
        
        // 清理 URL 参数
        window.history.replaceState({}, document.title, window.location.pathname);
        
        console.log('OAuth 登录成功!');
        
        // 更新 UI
        updateUserUI();
        enableUI();
        listTools();
        
    } catch (error) {
        console.error('Token 交换失败:', error);
        showError('登录失败: ' + error.message);
        window.history.replaceState({}, document.title, window.location.pathname);
        disableUI();
    }
    
    return true;
}

/**
 * 获取用户信息
 */
async function fetchUserInfo() {
    try {
        const response = await fetch('/api/oauth/userinfo', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(currentUser));
        }
    } catch (e) {
        console.error('获取用户信息失败:', e);
    }
}

/**
 * 检查登录状态（从 localStorage 恢复）
 */
async function checkLoginStatus() {
    // 尝试从 localStorage 恢复 token
    const savedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
    const savedUser = localStorage.getItem(USER_STORAGE_KEY);
    
    if (savedToken) {
        accessToken = savedToken;
        
        // 验证 token 是否仍然有效
        try {
            const response = await fetch('/api/oauth/verify', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.valid) {
                    // Token 有效
                    if (savedUser) {
                        currentUser = JSON.parse(savedUser);
                    } else {
                        await fetchUserInfo();
                    }
                    updateUserUI();
                    enableUI();
                    listTools();
                    return;
                }
            }
        } catch (e) {
            console.error('验证 token 失败:', e);
        }
        
        // Token 无效，清除
        clearAuth();
    }
    
    // 未登录
    currentUser = null;
    updateUserUI();
    disableUI();
}

/**
 * 清除认证信息
 */
function clearAuth() {
    accessToken = null;
    currentUser = null;
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
}

/**
 * 退出登录
 */
async function logout() {
    // 清除本地认证信息
    clearAuth();
    
    // 更新 UI
    updateUserUI();
    disableUI();
    
    // 清空工具列表
    document.getElementById('tools-list').innerHTML = '';
    
    console.log('已退出登录');
}

/**
 * 更新用户界面
 */
function updateUserUI() {
    const userNameEl = document.getElementById('user-name');
    const loginBtn = document.getElementById('login-btn');
    
    if (currentUser && currentUser.username) {
        userNameEl.textContent = currentUser.username;
        loginBtn.textContent = '退出';
        loginBtn.onclick = logout;
    } else {
        userNameEl.textContent = '未登录';
        loginBtn.textContent = '登录';
        loginBtn.onclick = login;
    }
}

// ============= UI 控制 =============

/**
 * 启用 UI
 */
function enableUI() {
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
    });
    
    // 移除遮罩
    const mask = document.getElementById('login-mask');
    if (mask) mask.remove();
}

/**
 * 禁用 UI（未登录时）
 */
function disableUI() {
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
    });
    
    // 添加登录提示遮罩
    const detailPanel = document.querySelector('.detail-panel .panel-body');
    if (detailPanel && !document.getElementById('login-mask')) {
        const mask = document.createElement('div');
        mask.id = 'login-mask';
        mask.style.cssText = `
            position: absolute;
            top: 80px;
            left: 50%;
            right: 24px;
            bottom: 24px;
            background: rgba(255,255,255,0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            z-index: 10;
        `;
        mask.innerHTML = `
            <div style="text-align: center;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#228be6" stroke-width="2" style="margin-bottom: 16px;">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
                <h3 style="margin: 0 0 8px 0; color: #212529;">需要登录</h3>
                <p style="color: #868e96; margin: 0 0 20px 0;">请先登录以使用 Uno 工具</p>
                <button onclick="login()" style="
                    padding: 10px 24px;
                    background: #228be6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    cursor: pointer;
                ">立即登录</button>
            </div>
        `;
        document.querySelector('.main').appendChild(mask);
    }
}

// ============= 工具操作 =============

/**
 * 切换搜索框显示
 */
function toggleSearch() {
    const searchBox = document.getElementById('search-box');
    const isVisible = searchBox.style.display !== 'none';
    searchBox.style.display = isVisible ? 'none' : 'block';
    if (!isVisible) {
        document.getElementById('tool-search').focus();
    }
}

/**
 * 获取工具列表
 */
async function listTools() {
    try {
        const headers = {};
        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }
        
        const response = await fetch('/api/tools', { headers });
        const data = await response.json();
        toolsData = data.tools || [];
        
        renderToolsList();
        
    } catch (error) {
        console.error('获取工具列表失败:', error);
        showError('获取工具列表失败');
    }
}

/**
 * 清空工具列表
 */
function clearTools() {
    toolsData = [];
    selectedTool = null;
    renderToolsList();
    document.getElementById('detail-title').textContent = '选择工具';
    document.getElementById('detail-content').innerHTML = 
        '<p class="placeholder">从左侧列表选择一个工具查看详情并运行</p>';
}

/**
 * 过滤工具
 */
function filterTools() {
    const search = document.getElementById('tool-search').value.toLowerCase();
    renderToolsList(search);
}

/**
 * 渲染工具列表
 */
function renderToolsList(filter = '') {
    const list = document.getElementById('tools-list');
    
    const filtered = filter 
        ? toolsData.filter(t => 
            t.name.toLowerCase().includes(filter) ||
            t.description.toLowerCase().includes(filter)
          )
        : toolsData;
    
    if (filtered.length === 0) {
        list.innerHTML = toolsData.length === 0 
            ? '' 
            : '<li class="placeholder" style="cursor: default;">没有匹配的工具</li>';
        return;
    }
    
    list.innerHTML = filtered.map(tool => `
        <li onclick="selectTool('${tool.name}')" 
            class="${selectedTool === tool.name ? 'active' : ''}">
            <div class="tool-name">${tool.name}</div>
            <div class="tool-desc">${getShortDesc(tool.description)}</div>
        </li>
    `).join('');
}

/**
 * 获取简短描述
 */
function getShortDesc(desc) {
    if (!desc) return '无描述';
    // 取第一行或前100字符
    const firstLine = desc.split('\n')[0];
    return firstLine.length > 80 ? firstLine.substring(0, 80) + '...' : firstLine;
}

/**
 * 选择工具
 */
function selectTool(name) {
    selectedTool = name;
    renderToolsList(document.getElementById('tool-search').value);
    
    const tool = toolsData.find(t => t.name === name);
    if (tool) {
        showToolDetail(tool);
    }
}

/**
 * 显示工具详情
 */
function showToolDetail(tool) {
    document.getElementById('detail-title').textContent = tool.name;
    
    const content = document.getElementById('detail-content');
    const schema = tool.inputSchema || {};
    const properties = schema.properties || {};
    const required = schema.required || [];
    
    // 构建参数输入表单
    let paramsHtml = '';
    for (const [paramName, paramDef] of Object.entries(properties)) {
        const isRequired = required.includes(paramName);
        const paramType = getParamType(paramDef);
        
        paramsHtml += `
            <div class="param-item">
                <div class="param-header">
                    <span class="param-name">${paramName}${isRequired ? ' *' : ''}</span>
                    <span class="param-type">${paramType}</span>
                </div>
                <div class="param-desc">${paramDef.description || '无描述'}</div>
                ${getParamInput(paramName, paramDef, paramType)}
            </div>
        `;
    }
    
    content.innerHTML = `
        <div class="tool-detail">
            <div class="tool-detail-name">${tool.name}</div>
            <div class="tool-detail-desc">${tool.description || '无描述'}</div>
        </div>
        
        ${Object.keys(properties).length > 0 ? `
            <div class="params-section">
                <div class="section-title">
                    参数
                    ${required.length > 0 ? '<span class="required-badge">* 必填</span>' : ''}
                </div>
                ${paramsHtml}
            </div>
        ` : ''}
        
        <button class="run-btn" onclick="runTool('${tool.name}')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
            </svg>
            运行
        </button>
        
        <div class="result-section" id="result-section" style="display: none;">
            <div class="result-header">
                <span class="result-title">执行结果</span>
                <span class="result-status" id="result-status"></span>
            </div>
            <div class="result-content" id="result-content"></div>
        </div>
    `;
}

/**
 * 获取参数类型显示文本
 */
function getParamType(paramDef) {
    if (paramDef.type === 'array') {
        const itemType = paramDef.items?.type || 'any';
        return `array<${itemType}>`;
    }
    return paramDef.type || 'any';
}

/**
 * 生成参数输入控件
 */
function getParamInput(name, def, type) {
    const placeholder = getPlaceholder(def, type);
    
    if (type === 'object' || type.startsWith('array')) {
        return `<textarea class="param-input" id="param-${name}" 
                    placeholder='${placeholder}'></textarea>`;
    }
    
    return `<input class="param-input" id="param-${name}" 
                type="text" placeholder="${placeholder}">`;
}

/**
 * 获取占位提示
 */
function getPlaceholder(def, type) {
    if (type === 'object') {
        return '输入 JSON 对象，如: {"key": "value"}';
    }
    if (type.startsWith('array')) {
        return '输入 JSON 数组，如: ["item1", "item2"]';
    }
    if (type === 'string') {
        return '输入文本';
    }
    if (type === 'number' || type === 'integer') {
        return '输入数字';
    }
    if (type === 'boolean') {
        return 'true 或 false';
    }
    return '输入值';
}

/**
 * 运行工具
 */
async function runTool(toolName) {
    const tool = toolsData.find(t => t.name === toolName);
    if (!tool) return;
    
    // 收集参数
    const schema = tool.inputSchema || {};
    const properties = schema.properties || {};
    const arguments_ = {};
    
    for (const [paramName, paramDef] of Object.entries(properties)) {
        const input = document.getElementById(`param-${paramName}`);
        if (!input) continue;
        
        const value = input.value.trim();
        if (!value) continue;
        
        // 解析值
        try {
            const paramType = getParamType(paramDef);
            if (paramType === 'object' || paramType.startsWith('array')) {
                arguments_[paramName] = JSON.parse(value);
            } else if (paramType === 'number' || paramType === 'integer') {
                arguments_[paramName] = Number(value);
            } else if (paramType === 'boolean') {
                arguments_[paramName] = value.toLowerCase() === 'true';
            } else {
                arguments_[paramName] = value;
            }
        } catch (e) {
            showResult(true, `参数 ${paramName} 格式错误: ${e.message}`);
            return;
        }
    }
    
    // 显示 loading
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';
    document.getElementById('result-status').className = 'result-status';
    document.getElementById('result-status').textContent = '';
    document.getElementById('result-content').innerHTML = 
        '<div class="loading"><div class="spinner"></div>执行中...</div>';
    
    try {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }
        
        const response = await fetch('/api/tools/call', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                name: toolName,
                arguments: arguments_
            })
        });
        
        const data = await response.json();
        
        // 提取结果文本
        let resultText = '';
        if (data.content && data.content.length > 0) {
            resultText = data.content.map(c => c.text || JSON.stringify(c)).join('\n');
        } else {
            resultText = JSON.stringify(data, null, 2);
        }
        
        showResult(data.isError, resultText);
        
    } catch (error) {
        console.error('执行失败:', error);
        showResult(true, `请求失败: ${error.message}`);
    }
}

/**
 * 显示执行结果
 */
function showResult(isError, content) {
    const resultSection = document.getElementById('result-section');
    const statusEl = document.getElementById('result-status');
    const contentEl = document.getElementById('result-content');
    
    resultSection.style.display = 'block';
    statusEl.className = `result-status ${isError ? 'error' : 'success'}`;
    statusEl.textContent = isError ? '失败' : '成功';
    contentEl.textContent = content;
}

/**
 * 显示错误提示
 */
function showError(message) {
    const content = document.getElementById('detail-content');
    content.innerHTML = `<p class="placeholder" style="color: var(--accent-red);">${message}</p>`;
}
