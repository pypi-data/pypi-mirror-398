# TC PyTools - 快速参考指南

## 安装工具包

### 首次安装

```bash
# 1. 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 进入项目目录
cd tc-pytools-v1.1

# 3. 开发模式安装（推荐）
uv sync

# 4. 验证安装
uv run rename-ngdc-genome-id --help
```

### 安装到系统（可选）

```bash
# 方式 1: 使用 uv pip（推荐）
uv pip install -e .

# 方式 2: 构建后安装
uv build
uv pip install dist/tc_pytools-1.1.0-py3-none-any.whl

# 安装后可直接使用
rename-ngdc-genome-id --help
```

## 项目管理

### 使用 uv 管理依赖
```bash
# 同步所有依赖（包括开发依赖）
uv sync

# 只同步生产依赖
uv sync --no-dev

# 添加新的依赖
uv add <package-name>

# 添加开发依赖
uv add --dev <package-name>

# 更新依赖
uv lock --upgrade
uv sync
```

### 使用 Make 命令
```bash
# 查看所有可用命令
make help

# 安装依赖
make install

# 运行测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 代码格式化
make format

# 检查代码格式
make format-check

# 运行代码检查
make lint

# 自动修复代码问题
make lint-fix

# 运行类型检查
make type-check

# 运行完整的 CI 检查
make ci

# 清理构建产物
make clean

# 构建包
make build
```

## 本地 CI 配置

### 方式 1: 使用 CI 脚本
```bash
./ci.sh
```

此脚本会运行：
- 依赖同步检查
- 代码格式检查 (ruff format)
- 代码质量检查 (ruff check)
- 类型检查 (mypy)
- 单元测试 (pytest)
- 测试覆盖率报告

### 方式 2: 使用 pre-commit
```bash
# 安装 pre-commit 钩子
make pre-commit-install
# 或
uv run pre-commit install

# 手动运行所有检查
make pre-commit-run
# 或
uv run pre-commit run --all-files
```

### 方式 3: 手动运行各项检查
```bash
# 代码格式检查
uv run ruff format --check .

# 代码质量检查
uv run ruff check .

# 类型检查
uv run mypy genome --ignore-missing-imports

# 运行测试
uv run pytest -v

# 生成覆盖率报告
uv run pytest --cov=genome --cov-report=html
```

## 运行项目

```bash
# 使用 uv run
uv run rename-ngdc-genome-id -f genome.fasta -o output.fasta

# 处理 GFF 文件
uv run rename-ngdc-genome-id -f genome.fasta -o output.fasta -g input.gff -og output.gff

# 在安装后直接运行
rename-ngdc-genome-id -f genome.fasta -o output.fasta
```

## 开发工作流

### 添加新功能
1. 创建新分支
2. 编写代码
3. 添加测试
4. 运行 `make ci` 确保所有检查通过
5. 提交代码

### 修复代码问题
```bash
# 自动格式化代码
make format

# 自动修复可修复的问题
make lint-fix

# 运行类型检查
make type-check
```

## 配置文件说明

- `pyproject.toml`: 项目配置、依赖管理、构建配置
- `ruff.toml`: Ruff 代码检查和格式化配置
- `.pre-commit-config.yaml`: pre-commit 钩子配置
- `.python-version`: 项目使用的 Python 版本
- `ci.sh`: 本地 CI 脚本
- `Makefile`: 常用命令快捷方式
- `.github/workflows/ci.yml`: GitHub Actions CI/CD 配置

## 测试

### 运行测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest genome/tests/test_rename_ngdc_genome_id.py

# 运行特定测试类
uv run pytest genome/tests/test_rename_ngdc_genome_id.py::TestParseFastaHeader

# 运行特定测试方法
uv run pytest genome/tests/test_rename_ngdc_genome_id.py::TestParseFastaHeader::test_standard_ngdc_format

# 详细输出
uv run pytest -v

# 显示打印输出
uv run pytest -s

# 生成 HTML 覆盖率报告
uv run pytest --cov=genome --cov-report=html
# 报告位置: htmlcov/index.html
```

## 构建和发布

```bash
# 构建包
make build
# 或
uv build

# 构建产物在 dist/ 目录
```

## 环境管理

```bash
# 查看虚拟环境位置
uv venv

# 激活虚拟环境（如需要）
source .venv/bin/activate

# 查看已安装的包
uv pip list

# 更新所有依赖
uv lock --upgrade
uv sync
```

## 故障排除

### 依赖问题
```bash
# 重新同步依赖
uv sync --reinstall

# 清理缓存
uv cache clean
```

### 测试失败
```bash
# 查看详细错误信息
uv run pytest -vv

# 只运行失败的测试
uv run pytest --lf
```

### 代码格式问题
```bash
# 查看需要修改的地方
uv run ruff format --check .

# 自动修复
uv run ruff format .
```
