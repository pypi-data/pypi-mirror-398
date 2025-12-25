# Rename Genome ID

重命名基因组 FASTA 和 GFF 文件中的染色体 ID，支持两种模式：
1. **NGDC 基因组模式**：从 FASTA 头中自动提取 OriSeqID
2. **自定义映射模式**：使用提供的 ID 映射文件

## 安装

```bash
pip install tc-pytools
```

## 功能说明

### 模式 1: NGDC 基因组（自动提取 OriSeqID）

从 FASTA 文件头中提取 OriSeqID，并将其替换为 GWHGECT 格式的 ID。

#### FASTA 头示例

```
>GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804
```

将被转换为：

```
>Chr1A
```

### 模式 2: 自定义映射（提供 ID 映射文件）

使用自定义的 ID 映射文件来重命名任何基因组的染色体 ID。适用于：
- 非 NGDC 基因组
- 需要自定义命名规则的基因组
- Scaffold 到染色体的映射

#### 映射文件格式

制表符分隔的文本文件（TSV），每行一个映射关系：

```
old_id	new_id
scaffold_1	Chr1
scaffold_2	Chr2
GWHGECT00000001.1	Chr1A
```

支持注释行（以 `#` 开头）和空行。

## 使用方法

### 基本用法

```bash
# 模式 1: 使用 NGDC 基因组（自动提取 OriSeqID）
tc-rename-genome-id ngdc -f genome.fasta -o output.fasta

# 模式 2: 使用自定义 ID 映射文件
tc-rename-genome-id custom -f genome.fasta -o output.fasta -m id_map.txt
uv run rename-ngdc-genome-id -f genome.fasta -o output.fasta
```

### 同时处理 FASTA 和 GFF 文件

```bash
# NGDC 模式
tc-rename-genome-id ngdc -f genome.fasta -o output.fasta -g input.gff -og output.gff

# 自定义模式
tc-rename-genome-id custom -f genome.fasta -o output.fasta -m id_map.txt -g input.gff -og output.gff
```

### 查看帮助

```bash
# 主命令帮助
tc-rename-genome-id --help

# NGDC 模式帮助
tc-rename-genome-id ngdc --help

# 自定义模式帮助
tc-rename-genome-id custom --help
```

## 使用示例

### 示例 1: NGDC 基因组（自动提取 OriSeqID）

```bash
# 只处理 FASTA 文件
tc-rename-genome-id ngdc \
    -f GWHGECT00000000.genome.fasta \
    -o genome_renamed.fasta

# 同时处理 FASTA 和 GFF
tc-rename-genome-id ngdc \
    -f GWHGECT00000000.genome.fasta \
    -o genome_renamed.fasta \
    -g GWHGECT00000000.gff \
    -og genome_renamed.gff
```

### 示例 2: 使用自定义 ID 映射文件

首先创建映射文件 `id_map.txt`：

```
# Mapping from scaffold IDs to chromosome IDs
scaffold_1	Chr1
scaffold_2	Chr2
scaffold_3	Chr3
contig_100	ChrUn
```

然后运行命令：

```bash
# 只处理 FASTA
tc-rename-genome-id custom \
    -f genome.fasta \
    -o genome_renamed.fasta \
    -m id_map.txt

# 同时处理 FASTA 和 GFF
tc-rename-genome-id custom \
    -f genome.fasta \
    -o genome_renamed.fasta \
    -g annotations.gff \
    -og annotations_renamed.gff \
    -m id_map.txt
rename-ngdc-genome-id -f input.fasta -o output.fasta -m id_map.txt
```

## 输入文件格式

### FASTA 格式

#### NGDC 基因组格式

标准 FASTA 格式，头部必须包含 `OriSeqID=` 字段：

```
>GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804
ATCGATCGATCGATCG...
>GWHGECT00000002.1      Chromosome 1B   Complete=T      Circular=F      OriSeqID=Chr1B  Len=731628012
GCTAGCTAGCTAGCTA...
```

#### 普通基因组格式（使用自定义映射）

标准 FASTA 格式，ID 为第一个空格前的部分：

```
>scaffold_1 length=1000000
ATCGATCGATCGATCG...
>scaffold_2 length=2000000
GCTAGCTAGCTAGCTA...
```

### ID 映射文件格式

制表符分隔的文本文件（`.txt` 或 `.tsv`）：

```
# 注释行（可选）
old_id	new_id
scaffold_1	Chr1
scaffold_2	Chr2
# 支持 NGDC ID
GWHGECT00000001.1	Chr1A
```

**格式要求**：
- 每行一个映射关系
- 使用制表符（`\t`）分隔
- 支持 `#` 开头的注释行
- 支持空行
- old_id 和 new_id 前后的空格会被自动去除

### GFF 格式

标准 GFF3 格式，第一列为染色体 ID：

```
##gff-version 3
GWHGECT00000001.1	RefSeq	gene	100	200	.	+	.	ID=gene1;Name=GENE1
GWHGECT00000001.1	RefSeq	mRNA	100	200	.	+	.	ID=transcript1;Parent=gene1
```

## 输出文件格式

### 输出 FASTA

简化的 FASTA 头，只保留新的染色体 ID：

```
>Chr1A
ATCGATCGATCGATCG...
>Chr1B
GCTAGCTAGCTAGCTA...
```

### 输出 GFF

染色体 ID 已替换，其他字段保持不变：

```
##gff-version 3
Chr1A	RefSeq	gene	100	200	.	+	.	ID=gene1;Name=GENE1
Chr1A	RefSeq	mRNA	100	200	.	+	.	ID=transcript1;Parent=gene1
```

## 注意事项

1. **NGDC 模式**: FASTA 文件头中必须包含 `OriSeqID=` 字段，否则该序列将保持原样
2. **自定义映射模式**: 需要提供正确格式的映射文件（制表符分隔）
3. **GFF 依赖**: GFF 文件的处理依赖于从 FASTA 文件或映射文件中提取的 ID 映射
4. **文件编码**: 默认使用 UTF-8 编码
5. **内存使用**: ID 映射表会全部加载到内存，但序列数据是流式处理
6. **ID 提取**: FASTA 头的 ID 为第一个空格前的部分（去除开头的 `>`）

## 使用场景

### NGDC 基因组

```bash
# NGDC 下载的基因组通常包含 OriSeqID
uv run rename-ngdc-genome-id \
    -f GWHGECT00000000.genome.fasta \
    -o genome.fasta
```

### 其他基因组（Scaffold 到染色体映射）

```bash
# 创建映射文件
cat > scaffold_to_chr.txt <<EOF
scaffold_1	Chr1
scaffold_2	Chr2
scaffold_3	Chr3
scaffold_4	Chr4
scaffold_5	Chr5
EOF

# 重命名基因组
uv run rename-ngdc-genome-id \
    -f genome.scaffold.fasta \
    -o genome.chr.fasta \
    -m scaffold_to_chr.txt
```

### 混合场景

如果基因组中部分序列有 OriSeqID，部分没有，可以：
1. 先自动提取 OriSeqID 生成映射文件
2. 手动补充缺失的映射关系
3. 使用完整的映射文件进行重命名

## 错误处理

如果 FASTA 头中没有找到 `OriSeqID`，该序列的头部将保持原样，程序会继续处理其他序列。

程序会在标准错误输出中显示处理进度和 ID 映射信息：

```
Building ID mapping from input.fasta...
Found 21 chromosome mappings
  GWHGECT00000001.1 -> Chr1A
  GWHGECT00000002.1 -> Chr1B
  ...
Renaming FASTA file to output.fasta...
Renaming GFF file to output.gff...
Done!
```

## Python API 使用

如果需要在 Python 代码中使用：

```python
from gtf.rename_ngdc_genome_id import (
    build_id_mapping,
    load_id_mapping,
    rename_fasta,
    rename_gff,
)

# 方式 1: 从 FASTA 自动构建 ID 映射（NGDC 基因组）
id_map = build_id_mapping('input.fasta')

# 方式 2: 从映射文件加载 ID 映射
id_map = load_id_mapping('id_map.txt')

# 重命名 FASTA
rename_fasta('input.fasta', 'output.fasta', id_map)

# 重命名 GFF
rename_gff('input.gff', 'output.gff', id_map)
```

## 性能说明

- 处理速度主要取决于文件 I/O
- ID 映射构建：O(n)，n 为序列数量
- FASTA 重命名：O(n)，n 为文件行数
- GFF 重命名：O(m)，m 为 GFF 行数
- 内存占用：ID 映射表 + 当前处理行的大小

对于大型基因组文件，处理速度通常在几秒到几分钟之间。
