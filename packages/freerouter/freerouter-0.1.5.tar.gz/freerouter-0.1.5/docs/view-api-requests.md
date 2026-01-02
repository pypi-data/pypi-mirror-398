# 如何查看 API 请求详情

## 🚀 快速开始（推荐）

### 方式 1：使用 --debug 标志（最简单）

```bash
# 启动服务（debug 模式）
freerouter start --debug

# 或重新加载服务（debug 模式）
freerouter reload --debug
```

**就这么简单！** 无需手动设置环境变量，配置会自动生成。

### 方式 2：手动设置环境变量

```bash
# 设置环境变量
export FREEROUTER_LOG_RAW=true
export LITELLM_LOG=DEBUG

# 重新生成配置
freerouter fetch

# 启动服务
freerouter start
```

### 2. 发送请求

```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-1234' \
  -d '{
    "model": "mimo-v2-flash",
    "messages": [{"role": "user", "content": "hello"}]
  }'
```

### 3. 查看日志

```bash
# 实时查看日志
freerouter logs

# 或直接查看日志文件
tail -f ~/.config/freerouter/freerouter.log
# 或项目级别
tail -f ./config/freerouter.log
```

## 日志内容示例

启用后，你会看到：

```
POST Request Sent from LiteLLM:
curl -X POST \
https://api.xiaomimimo.com/v1/ \
-H 'Authorization: Be****2g' \
-d '{'model': 'mimo-v2-flash', 'messages': [{'role': 'user', 'content': 'hello'}], 'extra_body': {}}'

RAW RESPONSE:
{"id": "d713ae8975d0426a94d58e5e0327528b", "choices": [{"message": {"content": "Hello! How can I help you today?"}}], "usage": {"total_tokens": 37}}
```

## 包含的信息

✅ **请求部分**：
- 实际的 API 端点 URL
- HTTP 方法和请求头
- 完整的请求体（model, messages 等）
- 可直接复制执行的 curl 命令

✅ **响应部分**：
- 完整的 JSON 响应
- Token 使用量
- 模型返回内容

## 配置说明

### 环境变量

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `FREEROUTER_LOG_RAW` | 启用原始请求日志 | `false` |
| `LITELLM_LOG` | LiteLLM 日志级别 | `INFO` |

### 配置文件

修改会自动应用到 `config.yaml`：

```yaml
litellm_settings:
  log_raw_request_response: true  # 由 FREEROUTER_LOG_RAW 控制
```

## 常用命令

```bash
# 🔥 使用 --debug 标志（推荐）
freerouter start --debug         # 启动 debug 模式
freerouter reload --debug        # 重启 debug 模式
freerouter reload -rd            # 刷新配置 + debug 模式

# 实时查看日志
freerouter logs

# 过滤特定供应商
freerouter logs | grep "api.xiaomimimo.com"

# 只看 POST 请求
freerouter logs | grep -A 10 "POST Request"

# 只看响应
freerouter logs | grep -A 5 "RAW RESPONSE"

# 禁用日志（恢复默认）
freerouter reload                # 重启（不带 --debug）
```

## 高级用法

### 保存日志到文件

```bash
# 保存完整日志
freerouter logs > debug-$(date +%Y%m%d-%H%M%S).log

# 只保存请求/响应
freerouter logs | grep -A 20 "POST Request\|RAW RESPONSE" > requests.log
```

### 使用 jq 格式化 JSON

```bash
# 格式化响应
freerouter logs | grep "RAW RESPONSE" -A 1 | tail -1 | jq .
```

### 调试特定模型

```bash
# 只看 mimo-v2-flash 的请求
freerouter logs | grep -B 2 -A 15 "mimo-v2-flash"
```

## 安全注意事项

⚠️ **API Keys 会被自动遮蔽**

日志中的敏感信息会被部分隐藏：
```
Authorization: Be****2g
```

但仍然建议：
- ❌ 不要在生产环境启用原始日志
- ❌ 不要分享日志文件
- ✅ 仅在开发/调试时使用
- ✅ 定期清理日志文件

## 性能影响

| 模式 | CPU | 磁盘 | 日志大小 |
|------|-----|------|---------|
| 默认 (INFO) | 低 | 小 | ~10 MB/天 |
| DEBUG + RAW | 中 | 大 | ~100 MB/天 |

**建议**：
- 开发环境：启用 DEBUG + RAW
- 生产环境：使用 INFO 级别

## 故障排查

### Q: 没有看到 "POST Request" 日志？

**A:** 检查以下条件：

```bash
# 1. 确认环境变量已设置
echo $FREEROUTER_LOG_RAW  # 应输出 true
echo $LITELLM_LOG          # 应输出 DEBUG

# 2. 确认配置文件正确
cat config/config.yaml | grep log_raw_request_response
# 应显示: log_raw_request_response: true

# 3. 确认服务以 DEBUG 模式启动
freerouter stop
LITELLM_LOG=DEBUG freerouter start

# 4. 发送测试请求后查看
freerouter logs | grep "POST Request"
```

### Q: 日志文件在哪里？

**A:**
- 用户级别：`~/.config/freerouter/freerouter.log`
- 项目级别：`./config/freerouter.log`

```bash
# 查找日志文件位置
freerouter status
```

### Q: 如何清理日志？

**A:**

```bash
# 清空日志文件
echo "" > config/freerouter.log

# 或删除后重启
rm config/freerouter.log
freerouter reload
```

## 完整示例

从零开始查看 API 请求：

```bash
# 步骤 1: 启动 debug 模式（一行命令）
freerouter start --debug

# 步骤 2: 在新终端查看日志
freerouter logs

# 步骤 3: 发送测试请求
curl -X POST http://localhost:4000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-1234' \
  -d '{"model": "your-model", "messages": [{"role": "user", "content": "test"}]}'

# 步骤 4: 查看请求详情（在日志终端）
# 你会看到完整的 curl 命令和响应

# 完成后，关闭 debug 模式
freerouter reload   # 不带 --debug
```

## 相关文档

- [日志配置指南](logging-guide.md) - 完整的日志配置选项
- [调试请求指南](debug-requests.md) - 更多调试技巧
- [LiteLLM 官方文档](https://docs.litellm.ai/docs/observability/logging)

---

**最后更新**：2025-12-28
