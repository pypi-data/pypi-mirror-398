# 知识库 API - 数据集

本文档基于控制台页面 /datasets?category=api 生成。

## 创建空知识库
**请求方法**: POST
**请求 URL**: /datasets
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| name | string | 知识库名称（必填） |
| description | string | 知识库描述（选填） |
| indexing_technique | string | 索引模式（选填，建议填写）<br>high_quality 高质量<br>economy 经济 |
| permission | string | 权限（选填，默认 only_me）<br>only_me 仅自己<br>all_team_members 所有团队成员<br>partial_members 部分团队成员 |
| provider | string | Provider（选填，默认 vendor）<br>vendor 上传文件<br>external 外部知识库 |
| external_knowledge_api_id | str | 外部知识库 API_ID（选填） |
| external_knowledge_id | str | 外部知识库 ID（选填） |
| embedding_model | str | Embedding 模型名称 |
| embedding_model_provider | str | Embedding 模型供应商 |
| retrieval_model | object | 检索模式<br>search_method (string) 检索方法<br>hybrid_search 混合检索<br>semantic_search 语义检索<br>full_text_search 全文检索<br>reranking_enable (bool) 是否开启 rerank<br>reranking_model (object) Rerank 模型配置<br>reranking_provider_name (string) Rerank 模型的提供商<br>reranking_model_name (string) Rerank 模型的名称<br>top_k (int) 召回条数<br>score_threshold_enabled (bool) 是否开启召回分数限制<br>score_threshold (float) 召回分数限制 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"name": "name", "permission": "only_me"}'
```
### Response
```json
{
  "id": "",
  "name": "name",
  "description": null,
  "provider": "vendor",
  "permission": "only_me",
  "data_source_type": null,
  "indexing_technique": null,
  "app_count": 0,
  "document_count": 0,
  "word_count": 0,
  "created_by": "",
  "created_at": 1695636173,
  "updated_by": "",
  "updated_at": 1695636173,
  "embedding_model": null,
  "embedding_model_provider": null,
  "embedding_available": null
}
```

## 知识库列表
**请求方法**: GET
**请求 URL**: /datasets
### Query

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| keyword | string | 搜索关键词，可选 |
| tag_ids | array[string] | 标签 ID 列表，可选 |
| page | integer | 页码，可选，默认为 1 |
| limit | string | 返回条数，可选，默认 20，范围 1-100 |
| include_all | boolean | 是否包含所有数据集（仅对所有者生效），可选，默认为 false |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets?page=1&limit=20' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "data": [
    {
      "id": "",
      "name": "知识库名称",
      "description": "描述信息",
      "permission": "only_me",
      "data_source_type": "upload_file",
      "indexing_technique": "",
      "app_count": 2,
      "document_count": 10,
      "word_count": 1200,
      "created_by": "",
      "created_at": "",
      "updated_by": "",
      "updated_at": ""
    },
    ...
  ],
  "has_more": true,
  "limit": 20,
  "total": 50,
  "page": 1
}
```

## 查看知识库详情
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "id": "eaedb485-95ac-4ffd-ab1e-18da6d676a2f",
  "name": "Test Knowledge Base",
  "description": "",
  "provider": "vendor",
  "permission": "only_me",
  "data_source_type": null,
  "indexing_technique": null,
  "app_count": 0,
  "document_count": 0,
  "word_count": 0,
  "created_by": "e99a1635-f725-4951-a99a-1daaaa76cfc6",
  "created_at": 1735620612,
  "updated_by": "e99a1635-f725-4951-a99a-1daaaa76cfc6",
  "updated_at": 1735620612,
  "embedding_model": null,
  "embedding_model_provider": null,
  "embedding_available": true,
  "retrieval_model_dict": {
    "search_method": "semantic_search",
    "reranking_enable": false,
    "reranking_mode": null,
    "reranking_model": {
      "reranking_provider_name": "",
      "reranking_model_name": ""
    },
    "weights": null,
    "top_k": 2,
    "score_threshold_enabled": false,
    "score_threshold": null
  },
  "tags": [],
  "doc_form": null,
  "external_knowledge_info": {
    "external_knowledge_id": null,
    "external_knowledge_api_id": null,
    "external_knowledge_api_name": null,
    "external_knowledge_api_endpoint": null
  },
  "external_retrieval_model": {
    "top_k": 2,
    "score_threshold": 0.0,
    "score_threshold_enabled": null
  }
}
```

## 修改知识库详情
**请求方法**: PATCH
**请求 URL**: /datasets/{dataset_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| indexing_technique | string | 索引模式（选填，建议填写）<br>high_quality 高质量<br>economy 经济 |
| permission | string | 权限（选填，默认 only_me）<br>only_me 仅自己<br>all_team_members 所有团队成员<br>partial_members 部分团队成员 |
| embedding_model_provider | string | 嵌入模型提供商（选填）, 必须先在系统内设定好接入的模型，对应的是 provider 字段 |
| embedding_model | string | 嵌入模型（选填） |
| retrieval_model | object | 检索参数（选填，如不填，按照默认方式召回）<br>search_method (text) 检索方法：以下四个关键字之一，必填<br>keyword_search 关键字检索<br>semantic_search 语义检索<br>full_text_search 全文检索<br>hybrid_search 混合检索<br>reranking_enable (bool) 是否启用 Reranking，非必填，如果检索模式为 semantic_search 模式或者 hybrid_search 则传值<br>reranking_mode (object) Rerank 模型配置，非必填，如果启用了 reranking 则传值<br>reranking_provider_name (string) Rerank 模型提供商<br>reranking_model_name (string) Rerank 模型名称<br>weights (float) 混合检索模式下语意检索的权重设置<br>top_k (integer) 返回结果数量，非必填<br>score_threshold_enabled (bool) 是否开启 score 阈值<br>score_threshold (float) Score 阈值 |
| partial_member_list | array | 部分团队成员 ID 列表（选填） |

### Request (curl)
```bash
curl --location --request PATCH 'http://localhost/v1/datasets/{dataset_id}' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{
      "name": "Test Knowledge Base",
      "indexing_technique": "high_quality",
      "permission": "only_me",
      "embedding_model_provider": "zhipuai",
      "embedding_model": "embedding-3",
      "retrieval_model": {
        "search_method": "keyword_search",
        "reranking_enable": false,
        "reranking_mode": null,
        "reranking_model": {
            "reranking_provider_name": "",
            "reranking_model_name": ""
        },
        "weights": null,
        "top_k": 1,
        "score_threshold_enabled": false,
        "score_threshold": null
      },
      "partial_member_list": []
    }'
```
### Response
```json
{
  "id": "eaedb485-95ac-4ffd-ab1e-18da6d676a2f",
  "name": "Test Knowledge Base",
  "description": "",
  "provider": "vendor",
  "permission": "only_me",
  "data_source_type": null,
  "indexing_technique": "high_quality",
  "app_count": 0,
  "document_count": 0,
  "word_count": 0,
  "created_by": "e99a1635-f725-4951-a99a-1daaaa76cfc6",
  "created_at": 1735620612,
  "updated_by": "e99a1635-f725-4951-a99a-1daaaa76cfc6",
  "updated_at": 1735622679,
  "embedding_model": "embedding-3",
  "embedding_model_provider": "zhipuai",
  "embedding_available": null,
  "retrieval_model_dict": {
    "search_method": "semantic_search",
    "reranking_enable": false,
    "reranking_mode": null,
    "reranking_model": {
      "reranking_provider_name": "",
      "reranking_model_name": ""
    },
    "weights": null,
    "top_k": 2,
    "score_threshold_enabled": false,
    "score_threshold": null
  },
  "tags": [],
  "doc_form": null,
  "external_knowledge_info": {
    "external_knowledge_id": null,
    "external_knowledge_api_id": null,
    "external_knowledge_api_name": null,
    "external_knowledge_api_endpoint": null
  },
  "external_retrieval_model": {
    "top_k": 2,
    "score_threshold": 0.0,
    "score_threshold_enabled": null
  },
  "partial_member_list": []
}
```

## 删除知识库
**请求方法**: DELETE
**请求 URL**: /datasets/{dataset_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request (curl)
```bash
curl --location --request DELETE 'http://localhost/v1/datasets/{dataset_id}' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```text
204 No Content
```

## 检索知识库
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/retrieve
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| query | string | 检索关键词 |
| retrieval_model | object | 检索参数（选填，如不填，按照默认方式召回）<br>search_method (text) 检索方法：以下四个关键字之一，必填<br>keyword_search 关键字检索<br>semantic_search 语义检索<br>full_text_search 全文检索<br>hybrid_search 混合检索<br>reranking_enable (bool) 是否启用 Reranking，非必填，如果检索模式为 semantic_search 模式或者 hybrid_search 则传值<br>reranking_mode (object) Rerank 模型配置，非必填，如果启用了 reranking 则传值<br>reranking_provider_name (string) Rerank 模型提供商<br>reranking_model_name (string) Rerank 模型名称<br>weights (float) 混合检索模式下语意检索的权重设置<br>top_k (integer) 返回结果数量，非必填<br>score_threshold_enabled (bool) 是否开启 score 阈值<br>score_threshold (float) Score 阈值<br>metadata_filtering_conditions (object) 元数据过滤条件<br>logical_operator (string) 逻辑运算符: and \| or<br>conditions (array[object]) 条件列表<br>name (string) 元数据字段名<br>comparison_operator (string) 比较运算符，可选值:<br>字符串比较:<br>contains: 包含<br>not contains: 不包含<br>start with: 以...开头<br>end with: 以...结尾<br>is: 等于<br>is not: 不等于<br>empty: 为空<br>not empty: 不为空<br>数值比较:<br>=: 等于<br>≠: 不等于<br>>: 大于<br>< : 小于<br>≥: 大于等于<br>≤: 小于等于<br>时间比较:<br>before: 早于<br>after: 晚于<br>value (string\|number\|null) 比较值 |
| external_retrieval_model | object | 未启用字段 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/retrieve' \
--header 'Authorization: Bearer {api_key}'\
--header 'Content-Type: application/json'\
--data-raw '{
  "query": "test",
  "retrieval_model": {
      "search_method": "keyword_search",
      "reranking_enable": false,
      "reranking_mode": null,
      "reranking_model": {
          "reranking_provider_name": "",
          "reranking_model_name": ""
      },
      "weights": null,
      "top_k": 1,
      "score_threshold_enabled": false,
      "score_threshold": null,
      "metadata_filtering_conditions": {
          "logical_operator": "and",
          "conditions": [
              {
                  "name": "document_name",
                  "comparison_operator": "contains",
                  "value": "test"
              }
          ]
      }
  }
}'
```
### Response
```json
{
  "query": {
    "content": "test"
  },
  "records": [
    {
      "segment": {
        "id": "7fa6f24f-8679-48b3-bc9d-bdf28d73f218",
        "position": 1,
        "document_id": "a8c6c36f-9f5d-4d7a-8472-f5d7b75d71d2",
        "content": "Operation guide",
        "answer": null,
        "word_count": 847,
        "tokens": 280,
        "keywords": ["install", "java", "base", "scripts", "jdk", "manual", "internal", "opens", "add", "vmoptions"],
        "index_node_id": "39dd8443-d960-45a8-bb46-7275ad7fbc8e",
        "index_node_hash": "0189157697b3c6a418ccf8264a09699f25858975578f3467c76d6bfc94df1d73",
        "hit_count": 0,
        "enabled": true,
        "disabled_at": null,
        "disabled_by": null,
        "status": "completed",
        "created_by": "dbcb1ab5-90c8-41a7-8b78-73b235eb6f6f",
        "created_at": 1728734540,
        "indexing_at": 1728734552,
        "completed_at": 1728734584,
        "error": null,
        "stopped_at": null,
        "document": {
          "id": "a8c6c36f-9f5d-4d7a-8472-f5d7b75d71d2",
          "data_source_type": "upload_file",
          "name": "readme.txt"
        }
      },
      "score": 3.730463140527718e-5,
      "tsne_position": null
    }
  ]
}
```
