# PyPI 发布检查清单

## ✅ 已完成

1. **项目结构** - 正确的 src 布局
2. **pyproject.toml** - 完整的元数据配置
3. **LICENSE** - MIT 许可证
4. **README.md** - 完整的英文文档
5. **README_zh.md** - 完整的中文文档
6. **资源文件** - alpha map 图片已正确打包
7. **构建测试** - 包构建成功，测试通过

## ⚠️ 发布前需要确认

1. **GitHub 仓库 URL** - pyproject.toml 中的 `YOUR_USERNAME` 需要替换为实际的 GitHub 用户名
2. **PyPI 账号** - 需要在 https://pypi.org 注册账号
3. **API Token** - 建议使用 API token 而不是密码

## 📦 发布步骤

### 1. 更新 pyproject.toml 中的 GitHub URL

```toml
[project.urls]
Homepage = "https://github.com/YOUR_ACTUAL_USERNAME/py-gemini-watermark-remover"
Repository = "https://github.com/YOUR_ACTUAL_USERNAME/py-gemini-watermark-remover"
Issues = "https://github.com/YOUR_ACTUAL_USERNAME/py-gemini-watermark-remover/issues"
```

### 2. 发布到 TestPyPI（推荐先测试）

```bash
# 发布到测试服务器
uv publish --publish-url https://test.pypi.org/legacy/

# 测试安装
pip install --index-url https://test.pypi.org/simple/ py-gemini-watermark-remover
```

### 3. 发布到正式 PyPI

```bash
# 发布到正式 PyPI
uv publish

# 用户可以通过以下命令安装
pip install py-gemini-watermark-remover
```

## 📝 注意事项

- **包名唯一性**: `py-gemini-watermark-remover` 必须在 PyPI 上未被使用
- **版本号**: 每次发布必须使用新的版本号（当前是 0.1.0）
- **不可撤销**: 发布到 PyPI 的版本无法删除，只能标记为 yanked
- **GitHub 先行**: 建议先将代码推送到 GitHub，再发布到 PyPI

## 🔐 配置 PyPI Token

```bash
# 在 PyPI 网站生成 token 后
uv publish --token pypi-YOUR_TOKEN_HERE

# 或者配置环境变量
export UV_PUBLISH_TOKEN=pypi-YOUR_TOKEN_HERE
uv publish
```
