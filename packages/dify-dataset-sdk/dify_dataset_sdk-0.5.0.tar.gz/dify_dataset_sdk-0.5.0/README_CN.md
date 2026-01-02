# Dify 知识库 SDK

一个用于与 Dify 知识库 API 交互的综合 Python SDK。此 SDK 提供了通过 Dify REST API 管理数据集（知识库）、文档、片段和元数据的易用方法。

## 功能特性

- 📚 **完整的 API 覆盖**：支持所有 Dify 知识库 API 端点
- 🔐 **身份验证**：基于 API 密钥的安全身份验证
- 📄 **文档管理**：从文本或文件创建、更新、删除文档
- 🗂️ **数据集操作**：知识库的完整 CRUD 操作
- ✂️ **片段控制**：精细控制文档片段（块）的管理
- 🏷️ **知识标签**：创建和管理知识标签，实现数据集组织
- 📊 **元数据支持**：创建和管理自定义元数据字段
- 🔍 **高级检索**：多种搜索方法（语义、全文、混合搜索）
- 🔗 **批量操作**：文档和元数据的高效批量处理
- 🌐 **HTTP 客户端**：基于 httpx 构建，提供可靠快速的 HTTP 通信
- ⚠️ **错误处理**：使用自定义异常进行全面的错误处理
- 📈 **进度监控**：详细状态跟踪文档索引进度
- 🛡️ **重试机制**：内置重试逻辑提供网络弹性
- 🔒 **类型安全**：使用 Pydantic 模型提供完整类型提示
- 📱 **丰富示例**：覆盖所有用例的综合示例集合

## 安装

```bash
pip install dify-dataset-sdk
```

## 快速开始

```python
from dify_dataset_sdk import DifyDatasetClient

# 初始化客户端
client = DifyDatasetClient(api_key="your-api-key-here")

# 创建新的数据集（知识库）
dataset = client.create_dataset(
    name="我的知识库",
    permission="only_me"
)

# 从文本创建文档
doc_response = client.create_document_by_text(
    dataset_id=dataset.id,
    name="示例文档",
    text="这是知识库的示例文档。",
    indexing_technique="high_quality"
)

# 列出所有文档
documents = client.list_documents(dataset.id)
print(f"文档总数: {documents.total}")

# 关闭客户端
client.close()
```

## 配置

### API 密钥

从 Dify 知识库 API 页面获取您的 API 密钥：

1. 进入您的 Dify 知识库
2. 在左侧边栏导航到 **API** 部分
3. 从 **API 密钥** 部分生成或复制您的 API 密钥

### 基础 URL

默认情况下，SDK 使用 `https://api.dify.ai` 作为基础 URL。您可以自定义：

```python
client = DifyDatasetClient(
    api_key="your-api-key",
    base_url="https://your-custom-dify-instance.com",
    timeout=60.0  # 自定义超时时间（秒）
)
```

## 核心功能

### 数据集管理

```python
# 创建数据集
dataset = client.create_dataset(
    name="技术文档",
    permission="only_me",
    description="内部技术文档"
)

# 分页列出数据集
datasets = client.list_datasets(page=1, limit=20)

# 删除数据集
client.delete_dataset(dataset_id)
```

### 文档操作

#### 从文本创建

```python
# 从文本创建文档
doc_response = client.create_document_by_text(
    dataset_id=dataset_id,
    name="API 文档",
    text="完整的 API 文档内容...",
    indexing_technique="high_quality",
    process_rule_mode="automatic"
)
```

#### 从文件创建

```python
# 从文件创建文档
doc_response = client.create_document_by_file(
    dataset_id=dataset_id,
    file_path="./documentation.pdf",
    indexing_technique="high_quality"
)
```

#### 自定义处理规则

```python
# 自定义处理配置
process_rule_config = {
    "rules": {
        "pre_processing_rules": [
            {"id": "remove_extra_spaces", "enabled": True},
            {"id": "remove_urls_emails", "enabled": True}
        ],
        "segmentation": {
            "separator": "###",
            "max_tokens": 500
        }
    }
}

doc_response = client.create_document_by_file(
    dataset_id=dataset_id,
    file_path="document.txt",
    process_rule_mode="custom",
    process_rule_config=process_rule_config
)
```

### 片段管理

```python
# 创建片段
segments_data = [
    {
        "content": "第一个片段内容",
        "answer": "第一个片段的答案",
        "keywords": ["关键词1", "关键词2"]
    },
    {
        "content": "第二个片段内容",
        "answer": "第二个片段的答案",
        "keywords": ["关键词3", "关键词4"]
    }
]

segments = client.create_segments(dataset_id, document_id, segments_data)

# 列出片段
segments = client.list_segments(dataset_id, document_id)

# 更新片段
client.update_segment(
    dataset_id=dataset_id,
    document_id=document_id,
    segment_id=segment_id,
    segment_data={
        "content": "更新的内容",
        "keywords": ["更新", "关键词"],
        "enabled": True
    }
)

# 删除片段
client.delete_segment(dataset_id, document_id, segment_id)
```

### 知识标签管理 (client.tags)

```python
# 创建知识标签
tag = client.tags.create(name="技术文档")
dept_tag = client.tags.create(name="工程部门")

# 将数据集绑定到标签
client.tags.bind_to_dataset(dataset_id, [tag.id, dept_tag.id])

# 列出所有知识标签
tags = client.tags.list()

# 获取特定数据集的标签
dataset_tags = client.tags.get_dataset_tags(dataset_id)

# 按标签过滤数据集
filtered_datasets = client.list_datasets(tag_ids=[tag.id])
```

### 元数据管理 (client.metadata)

```python
# 创建元数据字段
category_field = client.metadata.create(
    dataset_id=dataset_id,
    field_type="string",
    name="category"
)

priority_field = client.metadata.create(
    dataset_id=dataset_id,
    field_type="number",
    name="priority"
)

# 更新文档元数据
metadata_operations = [
    {
        "document_id": document_id,
        "metadata_list": [
            {
                "id": category_field.id,
                "value": "technical",
                "name": "category"
            },
            {
                "id": priority_field.id,
                "value": "5",
                "name": "priority"
            }
        ]
    }
]

client.metadata.update_document_metadata(dataset_id, metadata_operations)
```

### 高级检索

```python
# 语义搜索
results = client.retrieve(
    dataset_id=dataset_id,
    query="如何实现身份验证？",
    retrieval_config={
        "search_method": "semantic_search",
        "top_k": 5,
        "score_threshold": 0.7
    }
)

# 混合搜索（结合语义和全文搜索）
results = client.retrieve(
    dataset_id=dataset_id,
    query="API 文档",
    retrieval_config={
        "search_method": "hybrid_search",
        "top_k": 10,
        "rerank_model": {
            "model": "rerank-multilingual-v2.0",
            "mode": "reranking_model"
        }
    }
)

# 全文搜索
results = client.retrieve(
    dataset_id=dataset_id,
    query="数据库配置",
    retrieval_config={"search_method": "full_text_search", "top_k": 5}
)
```

### 进度监控

```python
# 监控文档索引进度
status = client.get_document_indexing_status(dataset_id, batch_id)

if status.data:
    indexing_info = status.data[0]
    print(f"状态: {indexing_info.indexing_status}")
    print(f"进度: {indexing_info.completed_segments}/{indexing_info.total_segments}")
```

## 错误处理

SDK 提供了具有特定异常类型的全面错误处理：

```python
from dify_dataset_sdk.exceptions import (
    DifyAPIError,
    DifyAuthenticationError,
    DifyValidationError,
    DifyNotFoundError,
    DifyConflictError,
    DifyServerError,
    DifyConnectionError,
    DifyTimeoutError
)

try:
    dataset = client.create_dataset(name="测试数据集")
except DifyAuthenticationError:
    print("无效的 API 密钥")
except DifyValidationError as e:
    print(f"验证错误: {e}")
except DifyConflictError as e:
    print(f"冲突: {e}")  # 例如，重复的数据集名称
except DifyAPIError as e:
    print(f"API 错误: {e}")
    print(f"状态码: {e.status_code}")
    print(f"错误码: {e.error_code}")
```

## 高级用法

对于更高级的场景，请查看 [examples](./examples/) 目录：

- [基础用法](./examples/basic_usage.py) - 简单操作和入门
- [高级用法](./examples/advanced_usage.py) - 复杂工作流和自定义处理
- [知识标签管理](./examples/knowledge_tag_management.py) - 基于标签的数据集组织
- [批量文档处理](./examples/batch_document_processing.py) - 并行处理和批量操作
- [高级检索分析](./examples/advanced_retrieval_analysis.py) - 检索方法对比和分析
- [错误处理和监控](./examples/error_handling_and_monitoring.py) - 生产级错误处理和监控

### 主要高级功能

#### 批量处理

使用并行操作高效处理多个文档：

```python
from concurrent.futures import ThreadPoolExecutor

def upload_document(file_path):
    return client.create_document_by_file(
        dataset_id=dataset_id,
        file_path=file_path,
        indexing_technique="high_quality"
    )

# 并行文档上传
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(upload_document, file) for file in file_list]
    results = [future.result() for future in futures]
```

#### 带重试的错误处理

实现具有自动重试的健壮错误处理：

```python
from dify_dataset_sdk.exceptions import DifyTimeoutError, DifyConnectionError
import time

def safe_operation_with_retry(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except (DifyTimeoutError, DifyConnectionError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                time.sleep(wait_time)
                continue
            raise e
```

#### 健康监控

监控 SDK 性能和 API 健康状态：

```python
class SDKMonitor:
    def __init__(self, client):
        self.client = client
        self.metrics = {"requests": 0, "errors": 0, "avg_response_time": 0}

    def health_check(self):
        try:
            start_time = time.time()
            self.client.list_datasets(limit=1)
            response_time = time.time() - start_time
            return {"status": "healthy", "response_time": response_time}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

## API 参考

### 客户端配置

```python
DifyDatasetClient(
    api_key: str,           # 必需：您的 Dify API 密钥
    base_url: str,          # 可选：API 基础 URL（默认："https://api.dify.ai"）
    timeout: float          # 可选：请求超时时间秒数（默认：30.0）
)
```

### 支持的文件类型

SDK 支持上传以下文件类型：

- `txt` - 纯文本文件
- `md`, `markdown` - Markdown 文件
- `pdf` - PDF 文档
- `html` - HTML 文件
- `xlsx` - Excel 电子表格
- `docx` - Word 文档
- `csv` - CSV 文件

### 速率限制

请遵守 Dify 的 API 速率限制。SDK 包含对速率限制响应的自动错误处理。

## 开发

### 设置

```bash
# 克隆仓库
git clone https://github.com/LeekJay/dify-dataset-sdk.git
cd dify-dataset-sdk

# 安装依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
python tests/test_all_39_apis.py

# 运行详细输出
pytest -v
```

### 代码格式化

```bash
# 格式化代码
ruff format dify_dataset_sdk/

# 检查并修复问题
ruff check --fix dify_dataset_sdk/

# 类型检查
mypy dify_dataset_sdk/
```

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

此项目根据 MIT 许可证授权 - 有关详细信息，请参阅 [LICENSE](LICENSE) 文件。

## 支持

- 📖 [Dify 文档](https://docs.dify.ai/)
- 🐛 [问题跟踪器](https://github.com/LeekJay/dify-dataset-sdk/issues)
- 💬 [社区讨论](https://github.com/dify/dify/discussions)
- 📋 [示例文档](./examples/README.md)

## 更新日志

### v0.5.0

- **破坏性变更**：`tags` 与 `metadata` 拆分为独立模块
- **新增模块**：`client.metadata` 专用于元数据相关操作

### v0.4.0

- **重构**：采用模块化架构，按功能拆分客户端
- **新 API**：使用 `DifyDatasetClient` 入口访问各子模块（datasets, documents, segments, tags, metadata, models）
- **改进**：简化方法命名（如 `create_dataset` → `datasets.create`）

### v0.3.0

- **初始发布功能**：
  - 完整的 Dify 知识库 API 支持（39 个端点）
  - 数据集、文档、片段和元数据的完整 CRUD 操作
  - 用于数据集组织的知识标签管理
  - 高级检索方法（语义、全文、混合搜索）
  - 使用自定义异常的全面错误处理
  - 使用 Pydantic 的类型安全模型
  - 多种格式的文件上传支持
  - 进度监控和索引状态跟踪
  - 批量处理功能
  - 重试机制和连接弹性
  - 涵盖所有用例的丰富示例集合
  - 生产级监控和健康检查
  - 多语言文档（英文和中文）
