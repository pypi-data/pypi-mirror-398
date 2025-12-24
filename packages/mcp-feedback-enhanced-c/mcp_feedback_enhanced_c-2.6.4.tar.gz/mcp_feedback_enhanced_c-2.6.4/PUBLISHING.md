# PyPI 发布指南

本文档提供将 `mcp-feedback-enhanced-c` 发布到 PyPI 的完整步骤。

## 📋 前置准备

### 1. 注册 PyPI 账号
- 访问 [PyPI](https://pypi.org/account/register/) 注册账号
- 访问 [TestPyPI](https://test.pypi.org/account/register/) 注册测试账号（推荐）

### 2. 创建 API Token
PyPI 推荐使用 API Token 而非密码进行上传。

#### 创建 PyPI API Token：
1. 登录 [PyPI](https://pypi.org)
2. 访问 Account Settings → API tokens
3. 点击 "Add API token"
4. Token name: `mcp-feedback-enhanced-c`
5. Scope: 选择 "Entire account" 或特定项目
6. **重要**: 复制生成的 token（格式：`pypi-...`），只显示一次！

#### 创建 TestPyPI API Token（用于测试）：
1. 登录 [TestPyPI](https://test.pypi.org)
2. 重复上述步骤创建测试环境的 token

### 3. 配置 `.pypirc`
在你的 home 目录创建或编辑 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

**重要**：替换 `pypi-YOUR_*_TOKEN_HERE` 为实际的 token。

文件权限设置（Linux/macOS）：
```bash
chmod 600 ~/.pypirc
```

## 🏗️ 构建包

### 1. 清理旧文件
```bash
rm -rf dist/ build/ *.egg-info
```

### 2. 构建新包
```bash
uv build
```

这将生成：
- `dist/mcp_feedback_enhanced_c-2.6.1.tar.gz` (源码包)
- `dist/mcp_feedback_enhanced_c-2.6.1-py3-none-any.whl` (wheel 包)

### 3. 验证包
```bash
uv run twine check dist/*
```

确保所有检查都显示 `PASSED`。

## 🧪 测试发布（推荐）

先发布到 TestPyPI 进行测试，确保一切正常。

### 1. 上传到 TestPyPI
```bash
uv run twine upload --repository testpypi dist/*
```

### 2. 测试安装
```bash
# 从 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-feedback-enhanced-c

# 测试命令
mcp-feedback-enhanced version
```

**注意**: `--extra-index-url https://pypi.org/simple/` 用于安装依赖包（因为 TestPyPI 可能缺少某些依赖）。

### 3. 验证功能
```bash
# 测试 Web UI
uvx --from https://test.pypi.org/simple/ mcp-feedback-enhanced-c test --web

# 测试桌面应用
uvx --from https://test.pypi.org/simple/ mcp-feedback-enhanced-c test --desktop
```

## 🚀 正式发布

确认测试无误后，发布到正式 PyPI。

### 1. 上传到 PyPI
```bash
uv run twine upload dist/*
```

或使用指定仓库：
```bash
uv run twine upload --repository pypi dist/*
```

### 2. 验证发布
访问包页面确认：
- https://pypi.org/project/mcp-feedback-enhanced-c/

### 3. 测试安装
```bash
# 安装
pip install mcp-feedback-enhanced-c

# 或使用 uvx
uvx mcp-feedback-enhanced-c@latest version

# 测试功能
uvx mcp-feedback-enhanced-c@latest test --web
```

## 📝 发布后检查清单

- [ ] 包在 PyPI 上可见：https://pypi.org/project/mcp-feedback-enhanced-c/
- [ ] 可以通过 `pip install mcp-feedback-enhanced-c` 安装
- [ ] 可以通过 `uvx mcp-feedback-enhanced-c@latest` 运行
- [ ] README 在 PyPI 页面正确显示
- [ ] 所有链接可正常访问
- [ ] 版本号正确：2.6.1

## 🔄 后续版本发布

### 1. 更新版本号
编辑 `pyproject.toml`:
```toml
version = "2.6.2"  # 或其他新版本
```

### 2. 更新 CHANGELOG
记录版本更改内容。

### 3. 提交更改
```bash
git add .
git commit -m "Bump version to 2.6.2"
git push
```

### 4. 创建 Git Tag
```bash
git tag -a v2.6.2 -m "Release version 2.6.2"
git push origin v2.6.2
```

### 5. 构建并发布
```bash
# 清理旧文件
rm -rf dist/

# 构建新包
uv build

# 验证
uv run twine check dist/*

# 测试发布（可选）
uv run twine upload --repository testpypi dist/*

# 正式发布
uv run twine upload dist/*
```

## 🛠️ 常见问题

### Q: 上传失败，提示包已存在
A: PyPI 不允许重复上传相同版本。需要：
1. 增加版本号
2. 重新构建
3. 重新上传

### Q: README 在 PyPI 页面显示不正确
A: 确保：
- `pyproject.toml` 中 `readme = "README.md"` 配置正确
- README.md 使用标准 Markdown 格式
- 使用 `twine check` 验证

### Q: 如何删除已发布的包？
A:
- PyPI 不支持删除特定版本（防止破坏依赖）
- 可以 "yank" 版本使其不推荐使用：
  ```bash
  twine upload --repository pypi dist/* --skip-existing
  ```
- 在 PyPI 网站上可以标记版本为 "yanked"

### Q: 忘记保存 API Token 怎么办？
A:
1. 登录 PyPI
2. 访问 API tokens 页面
3. 删除旧 token
4. 创建新 token
5. 更新 `~/.pypirc`

## 📚 参考资源

- [PyPI 官方文档](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine 文档](https://twine.readthedocs.io/)
- [语义化版本规范](https://semver.org/lang/zh-CN/)
- [Python 打包指南](https://packaging.python.org/)

## 🎉 恭喜！

你的包现在已经发布到 PyPI，全世界的开发者都可以通过以下方式使用：

```bash
# 使用 pip 安装
pip install mcp-feedback-enhanced-c

# 使用 uvx 运行（推荐）
uvx mcp-feedback-enhanced-c@latest version
uvx mcp-feedback-enhanced-c@latest test --web
```

**重要说明**：
- 包提供的可执行文件名为：`mcp-feedback-enhanced-c`
- 直接使用 `uvx mcp-feedback-enhanced-c` 即可，无需额外指定可执行文件名
