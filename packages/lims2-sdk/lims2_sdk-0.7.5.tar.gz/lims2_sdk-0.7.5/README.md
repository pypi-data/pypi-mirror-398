# Lims2 SDK

[![Version](https://img.shields.io/badge/version-0.6.4-blue.svg)](https://github.com/huangzhibo/lims2-sdk)
[![Python](https://img.shields.io/badge/python-≥3.9-green.svg)](https://www.python.org/)

生信云平台 Python SDK，提供图表上传和文件存储功能。

## 功能特性

- **图表服务**：支持 Plotly、Cytoscape、图片、PDF 格式上传
- **自定义文件名**：支持指定英文文件名，避免中文图表名在OSS路径中的问题
- **文件去重**：自动检查并跳过已存在的相同文件，避免重复上传
- **缩略图生成**：自动为 Plotly 图表生成静态缩略图（800×600 WebP格式）
- **文件存储**：通过 STS 凭证上传文件到阿里云 OSS，支持断点续传
- **命令行工具**：提供便捷的 CLI 命令
- **精度控制**：使用 decimal 库精确四舍五入，默认保留3位小数，减少 JSON 文件大小（可减少 15-60%）
- **连接优化**：自动重试机制处理网络不稳定问题，适合批量上传场景

## 安装配置

### 从 PyPI 安装
```bash
pip install -U lims2-sdk
```

### 设置环境变量：

```bash
export LIMS2_API_URL="your-api"
export LIMS2_API_TOKEN="your-api-token"
```

## 命令行使用

### 📖 获取帮助信息

```bash
# 查看所有可用命令
lims2 --help

# 查看图表上传帮助
lims2 chart --help
lims2 chart upload --help

# 查看存储服务帮助
lims2 storage --help
lims2 storage upload --help
lims2 storage upload-dir --help

# 查看文件操作帮助
lims2 storage exists --help
lims2 storage info --help
```

### 图表上传
```bash
# 上传图表文件（完整参数示例）
lims2 chart upload plot.json -p proj_001 -n "基因表达分析" -s sample_001 -t heatmap -d "差异表达热图" -c A_vs_B -a Expression_statistics --precision 3
```

### 文件存储
```bash
# 上传单个文件（简化）
lims2 storage upload results.csv -p proj_001

# 上传到指定路径
lims2 storage upload results.csv -p proj_001 --base-path analysis

# 上传目录（简化）
lims2 storage upload-dir output/ -p proj_001

# 上传目录到指定路径
lims2 storage upload-dir output/ -p proj_001 --base-path analysis
```

## Python SDK 使用
** 多个图表上传，推荐使用该方法，可复用链接池 **

### 推荐使用方式（v0.4.1+）

```python
from lims2 import Lims2Client

# 初始化客户端（推荐复用，避免重复创建连接）
client = Lims2Client()

# 批量上传时复用同一个客户端实例
charts = ["plot1.json", "plot2.json", "plot3.json"]
for chart_file in charts:
    client.chart.upload(
        data_source=chart_file,
        project_id="proj_001",
        chart_name=f"图表_{chart_file}",
        analysis_node="Expression_statistics",
        precision=3
    )
```

### 完整参数示例

```python
# 上传图表（完整参数示例）
client.chart.upload(
    data_source="plot.json",        # 图表数据源：字典、文件路径或 Path 对象
    project_id="proj_001",          # 项目 ID（必需）
    chart_name="基因表达分析",        # 图表名称（必需）
    sample_id="sample_001",         # 样本 ID（可选）
    chart_type="heatmap",           # 图表类型（可选）
    description="差异表达基因热图",   # 图表描述（可选）
    contrast="A_vs_B",              # 对比策略（可选）
    analysis_node="Expression_statistics",  # 分析节点名称（可选）
    precision=3,                    # 浮点数精度：0-10位小数（默认3）
    generate_thumbnail=True,        # 是否生成缩略图（默认True）
    file_name="gene_expression_heatmap"  # 自定义文件名（仅字典数据有效，文件上传使用文件本身名称）
)

# 上传文件（最简）
client.storage.upload_file("results.csv", "proj_001")

# 上传文件到指定路径
client.storage.upload_file("results.csv", "proj_001", base_path="analysis")

# 上传目录（最简）
client.storage.upload_directory("output/", "proj_001")

# 上传目录到指定路径
client.storage.upload_directory("output/", "proj_001", base_path="analysis")
```

### 便捷函数（已弃用）

> ⚠️ **弃用警告**: 以下函数在 v0.4.1 中已弃用，将在 v0.5.0 中移除。推荐使用上述 `Lims2Client` 实例方法复用连接池，避免批量上传时的连接问题。

```python
# 不推荐：每次调用都创建新连接
from lims2 import upload_chart_from_file
upload_chart_from_file("图表名", "proj_001", "chart.json")
```

## 智能路径结构

SDK采用智能的OSS路径结构，完美适配生物信息学分析流程：

**路径格式**：`project/[analysis/][contrast/][sample/]filename`

### 使用示例

```python
from lims2 import Lims2Client

client = Lims2Client()
chart_data = {"data": [...], "layout": {...}}

# 1. 质控分析 - 按样本分类
client.chart.upload(
    data_source=chart_data,
    project_id="RNA_Seq_Project",
    analysis_node="FastQC_Analysis",
    sample_id="Sample_001",
    chart_name="quality_metrics"
)
# → RNA_Seq_Project/FastQC_Analysis/Sample_001/

# 2. 差异分析 - 按对比策略分组
client.chart.upload(
    data_source=chart_data,
    project_id="RNA_Seq_Project",
    analysis_node="Differential_Expression",
    contrast="Treatment_vs_Control",
    sample_id="Sample_T1",  # Treatment组样本
    chart_name="volcano_plot"
)
# → RNA_Seq_Project/Differential_Expression/Treatment_vs_Control/Sample_T1/

# 3. 功能分析 - 基于对比结果
client.chart.upload(
    data_source=chart_data,
    project_id="RNA_Seq_Project",
    analysis_node="GO_Enrichment",
    contrast="Treatment_vs_Control",
    chart_name="go_terms"  # 无需指定样本
)
# → RNA_Seq_Project/GO_Enrichment/Treatment_vs_Control/
```

### 路径结构优势

- 🎯 **分析类型优先**：同种分析集中管理，便于批量操作
- 🧬 **对比策略分组**：多样本实验按对比逻辑组织
- 🔧 **完全灵活**：所有层级均可选，适应不同分析场景
- 📊 **逻辑清晰**：符合实际的生物信息学工作流程

## 高级功能

### 自定义文件名

避免中文文件名在OSS路径中的问题：

```python
# 字典数据上传
result = client.chart.upload(
    data_source=chart_data,
    project_id="proj_001",
    chart_name="中文图表名称",     # 用于显示
    filename="english_chart_name"  # 用于OSS路径
)

# JSON文件上传
result = client.chart.upload(
    data_source="中文图表.json",
    project_id="proj_001",
    chart_name="图表显示名称",
    filename="english_chart"       # 自定义OSS文件名
)
```

### 支持的数据格式

**图表格式**：
- **Plotly**: 包含 `data` 和 `layout` 字段的字典（支持自动缩略图）
- **Cytoscape**: 包含 `elements` 或 `nodes`+`edges` 字段的字典（使用预设缩略图）
- **图片**: PNG, JPG, JPEG, SVG, PDF

**文件存储**：
- 支持任意格式文件上传
- 大文件（>10MB）自动断点续传
- 提供进度回调支持

### 缩略图功能

```python
# Plotly图表 - 自动生成缩略图
client.chart.upload(
    data_source=plotly_data,
    project_id="proj_001",
    chart_name="表达分析图"
    # generate_thumbnail=True  # 默认启用
)

# Cytoscape网络图 - 使用预设缩略图
client.chart.upload(
    data_source=cytoscape_data,
    project_id="proj_001",
    chart_name="网络图",
    chart_type="network"
)

# 禁用缩略图
client.chart.upload(
    data_source=data,
    project_id="proj_001",
    chart_name="图表",
    generate_thumbnail=False
)
```

## 环境配置

通过环境变量进行配置：

```bash
# API配置
export LIMS2_API_URL="你的API地址"
export LIMS2_API_TOKEN="你的API Token"

# 网络配置
export LIMS2_CONNECTION_TIMEOUT=30
export LIMS2_READ_TIMEOUT=300
export LIMS2_MAX_RETRIES=3

# STS 凭证优化配置（可选，使用独立的 STS Agent 服务）
export LIMS2_STS_AGENT_URL="http://172.16.70.100:8101/aliyun_sts"

# 缩略图配置
export LIMS2_THUMBNAIL_WIDTH=800
export LIMS2_THUMBNAIL_HEIGHT=600
export LIMS2_THUMBNAIL_FORMAT=webp
```

## 日志配置

SDK使用标准的Python logging模块，默认不输出任何日志。你可以根据需要启用日志：

### 启用所有日志
```python
import logging

# 启用INFO级别日志（显示重要操作信息）
logging.basicConfig(level=logging.INFO)

from lims2 import Lims2Client
client = Lims2Client()
# 输出：文件已存在且大小相同，跳过OSS上传: biochart/xxx/xxx.json
# 输出：缩略图已生成: https://image.lims2.com/xxx
```

### 启用DEBUG级别日志
```python
import logging

# 启用DEBUG级别日志（显示详细调试信息）
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from lims2 import Lims2Client
client = Lims2Client()
# 输出：2024-09-24 15:30:45 - lims2.config - DEBUG - API地址: https://api.lims2.com (来源: 环境变量)
# 输出：2024-09-24 15:30:46 - lims2.chart - DEBUG - 开始生成Plotly缩略图...
```

### 只启用lims2的日志
```python
import logging

# 只为lims2模块启用日志
lims2_logger = logging.getLogger('lims2')
lims2_logger.setLevel(logging.INFO)
lims2_logger.addHandler(logging.StreamHandler())

from lims2 import Lims2Client
client = Lims2Client()
```

### 命令行工具日志

命令行工具（`lims2`）默认启用INFO级别日志，显示重要操作信息。可以通过环境变量控制：

```bash
# 默认INFO级别（显示重要操作）
lims2 chart upload plot.json -p proj_001
# 输出：缩略图已生成: https://image.lims2.com/xxx

# 启用DEBUG级别（显示详细信息）
export LIMS2_LOG_LEVEL=DEBUG
lims2 chart upload plot.json -p proj_001

# 只显示错误（静默模式）
export LIMS2_LOG_LEVEL=ERROR
lims2 chart upload plot.json -p proj_001

# 完全静默
export LIMS2_LOG_LEVEL=CRITICAL
lims2 chart upload plot.json -p proj_001
```

### 日志级别说明

- **DEBUG**: 配置信息、缩略图生成过程等调试信息
- **INFO**: 文件跳过上传、缩略图生成结果等重要操作反馈（CLI默认级别）
- **WARNING**: 降级处理、异常情况
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

## 许可证

MIT License
