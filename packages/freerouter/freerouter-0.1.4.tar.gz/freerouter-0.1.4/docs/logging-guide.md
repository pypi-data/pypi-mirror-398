# FreeRouter 日志配置指南

## 查看 API 请求日志

FreeRouter 使用 LiteLLM 作为底层路由引擎，支持多种日志级别来查看详细的 API 请求/响应信息。

## 方法 1：使用环境变量（推荐）

### 方式 A：使用 LITELLM_LOG（LiteLLM 原生方式）

```bash
# 设置日志级别为 DEBUG
export LITELLM_LOG=DEBUG

# 重启服务（会自动应用新的环境变量）
freerouter reload

# 查看实时日志
freerouter logs
```

### 方式 B：使用 FREEROUTER_LOG_LEVEL（FreeRouter 专用）

```bash
# FreeRouter 会自动将此变量传递给 LiteLLM
export FREEROUTER_LOG_LEVEL=DEBUG

# 重启服务
freerouter reload

# 查看实时日志
freerouter logs
```

### 临时启动（不修改全局环境）

```bash
# 方法 1
LITELLM_LOG=DEBUG freerouter start

# 方法 2
FREEROUTER_LOG_LEVEL=DEBUG freerouter start
```

### 永久配置（添加到 ~/.bashrc 或 ~/.zshrc）

```bash
# 在 shell 配置文件中添加
echo 'export LITELLM_LOG=DEBUG' >> ~/.bashrc
source ~/.bashrc
```

## 方法 2：使用 Python logging 配置

在启动服务前，创建配置文件：

```bash
# 临时设置 Python logging 级别
export PYTHONUNBUFFERED=1
export LITELLM_LOG=DEBUG

freerouter start
```

## 日志级别说明

| 级别 | 说明 | 适用场景 |
|------|------|----------|
| `DEBUG` | 显示所有详细信息，包括完整的请求/响应 | 开发调试、查看 API 请求详情 |
| `INFO` | 显示常规操作信息（默认） | 日常使用 |
| `WARNING` | 仅显示警告和错误 | 生产环境 |
| `ERROR` | 仅显示错误信息 | 生产环境（静默模式） |

## DEBUG 模式下的日志内容

启用 `DEBUG` 级别后，你会看到：

1. **完整的 HTTP 请求**：
   - 请求 URL
   - 请求头（Headers）
   - 请求体（Body/Payload）

2. **完整的 HTTP 响应**：
   - 响应状态码
   - 响应头
   - 响应体（包括模型返回的内容）

3. **性能指标**：
   - 请求耗时
   - Token 使用量
   - 重试次数

## 示例输出

```
2025-12-28 10:30:15 - DEBUG - POST Request Sent from LiteLLM:
POST Request Sent from LiteLLM:
https://openrouter.ai/api/v1/chat/completions
{
  "model": "anthropic/claude-3.5-sonnet",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.7
}

2025-12-28 10:30:16 - DEBUG - POST Response from API:
Status: 200
Response Time: 1.23s
{
  "id": "chatcmpl-...",
  "choices": [{"message": {"content": "Hello! ..."}}],
  "usage": {"prompt_tokens": 10, "completion_tokens": 20}
}
```

## 实时查看日志

```bash
# 使用 freerouter 自带命令
freerouter logs

# 或使用 tail 命令
tail -f ~/.config/freerouter/freerouter.log

# 或使用 grep 过滤特定内容
freerouter logs | grep -i "POST Request"
```

## 高级配置：自定义日志文件

如果需要将请求日志单独保存到文件：

```bash
# 启动服务时重定向输出
export LITELLM_LOG=DEBUG
freerouter start

# 日志会自动保存到：
# ~/.config/freerouter/freerouter.log
```

## 过滤特定供应商的日志

```bash
# 查看所有 OpenRouter 请求
freerouter logs | grep -i "openrouter"

# 查看特定模型的请求
freerouter logs | grep -i "claude-3.5-sonnet"

# 查看错误日志
freerouter logs | grep -i "error"
```

## 性能影响

**注意**：`DEBUG` 级别会：
- 增加日志文件大小（建议定期清理）
- 略微降低性能（约 5-10%）
- 可能包含敏感信息（如 API keys）

**生产环境建议使用 `INFO` 或 `WARNING` 级别。**

## 清理日志文件

```bash
# 清空日志文件
echo "" > ~/.config/freerouter/freerouter.log

# 或删除后重新启动
rm ~/.config/freerouter/freerouter.log
freerouter reload
```

## 使用外部日志工具

### 使用 LiteLLM Proxy UI（可选）

LiteLLM 提供 Web UI 查看请求日志：

```bash
# 安装 UI 组件
pip install 'litellm[proxy]'

# 带 UI 启动（FreeRouter 暂不支持，需直接使用 litellm）
litellm --config ~/.config/freerouter/config.yaml --port 4000 --ui
```

访问 `http://localhost:4000/ui` 查看可视化日志。

## 故障排查

### 1. 日志没有显示请求详情

检查环境变量是否生效：

```bash
echo $LITELLM_LOG  # 应显示 DEBUG
```

如果未设置，重新设置并重启服务：

```bash
export LITELLM_LOG=DEBUG
freerouter reload
```

### 2. 日志文件过大

配置日志轮转：

```bash
# 使用 logrotate（Linux）
sudo tee /etc/logrotate.d/freerouter << EOF
~/.config/freerouter/freerouter.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF
```

### 3. 查看历史日志

```bash
# 查看最近 100 行
tail -n 100 ~/.config/freerouter/freerouter.log

# 搜索特定时间段
grep "2025-12-28 10:" ~/.config/freerouter/freerouter.log
```

## 安全注意事项

⚠️ **DEBUG 日志可能包含**：
- API Keys（部分遮蔽）
- 用户请求内容
- 模型响应内容

**不要将 DEBUG 日志分享给他人或上传到公共平台！**

---

**相关文档**：
- [LiteLLM Logging 文档](https://docs.litellm.ai/docs/observability/logging)
- [FreeRouter FAQ](FAQ.md)
