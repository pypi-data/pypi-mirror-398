# TC PyTools

基因组数据处理工具集。

## 项目概述

本项目使用 [uv](https://github.com/astral-sh/uv) 进行包管理和依赖管理，包含多个用于基因组数据处理的工具。

## 安装

### 前提条件

需要先安装 [uv](https://github.com/astral-sh/uv)（快速的 Python 包管理器）：

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 安装工具包

#### 方式 1: 开发模式安装（推荐用于开发）

```bash
# 进入项目目录
cd tc-pytools-v2

# 同步依赖并安装包（可编辑模式）
uv sync

# 此时可以直接使用 uv run 运行命令
uv run rename-ngdc-genome-id --help
```

#### 方式 2: 安装到用户环境（推荐用于日常使用）

```bash
# 进入项目目录
cd tc-pytools-v2

# 使用 uv pip 安装到当前 Python 环境
uv pip install -e .

# 或安装到系统（需要激活相应的虚拟环境）
# 激活虚拟环境后
pip install -e .

# 安装后可以直接使用命令
rename-ngdc-genome-id --help
```

#### 方式 3: 从源码构建并安装

```bash
# 构建包
uv build

# 安装构建的包
uv pip install dist/tc_pytools-1.1.0-py3-none-any.whl
```

## 工具列表

| 工具名称 | 功能描述 | 主要用途 | 文档链接 |
|---------|---------|---------|---------|
| `tc-rename-genome-id` | 重命名基因组染色体 ID | 支持 NGDC 基因组（自动提取 OriSeqID）和自定义映射两种模式，可同时处理 FASTA 和 GFF 文件 | [详细文档](genome/docs/rename-genome-id.md) |
| `tc-table2vcf` | 表格转换为 VCF 格式 | 将包含 chrom、pos、refer、alt 四列的表格文件转换为标准 VCF 格式文件 | - |

> 💡 每个工具都有详细的使用文档，请点击文档链接查看具体用法和示例。

## 开发

### 快速命令

```bash
make help          # 查看所有可用命令
make test          # 运行测试
make ci            # 运行完整 CI 检查
./ci.sh            # 运行本地 CI 脚本
```

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov

# 查看 HTML 覆盖率报告
uv run pytest --cov --cov-report=html
# 打开 htmlcov/index.html
```

### 代码质量

```bash
# 代码格式化
make format

# 代码检查
make lint

# 类型检查
make type-check
```

### 本地 CI

项目提供三种本地 CI 方式：

1. **CI 脚本**: `./ci.sh`
2. **Make 命令**: `make ci`
3. **Pre-commit**: `uv run pre-commit run --all-files`

详细使用说明请参考 [QUICKREF.md](QUICKREF.md)

## 项目结构

```
tc-pytools-v1.1/
├── gtf/                    # GTF 相关工具
│   ├── rename_ngdc_genome_id.py
│   ├── docs/              # 工具文档
│   └── tests/             # 单元测试
├── pyproject.toml         # 项目配置
├── Makefile              # Make 命令
├── ci.sh                 # CI 脚本
└── QUICKREF.md           # 快速参考
```

## 文档

- **[INSTALL.md](INSTALL.md)** - 详细安装指南（推荐首先阅读）
- **[PUBLISH.md](PUBLISH.md)** - PyPI 发布指南
- [QUICKREF.md](QUICKREF.md) - 快速参考指南（中文）
- [CHANGELOG.md](CHANGELOG.md) - 版本更新日志
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - 项目配置说明
- 各工具的详细文档位于对应的 `docs/` 目录下

## 许可证

MIT
