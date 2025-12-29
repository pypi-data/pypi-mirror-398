# Uno 配置检查清单

## 连接真实服务器环境的配置要点

### ✅ 必需配置

#### 1. **MCPMarket 配置**（第 10-12 行）
```env
MCPMARKET_URL=https://mcpmarket.cn
MCPMARKET_API_URL=https://mcpmarket.cn/api
```

**重要说明：**
- ✅ `MCPMARKET_URL`：用于 OAuth 授权、token 交换、MCP server 直连 URL 构建
- ✅ `MCPMARKET_API_URL`：用于所有 HTTP API 调用（**必需**）
  - `/api/uno/verify-token` - 验证 token
  - `/api/uno/servers` - 获取 server 列表
  - `/api/uno/check-connection` - 检查连接状态
  - `/api/uno/create-instance` - 创建实例
  - `/api/uno/user-info` - 获取用户信息

**检查项：**
- [ ] 确认 `MCPMARKET_API_URL` 可以正常访问（`https://mcpmarket.cn/api/uno/verify-token`）
- [ ] 确认 `MCPMARKET_URL` 用于 OAuth 回调（`https://mcpmarket.cn/oauth/authorize`）

#### 2. **服务器 URL 配置**（第 8 行）
```env
SERVER_URL=http://localhost:8089
```

**重要说明：**
- ⚠️ **生产环境必须修改**为实际的外部访问地址
- 用于 OAuth 回调和 well-known 端点
- 如果部署在服务器上，应该使用：
  ```env
  SERVER_URL=https://your-domain.com
  # 或
  SERVER_URL=http://your-server-ip:8089
  ```

**检查项：**
- [ ] 确认 `SERVER_URL` 可以从外部访问（用于 OAuth 回调）
- [ ] 确认 `SERVER_URL` 与 `HOST` 和 `PORT` 配置一致

### ❌ 已废弃配置（可以删除）

#### MongoDB 配置（第 14-16 行）
```env
# 以下配置已不再需要，可以删除
# MONGODB_URI=mongodb://localhost:27017
# MONGODB_DB=mcpmarket
```

**原因：**
- uno 已改为全部通过 HTTP API 访问 mcpmarket
- 不再直接连接 MongoDB 数据库
- 保留仅为兼容性，实际不再使用

### ⚠️ 其他重要配置

#### 1. **安全配置**（第 27 行）
```env
SECRET_KEY=your-secret-key-change-in-production
```

**检查项：**
- [ ] 生产环境必须修改为强随机密钥
- [ ] 不要使用默认值

#### 2. **CORS 配置**（第 30 行）
```env
CORS_ORIGINS=*
```

**检查项：**
- [ ] 生产环境建议限制为具体域名：
  ```env
  CORS_ORIGINS=https://your-frontend-domain.com,https://mcpmarket.cn
  ```

#### 3. **OpenAI 配置**（第 22-24 行）
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
SKILL_MATCHER_MODEL=gpt-4o-mini
```

**检查项：**
- [ ] 如果使用 skill 匹配功能，需要配置 OpenAI API Key
- [ ] 如果使用其他兼容 OpenAI API 的服务，修改 `OPENAI_BASE_URL`

#### 4. **Redis 配置**（第 19 行）
```env
REDIS_URL=redis://localhost:6379/1
```

**检查项：**
- [ ] 如果使用 Redis 缓存，确认 Redis 服务可访问
- [ ] 生产环境建议使用密码保护：
  ```env
  REDIS_URL=redis://:password@redis-server:6379/1
  ```

## 配置验证步骤

### 1. 测试 MCPMarket API 连接
```bash
# 测试 API 是否可访问
curl https://mcpmarket.cn/api/uno/verify-token \
  -H "Authorization: Bearer test-token"
```

### 2. 测试服务器启动
```bash
# 启动 uno
uv run uno

# 检查日志，确认：
# - "ServerRegistry 已初始化（使用 HTTP API）"
# - "AuthClient 已初始化（使用 HTTP API）"
# - 没有 MongoDB 连接错误
```

### 3. 测试 OAuth 流程
- 访问 `http://your-server:8089/gui`
- 尝试登录，确认 OAuth 回调正常

## 常见问题

### Q: MongoDB 配置还需要吗？
**A:** 不需要。uno 已改为全部通过 HTTP API 访问，不再直接连接数据库。

### Q: `MCPMARKET_URL` 和 `MCPMARKET_API_URL` 有什么区别？
**A:**
- `MCPMARKET_URL`: 用于 OAuth 授权、token 交换、MCP server 直连 URL
- `MCPMARKET_API_URL`: 用于所有 uno API 调用（必须以 `/api` 结尾）

### Q: 生产环境 `SERVER_URL` 应该怎么配置？
**A:** 必须配置为外部可访问的地址：
- 如果有域名：`https://your-domain.com`
- 如果只有 IP：`http://your-ip:8089`
- 必须确保可以从 mcpmarket 服务器访问（用于 OAuth 回调）

### Q: 如何确认配置正确？
**A:** 检查启动日志：
- ✅ 看到 "使用 HTTP API" 相关日志
- ❌ 没有 MongoDB 连接错误
- ✅ 可以成功调用 `/api/uno/servers` API




