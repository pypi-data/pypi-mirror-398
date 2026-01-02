# 发布到 PyPI 指南

## 准备工作

### 1. 安装构建工具

```bash
pip install --upgrade pip build twine
```

### 2. 注册 PyPI 账号

- **PyPI 正式**: https://pypi.org/account/register/
- **TestPyPI 测试**: https://test.pypi.org/account/register/

### 3. 创建 API Token

访问 https://pypi.org/manage/account/token/ 创建 API token

在 `~/.pypirc` 文件中配置：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZw...
```

## 发布流程

### 步骤 1: 更新版本号

编辑 `freerouter/__version__.py`:

```python
__version__ = "0.1.0"  # 更新版本号
```

### 步骤 2: 运行测试

```bash
# 确保所有测试通过
pytest --cov=freerouter

# 或
pytest
```

### 步骤 3: 构建包

```bash
# 清理旧的构建
rm -rf build/ dist/ *.egg-info

# 构建包
python -m build
```

这会在 `dist/` 目录生成：
- `freerouter-0.1.0.tar.gz` (源码包)
- `freerouter-0.1.0-py3-none-any.whl` (wheel 包)

### 步骤 4: 测试上传到 TestPyPI

```bash
# 上传到测试环境
python -m twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ --no-deps freerouter
```

### 步骤 5: 正式发布到 PyPI

```bash
# 上传到 PyPI
python -m twine upload dist/*
```

### 步骤 6: 验证安装

```bash
# 从 PyPI 安装
pip install freerouter

# 验证
freerouter --version
```

### 步骤 7: 创建 GitHub Release

```bash
# 打标签
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# 在 GitHub 上创建 Release
# https://github.com/mmdsnb/freerouter/releases/new
```

## 快速发布脚本

```bash
#!/bin/bash
# publish.sh - PyPI publishing script

set -e

echo "=== FreeRouter 发布脚本 ==="

# 1. 检查工作区是否干净
if [[ -n $(git status -s) ]]; then
    echo "错误: 有未提交的更改"
    exit 1
fi

# 2. 运行测试
echo "运行测试..."
pytest --cov=freerouter

# 3. 清理旧构建
echo "清理旧构建..."
rm -rf build/ dist/ *.egg-info

# 4. 构建
echo "构建包..."
python -m build

# 5. 检查包
echo "检查包..."
python -m twine check dist/*

# 6. 上传到 TestPyPI
echo "上传到 TestPyPI..."
python -m twine upload --repository testpypi dist/*

# 7. 等待确认
read -p "TestPyPI 测试通过？继续上传到 PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "上传到 PyPI..."
    python -m twine upload dist/*
    echo "✓ 发布成功!"
fi
```

## 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- **MAJOR.MINOR.PATCH** (如 1.2.3)
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的 bug 修复

当前版本: `0.1.0` (Alpha 阶段)

## 发布检查清单

- [ ] 所有测试通过
- [ ] 版本号已更新
- [ ] CHANGELOG.md 已更新
- [ ] README.md 准确无误
- [ ] 没有敏感信息（API key、密码等）
- [ ] LICENSE 文件存在
- [ ] 依赖版本正确
- [ ] 本地测试安装成功
- [ ] TestPyPI 测试成功

## 常见问题

### Q: 包名已被占用怎么办？
A: 需要换一个包名，修改 setup.py 和 pyproject.toml 中的 name 字段

### Q: 上传失败 403 Forbidden？
A: 检查 PyPI token 是否正确配置在 ~/.pypirc

### Q: 如何删除已发布的版本？
A: PyPI 不允许删除版本，只能发布新版本覆盖

### Q: 如何撤回错误的发布？
A: 无法撤回，只能立即发布修复版本（递增版本号）

## 参考资料

- [Python 打包指南](https://packaging.python.org/)
- [Twine 文档](https://twine.readthedocs.io/)
- [PyPI 帮助](https://pypi.org/help/)
