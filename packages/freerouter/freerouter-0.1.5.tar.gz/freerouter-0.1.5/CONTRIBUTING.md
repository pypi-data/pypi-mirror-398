# 贡献指南

感谢你对 FreeRouter 的兴趣！

## 开发环境设置

```bash
# Clone repository
git clone https://github.com/mmdsnb/freerouter.git
cd freerouter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies and dev dependencies
pip install -e ".[dev]"
```

## 添加新 Provider

1. 在 `freerouter/providers/` 创建新文件
2. 继承 `BaseProvider` 并实现必需方法
3. 在 `ProviderFactory` 添加分支
4. 编写单元测试
5. 更新文档

详见 [CLAUDE.md](CLAUDE.md)

## 代码规范

- 使用 `black` 格式化代码
- 使用 `flake8` 检查代码
- 编写单元测试
- 添加文档字符串

```bash
# Format code
black freerouter/ tests/

# Check code
flake8 freerouter/ tests/

# Run tests
pytest
```

## 提交 Pull Request

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

谢谢！
