# 发布到 PyPI 指南

本指南介绍如何将 tc-pytools 发布到 PyPI（Python Package Index）。

## 前提准备

### 1. 注册 PyPI 账号

- **生产环境**: https://pypi.org/account/register/
- **测试环境**: https://test.pypi.org/account/register/ （推荐先在这里测试）

### 2. 生成 API Token

为了安全地发布包，推荐使用 API Token 而不是密码。

#### 在 PyPI 生成 Token：

1. 登录 PyPI: https://pypi.org/
2. 进入账户设置: https://pypi.org/manage/account/
3. 滚动到 "API tokens" 部分
4. 点击 "Add API token"
5. 填写 Token 名称（如 "tc-pytools"）
6. 选择作用域：
   - 首次发布选择 "Entire account"
   - 后续可以限制到特定项目
7. 点击 "Add token"
8. **重要**: 立即复制并保存 Token（只显示一次）

#### 在 Test PyPI 生成 Token（推荐先测试）：

同样的步骤，在 https://test.pypi.org/ 上操作。

### 3. 配置凭证

创建或编辑 `~/.pypirc` 文件：

```bash
# 创建配置文件
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # 你的 PyPI Token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # 你的 Test PyPI Token
EOF

# 设置正确的权限
chmod 600 ~/.pypirc
```

## 发布步骤

### 方式 1: 使用 uv（推荐）

uv 提供了最简单的发布方式：

```bash
# 1. 确保在项目目录
cd tc-pytools-v1.1

# 2. 清理旧的构建产物
make clean
# 或手动清理
rm -rf dist/ build/ *.egg-info

# 3. 构建包
uv build

# 4. 先发布到 Test PyPI 测试（推荐）
uv publish --publish-url https://test.pypi.org/legacy/

# 5. 验证测试版本
uv pip install --index-url https://test.pypi.org/simple/ tc-pytools

# 6. 测试通过后，发布到正式 PyPI
uv publish
```

### 方式 2: 使用 twine

如果需要更多控制，可以使用传统的 twine：

```bash
# 1. 安装 twine
uv pip install twine

# 2. 清理并构建
make clean
uv build

# 3. 检查构建产物
twine check dist/*

# 4. 上传到 Test PyPI
twine upload --repository testpypi dist/*

# 5. 上传到正式 PyPI
twine upload dist/*
```

### 方式 3: 使用 Makefile（已集成）

为了方便，我们在 Makefile 中添加了发布命令：

```bash
# 发布到 Test PyPI
make publish-test

# 发布到正式 PyPI
make publish
```

## 发布前检查清单

在发布之前，请确保：

- [ ] 版本号已更新（在 `pyproject.toml` 和 `gtf/__init__.py` 中）
- [ ] 所有测试通过（运行 `make ci` 或 `./ci.sh`）
- [ ] README.md 内容准确完整
- [ ] LICENSE 文件存在
- [ ] 代码已提交到 Git（如果使用版本控制）
- [ ] CHANGELOG 已更新（如果有）
- [ ] 依赖声明正确
- [ ] 包元数据完整（作者、邮箱、URL 等）

检查构建产物：

```bash
# 构建包
uv build

# 检查 dist/ 目录
ls -lh dist/

# 应该看到两个文件：
# - tc_pytools-1.1.0-py3-none-any.whl
# - tc_pytools-1.1.0.tar.gz

# 检查包内容
tar -tzf dist/tc_pytools-1.1.0.tar.gz
# 或
unzip -l dist/tc_pytools-1.1.0-py3-none-any.whl
```

## 发布流程示例

### 首次发布完整流程：

```bash
# 1. 更新版本号（如果需要）
# 编辑 pyproject.toml 中的 version = "1.1.0"
# 编辑 gtf/__init__.py 中的 __version__ = "1.1.0"

# 2. 运行测试
make ci

# 3. 清理旧构建
make clean

# 4. 构建包
uv build

# 5. 检查包
uv pip install twine  # 如果还没安装
twine check dist/*

# 6. 测试发布到 Test PyPI
uv publish --publish-url https://test.pypi.org/legacy/

# 7. 在测试环境安装验证
python -m pip install --index-url https://test.pypi.org/simple/ tc-pytools
rename-ngdc-genome-id --help

# 8. 确认无误后，发布到正式 PyPI
uv publish

# 9. 从正式 PyPI 安装验证
pip install tc-pytools
rename-ngdc-genome-id --help
```

## 版本管理

### 语义化版本

本项目使用语义化版本（SemVer）：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修正

示例：
- `1.0.0` - 初始稳定版
- `1.1.0` - 添加新功能
- `1.1.1` - 修复 bug
- `2.0.0` - 重大更新，可能不兼容

### 更新版本号

需要在两个地方更新：

1. `pyproject.toml`:
```toml
[project]
version = "1.1.0"
```

2. `gtf/__init__.py`:
```python
__version__ = "1.1.0"
```

建议使用工具自动化：

```bash
# 使用 sed 同时更新两个文件
NEW_VERSION="1.2.0"
sed -i "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" gtf/__init__.py
```

## 发布后

### 1. 创建 Git Tag

```bash
# 创建带注释的标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 推送标签到远程
git push origin v1.1.0
```

### 2. 创建 GitHub Release

如果使用 GitHub：

1. 进入仓库的 Releases 页面
2. 点击 "Create a new release"
3. 选择刚创建的标签
4. 填写发布说明
5. 可以附加构建产物（dist/ 中的文件）

### 3. 通知用户

- 更新 README.md 中的安装说明
- 发布更新日志
- 通知相关用户

## 故障排除

### 问题：包名已存在

如果包名 `tc-pytools` 已被占用：

1. 选择新的包名（在 `pyproject.toml` 中修改 `name`）
2. 或联系现有包的所有者

### 问题：认证失败

```bash
# 检查 ~/.pypirc 配置
cat ~/.pypirc

# 确保 token 格式正确（以 pypi- 开头）
# 确保文件权限正确
chmod 600 ~/.pypirc
```

### 问题：版本号冲突

PyPI 不允许覆盖已发布的版本，需要：

1. 增加版本号
2. 重新构建和发布

```bash
# 更新版本
sed -i 's/version = "1.1.0"/version = "1.1.1"/' pyproject.toml
uv build
uv publish
```

### 问题：构建失败

```bash
# 清理并重试
make clean
rm -rf .venv
uv sync
uv build
```

## 自动化发布（GitHub Actions）

可以使用 GitHub Actions 自动发布：

创建 `.github/workflows/publish.yml`（已在项目中提供）

发布流程：

1. 推送新标签：`git tag v1.1.0 && git push origin v1.1.0`
2. GitHub Actions 自动构建并发布到 PyPI
3. 无需手动操作

## 最佳实践

1. **始终先发布到 Test PyPI** 进行测试
2. **每次发布前运行完整测试** (`./ci.sh`)
3. **使用 API Token** 而不是密码
4. **保持版本号同步** （pyproject.toml 和 __init__.py）
5. **更新 CHANGELOG** 记录变更
6. **创建 Git 标签** 标记发布点
7. **不要删除已发布的版本** （PyPI 不允许）
8. **使用语义化版本**

## 相关链接

- PyPI 官网: https://pypi.org/
- Test PyPI: https://test.pypi.org/
- PyPI 帮助: https://pypi.org/help/
- Python 打包指南: https://packaging.python.org/
- uv 文档: https://github.com/astral-sh/uv

## 常用命令速查

```bash
# 构建
uv build

# 检查
twine check dist/*

# 测试发布
uv publish --publish-url https://test.pypi.org/legacy/

# 正式发布
uv publish

# 从 Test PyPI 安装
pip install --index-url https://test.pypi.org/simple/ tc-pytools

# 从 PyPI 安装
pip install tc-pytools
```
