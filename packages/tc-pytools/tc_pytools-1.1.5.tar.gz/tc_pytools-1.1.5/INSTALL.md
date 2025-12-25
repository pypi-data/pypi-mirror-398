# TC PyTools 安装指南

## 快速安装

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 进入项目目录
cd tc-pytools-v1.1

# 3. 安装工具包
uv sync

# 4. 验证安装
uv run rename-ngdc-genome-id --help
```

## 详细安装步骤

### 1. 安装 uv

uv 是一个快速的 Python 包管理器，用于管理本项目的依赖。

#### Linux/macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 使用 pip 安装

```bash
pip install uv
```

安装后验证：

```bash
uv --version
```

### 2. 安装工具包

根据你的使用场景选择不同的安装方式：

#### 场景 1: 日常使用（推荐）

如果你只是想使用工具，不需要修改代码：

```bash
# 进入项目目录
cd tc-pytools-v1.1

# 安装依赖
uv sync

# 使用工具
uv run rename-ngdc-genome-id -f input.fasta -o output.fasta
```

**优点**：简单快速，所有依赖自动管理

#### 场景 2: 全局安装

如果你想在任何地方都能直接使用命令（不需要 `uv run` 前缀）：

```bash
# 进入项目目录
cd tc-pytools-v1.1

# 安装到用户环境（推荐）
uv pip install --user -e .

# 或安装到系统（可能需要 sudo）
uv pip install -e .
```

安装后可以直接使用：

```bash
rename-ngdc-genome-id -f input.fasta -o output.fasta
```

**优点**：命令更简洁，不需要 `uv run`

**注意**：确保 `~/.local/bin` 在你的 PATH 中（使用 `--user` 时）

#### 场景 3: 开发模式

如果你需要修改代码或贡献到项目：

```bash
# 进入项目目录
cd tc-pytools-v1.1

# 同步所有依赖（包括开发依赖）
uv sync

# 安装 pre-commit 钩子（可选）
uv run pre-commit install

# 运行测试验证
uv run pytest

# 运行 CI 检查
./ci.sh
```

**优点**：包含测试工具、代码检查工具等开发依赖

#### 场景 4: 从构建包安装

如果你想从构建的包安装：

```bash
# 进入项目目录
cd tc-pytools-v1.1

# 构建包
uv build

# 这会在 dist/ 目录生成两个文件：
# - tc_pytools-1.1.0-py3-none-any.whl
# - tc_pytools-1.1.0.tar.gz

# 安装 wheel 文件
uv pip install dist/tc_pytools-1.1.0-py3-none-any.whl

# 或安装 tar.gz 文件
uv pip install dist/tc_pytools-1.1.0.tar.gz
```

**优点**：可以分发给其他用户

### 3. 验证安装

```bash
# 方式 1: 使用 uv run（开发模式）
uv run rename-ngdc-genome-id --help

# 方式 2: 直接运行（全局安装后）
rename-ngdc-genome-id --help

# 方式 3: 使用 Python 模块
uv run python -m gtf.rename_ngdc_genome_id --help
```

如果看到帮助信息，说明安装成功！

## 常见问题

### Q: uv 命令找不到

**解决方案**：

1. 确保安装脚本执行成功
2. 添加 uv 到 PATH：

```bash
# 对于 Linux/macOS，添加到 ~/.bashrc 或 ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc
```

### Q: 提示 "No module named 'gtf'"

**解决方案**：

确保已经运行了 `uv sync` 或 `uv pip install -e .`

### Q: 权限错误

**解决方案**：

使用 `--user` 标志安装到用户目录：

```bash
uv pip install --user -e .
```

### Q: 想要卸载

**解决方案**：

```bash
# 卸载包
uv pip uninstall tc-pytools

# 清理虚拟环境
rm -rf .venv
```

### Q: Python 版本问题

本项目要求 Python >= 3.8

**检查 Python 版本**：

```bash
python --version
# 或
python3 --version
```

**使用特定 Python 版本**：

```bash
# 使用 uv 安装特定 Python 版本
uv python install 3.11

# 使用该版本创建环境
uv sync
```

## 升级和更新

### 更新工具包

```bash
# 拉取最新代码（如果使用 git）
git pull

# 重新同步依赖
uv sync

# 或重新安装
uv pip install -e . --force-reinstall
```

### 更新 uv

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install --upgrade uv
```

## 不同环境的推荐方式

| 环境 | 推荐方式 | 命令 |
|------|---------|------|
| 个人使用 | 开发模式 | `uv sync` + `uv run` |
| 服务器部署 | 全局安装 | `uv pip install -e .` |
| 开发贡献 | 开发模式 | `uv sync` + CI 工具 |
| 分发给他人 | 构建包 | `uv build` |

## 下一步

安装完成后，请查看：

- [README.md](README.md) - 项目总览
- [QUICKREF.md](QUICKREF.md) - 快速参考指南
- [gtf/docs/README.md](gtf/docs/README.md) - 工具使用说明

开始使用：

```bash
# 查看工具帮助
uv run rename-ngdc-genome-id --help

# 运行示例
uv run rename-ngdc-genome-id -f example.fasta -o output.fasta
```
