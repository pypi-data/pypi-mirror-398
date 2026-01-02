# 查看 API 请求详情 - 完整指南

## 方法 1：全局启用（查看所有请求）

### 设置环境变量并重新生成配置

```bash
# 启用原始请求日志记录
export FREEROUTER_LOG_RAW=true

# 重新生成配置（应用新设置）
freerouter fetch

# 重启服务
freerouter reload

# 查看日志
freerouter logs
```

### 你会看到的内容

```
POST Request Sent from LiteLLM:
curl -X POST \
https://api.xiaomimimo.com/v1/chat/completions \
-H 'content-type: application/json' \
-H 'Authorization: Bearer sk-cdei7y********' \
-d '{"model": "mimo-v2-flash", "messages": [{"role": "user", "content": "1+1=?"}]}'

RAW RESPONSE:
{"id":"chatcmpl-...","object":"chat.completion","created":1735329926,"model":"mimo-v2-flash","choices":[{"index":0,"message":{"role":"assistant","content":"2"},"finish_reason":"stop"}],"usage":{"prompt_tokens":30,"completion_tokens":2,"total_tokens":32}}
```

## 方法 2：单次请求调试（推荐用于调试）

### 在请求中添加 `metadata`

```bash
curl -X POST 'http://localhost:4000/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-1234' \
  -d '{
    "model": "mimo-v2-flash",
    "messages": [
      {"role": "user", "content": "1+1=?"}
    ],
    "metadata": {
      "log_raw_request": true
    }
  }'
```

### 使用 Python SDK

```python
import openai

client = openai.OpenAI(
    api_key="sk-1234",
    base_url="http://localhost:4000"
)

response = client.chat.completions.create(
    model="mimo-v2-flash",
    messages=[
        {"role": "user", "content": "1+1=?"}
    ],
    extra_body={
        "metadata": {
            "log_raw_request": True
        }
    }
)

print(response)
```

## 方法 3：单请求详细调试

使用 `litellm_request_debug` 参数：

```bash
curl -X POST 'http://localhost:4000/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-1234' \
  -d '{
    "model": "mimo-v2-flash",
    "messages": [
      {"role": "user", "content": "1+1=?"}
    ],
    "litellm_request_debug": true
  }'
```

这会显示更详细的调试信息，包括：
- 路由决策过程
- 重试逻辑
- 错误堆栈（如果有）

## 对比三种方法

| 方法 | 适用场景 | 日志详细程度 | 性能影响 |
|------|---------|------------|---------|
| 全局启用 (`FREEROUTER_LOG_RAW`) | 开发环境，需要查看所有请求 | ⭐⭐⭐ | 中等 |
| 单次请求 (`log_raw_request`) | 调试特定请求 | ⭐⭐⭐ | 极小 |
| 详细调试 (`litellm_request_debug`) | 排查错误，理解路由逻辑 | ⭐⭐⭐⭐⭐ | 较大 |

## 日志内容详解

### 1. 请求部分

```
POST Request Sent from LiteLLM:
curl -X POST \
https://api.xiaomimimo.com/v1/chat/completions \
-H 'content-type: application/json' \
-H 'Authorization: Bearer sk-cdei7y********' \
-d '{"model": "mimo-v2-flash", "messages": [...]}'
```

**包含信息**：
- ✅ 实际请求的 URL（API 端点）
- ✅ 请求头（Content-Type, Authorization 等）
- ✅ 完整的请求体（model, messages, temperature 等参数）
- ✅ 可直接复制的 curl 命令

### 2. 响应部分

```
RAW RESPONSE:
{"id":"chatcmpl-...","choices":[...],"usage":{...}}
```

**包含信息**：
- ✅ HTTP 状态码
- ✅ 完整的 JSON 响应
- ✅ Token 使用量
- ✅ 模型返回内容

## 安全注意事项

⚠️ **API Keys 会被自动遮蔽**

日志中的敏感信息会被部分隐藏：
```
Authorization: Bearer sk-cdei7y********
```

但仍然建议：
- 不要在生产环境启用全局日志
- 不要分享日志文件给他人
- 定期清理日志文件

## 快速命令

```bash
# 启用原始请求日志
export FREEROUTER_LOG_RAW=true
freerouter fetch && freerouter reload

# 查看实时日志
freerouter logs

# 禁用原始请求日志（恢复默认）
unset FREEROUTER_LOG_RAW
freerouter fetch && freerouter reload
```

## 常见问题

### Q1: 为什么没有看到 HTTP 请求详情？

**A:** 需要确保以下两点：
1. 设置了 `FREEROUTER_LOG_RAW=true`
2. 运行了 `freerouter fetch` 重新生成配置
3. 运行了 `freerouter reload` 重启服务

### Q2: 日志文件在哪里？

**A:**
- 用户级别：`~/.config/freerouter/freerouter.log`
- 项目级别：`./config/freerouter.log`

### Q3: 如何只看特定供应商的请求？

**A:** 使用 grep 过滤：

```bash
# 只看 xiaomimimo 的请求
freerouter logs | grep -A 20 "api.xiaomimimo.com"

# 只看 OpenRouter 的请求
freerouter logs | grep -A 20 "openrouter.ai"
```

### Q4: 如何保存日志到文件？

**A:**

```bash
# 保存最近的日志
freerouter logs > debug-$(date +%Y%m%d-%H%M%S).log

# 实时保存日志
freerouter logs | tee debug.log
```

## 进阶用法

### 组合使用 DEBUG 模式

```bash
# 同时启用详细日志和原始请求
export LITELLM_LOG=DEBUG
export FREEROUTER_LOG_RAW=true
freerouter fetch && freerouter reload
```

这会显示：
- LiteLLM 内部调试信息
- 路由决策过程
- 完整的 HTTP 请求/响应
- 性能指标

### 使用 jq 格式化 JSON

```bash
# 提取并格式化响应
freerouter logs | grep "RAW RESPONSE:" -A 1 | jq .
```

## 相关文档

- [LiteLLM Logging 文档](https://docs.litellm.ai/docs/observability/logging)
- [LiteLLM Debugging 文档](https://docs.litellm.ai/docs/debugging)
- [FreeRouter 日志配置指南](logging-guide.md)

---

**最后更新**：2025-12-28
