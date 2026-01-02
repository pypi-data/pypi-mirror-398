# 知识库 API - 文档分段

本文档基于控制台页面 /datasets?category=api 生成。

## 新增分段
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| segments | object list | content (text) 文本内容/问题内容，必填<br>answer (text) 答案内容，非必填，如果知识库的模式为 Q&A 模式则传值<br>keywords (list) 关键字，非必填 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"segments": [{"content": "1","answer": "1","keywords": ["a"]}]}'
```
### Response
```json
{
  "data": [
    {
      "id": "",
      "position": 1,
      "document_id": "",
      "content": "1",
      "answer": "1",
      "word_count": 25,
      "tokens": 0,
      "keywords": ["a"],
      "index_node_id": "",
      "index_node_hash": "",
      "hit_count": 0,
      "enabled": true,
      "disabled_at": null,
      "disabled_by": null,
      "status": "completed",
      "created_by": "",
      "created_at": 1695312007,
      "indexing_at": 1695312007,
      "completed_at": 1695312007,
      "error": null,
      "stopped_at": null
    }
  ],
  "doc_form": "text_model"
}
```

## 查询文档分段
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |

### Query

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| keyword | string | 搜索关键词，可选 |
| status | string | 搜索状态，completed |
| page | string | 页码，可选 |
| limit | string | 返回条数，可选，默认 20，范围 1-100 |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'
```
### Response
```json
{
  "data": [
    {
      "id": "",
      "position": 1,
      "document_id": "",
      "content": "1",
      "answer": "1",
      "word_count": 25,
      "tokens": 0,
      "keywords": ["a"],
      "index_node_id": "",
      "index_node_hash": "",
      "hit_count": 0,
      "enabled": true,
      "disabled_at": null,
      "disabled_by": null,
      "status": "completed",
      "created_by": "",
      "created_at": 1695312007,
      "indexing_at": 1695312007,
      "completed_at": 1695312007,
      "error": null,
      "stopped_at": null
    }
  ],
  "doc_form": "text_model",
  "has_more": false,
  "limit": 20,
  "total": 9,
  "page": 1
}
```

## 删除文档分段
**请求方法**: DELETE
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |
| segment_id | string | 文档分段 ID |

### Request (curl)
```bash
curl --location --request DELETE 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'
```
### Response
```text
204 No Content
```

## 查看文档分段详情
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}
**说明**: 查看指定知识库中特定文档的分段详情
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |
| segment_id | string | 分段 ID |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "data": {
    "id": "分段唯一ID",
    "position": 2,
    "document_id": "所属文档ID",
    "content": "分段内容文本",
    "sign_content": "签名内容文本",
    "answer": "答案内容(如果有)",
    "word_count": 470,
    "tokens": 382,
    "keywords": ["关键词1", "关键词2"],
    "index_node_id": "索引节点ID",
    "index_node_hash": "索引节点哈希值",
    "hit_count": 0,
    "enabled": true,
    "status": "completed",
    "created_by": "创建者ID",
    "created_at": 创建时间戳,
    "updated_at": 更新时间戳,
    "indexing_at": 索引时间戳,
    "completed_at": 完成时间戳,
    "error": null,
    "child_chunks": []
  },
  "doc_form": "text_model"
}
```

## 更新文档分段
**说明**: POST Name dataset_id Type string Description 知识库 ID Name document_id Type string Description 文档 ID Name segment_id Type string Description 文档分段 ID
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| segment | object | content (text) 文本内容/问题内容，必填<br>answer (text) 答案内容，非必填，如果知识库的模式为 Q&A 模式则传值<br>keywords (list) 关键字，非必填<br>enabled (bool) false/true，非必填<br>regenerate_child_chunks (bool) 是否重新生成子分段，非必填 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'\
--data-raw '{"segment": {"content": "1","answer": "1", "keywords": ["a"], "enabled": false}}'
```
### Response
```json
{
  "data": {
    "id": "",
    "position": 1,
    "document_id": "",
    "content": "1",
    "answer": "1",
    "word_count": 25,
    "tokens": 0,
    "keywords": ["a"],
    "index_node_id": "",
    "index_node_hash": "",
    "hit_count": 0,
    "enabled": true,
    "disabled_at": null,
    "disabled_by": null,
    "status": "completed",
    "created_by": "",
    "created_at": 1695312007,
    "indexing_at": 1695312007,
    "completed_at": 1695312007,
    "error": null,
    "stopped_at": null
  },
  "doc_form": "text_model"
}
```

## 新增文档子分段
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |
| segment_id | string | 分段 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| content | string | 子分段内容 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"content": "子分段内容"}'
```
### Response
```json
{
  "data": {
    "id": "",
    "segment_id": "",
    "content": "子分段内容",
    "word_count": 25,
    "tokens": 0,
    "index_node_id": "",
    "index_node_hash": "",
    "status": "completed",
    "created_by": "",
    "created_at": 1695312007,
    "indexing_at": 1695312007,
    "completed_at": 1695312007,
    "error": null,
    "stopped_at": null
  }
}
```

## 查询文档子分段
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |
| segment_id | string | 分段 ID |

### Query

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| keyword | string | 搜索关键词（选填） |
| page | integer | 页码（选填，默认 1） |
| limit | integer | 每页数量（选填，默认 20，最大 100） |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks?page=1&limit=20' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "data": [
    {
      "id": "",
      "segment_id": "",
      "content": "子分段内容",
      "word_count": 25,
      "tokens": 0,
      "index_node_id": "",
      "index_node_hash": "",
      "status": "completed",
      "created_by": "",
      "created_at": 1695312007,
      "indexing_at": 1695312007,
      "completed_at": 1695312007,
      "error": null,
      "stopped_at": null
    }
  ],
  "total": 1,
  "total_pages": 1,
  "page": 1,
  "limit": 20
}
```

## 删除文档子分段
**请求方法**: DELETE
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |
| segment_id | string | 分段 ID |
| child_chunk_id | string | 子分段 ID |

### Request (curl)
```bash
curl --location --request DELETE 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```text
204 No Content
```

## 更新文档子分段
**请求方法**: PATCH
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |
| segment_id | string | 分段 ID |
| child_chunk_id | string | 子分段 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| content | string | 子分段内容 |

### Request (curl)
```bash
curl --location --request PATCH 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"content": "更新的子分段内容"}'
```
### Response
```json
{
  "data": {
    "id": "",
    "segment_id": "",
    "content": "更新的子分段内容",
    "word_count": 25,
    "tokens": 0,
    "index_node_id": "",
    "index_node_hash": "",
    "status": "completed",
    "created_by": "",
    "created_at": 1695312007,
    "indexing_at": 1695312007,
    "completed_at": 1695312007,
    "error": null,
    "stopped_at": null
  }
}
```
