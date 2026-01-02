# 知识库 API - 文档

本文档基于控制台页面 /datasets?category=api 生成。

## 通过文本创建文档
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/document/create-by-text
**说明**: 此接口基于已存在知识库，在此知识库的基础上通过文本创建新的文档
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| name | string | 文档名称 |
| text | string | 文档内容 |
| indexing_technique | string | 索引方式<br>high_quality 高质量：使用<br>Embedding 模型进行嵌入，构建为向量数据库索引<br>economy 经济：使用 keyword table index 的倒排索引进行构建 |
| doc_form | string | 索引内容的形式<br>text_model text 文档直接 embedding，经济模式默认为该模式<br>hierarchical_model parent-child 模式<br>qa_model Q&A 模式：为分片文档生成 Q&A 对，然后对问题进行 embedding |
| doc_language | string | 在 Q&A 模式下，指定文档的语言，例如：English、Chinese |
| process_rule | object | 处理规则<br>mode (string) 清洗、分段模式 ，automatic 自动 / custom 自定义 / hierarchical 父子<br>rules (object) 自定义规则（自动模式下，该字段为空）<br>pre_processing_rules (array[object]) 预处理规则<br>id (string) 预处理规则的唯一标识符<br>枚举：<br>remove_extra_spaces 替换连续空格、换行符、制表符<br>remove_urls_emails 删除 URL、电子邮件地址<br>enabled (bool) 是否选中该规则，不传入文档 ID 时代表默认值<br>segmentation (object) 分段规则<br>separator 自定义分段标识符，目前仅允许设置一个分隔符。默认为 \n<br>max_tokens 最大长度（token）默认为 1000<br>parent_mode 父分段的召回模式 full-doc 全文召回 / paragraph 段落召回<br>subchunk_segmentation (object) 子分段规则<br>separator 分段标识符，目前仅允许设置一个分隔符。默认为 \*\*\*<br>max_tokens 最大长度 (token) 需要校验小于父级的长度<br>chunk_overlap 分段重叠指的是在对数据进行分段时，段与段之间存在一定的重叠部分（选填）<br>当知识库未设置任何参数的时候，首次上传需要提供以下参数，未提供则使用默认选项： |
| retrieval_model | object | 检索模式<br>search_method (string) 检索方法<br>hybrid_search 混合检索<br>semantic_search 语义检索<br>full_text_search 全文检索<br>reranking_enable (bool) 是否开启 rerank<br>reranking_mode (String) 混合检索<br>weighted_score 权重设置<br>reranking_model Rerank 模型<br>reranking_model (object) Rerank 模型配置<br>reranking_provider_name (string) Rerank 模型的提供商<br>reranking_model_name (string) Rerank 模型的名称<br>top_k (int) 召回条数<br>score_threshold_enabled (bool)是否开启召回分数限制<br>score_threshold (float) 召回分数限制 |
| embedding_model | string | Embedding 模型名称 |
| embedding_model_provider | string | Embedding 模型供应商 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/document/create-by-text' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"name": "text","text": "text","indexing_technique": "high_quality","process_rule": {"mode": "automatic"}}'
```
### Response
```json
{
  "document": {
    "id": "",
    "position": 1,
    "data_source_type": "upload_file",
    "data_source_info": {
      "upload_file_id": ""
    },
    "dataset_process_rule_id": "",
    "name": "text.txt",
    "created_from": "api",
    "created_by": "",
    "created_at": 1695690280,
    "tokens": 0,
    "indexing_status": "waiting",
    "error": null,
    "enabled": true,
    "disabled_at": null,
    "disabled_by": null,
    "archived": false,
    "display_status": "queuing",
    "word_count": 0,
    "hit_count": 0,
    "doc_form": "text_model"
  },
  "batch": ""
}
```

## 通过文件创建文档
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/document/create-by-file
**说明**: 此接口基于已存在知识库，在此知识库的基础上通过文件创建新的文档
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| data | multipart/form-data json string | original_document_id 源文档 ID（选填）<br>用于重新上传文档或修改文档清洗、分段配置，缺失的信息从源文档复制<br>源文档不可为归档的文档<br>当传入 original_document_id 时，代表文档进行更新操作，process_rule 为可填项目，不填默认使用源文档的分段方式<br>未传入 original_document_id 时，代表文档进行新增操作，process_rule 为必填<br>indexing_technique 索引方式<br>high_quality 高质量：使用 embedding 模型进行嵌入，构建为向量数据库索引<br>economy 经济：使用 keyword table index 的倒排索引进行构建<br>doc_form 索引内容的形式<br>text_model text 文档直接 embedding，经济模式默认为该模式<br>hierarchical_model parent-child 模式<br>qa_model Q&A 模式：为分片文档生成 Q&A 对，然后对问题进行 embedding<br>doc_language 在 Q&A 模式下，指定文档的语言，例如：English、Chinese<br>process_rule 处理规则<br>mode (string) 清洗、分段模式，automatic 自动 / custom 自定义 / hierarchical 父子<br>rules (object) 自定义规则（自动模式下，该字段为空）<br>pre_processing_rules (array[object]) 预处理规则<br>id (string) 预处理规则的唯一标识符<br>枚举：<br>remove_extra_spaces 替换连续空格、换行符、制表符<br>remove_urls_emails 删除 URL、电子邮件地址<br>enabled (bool) 是否选中该规则，不传入文档 ID 时代表默认值<br>segmentation (object) 分段规则<br>separator 自定义分段标识符，目前仅允许设置一个分隔符。默认为 \n<br>max_tokens 最大长度（token）默认为 1000<br>parent_mode 父分段的召回模式 full-doc 全文召回 / paragraph 段落召回<br>subchunk_segmentation (object) 子分段规则<br>separator 分段标识符，目前仅允许设置一个分隔符。默认为 \*\*\*<br>max_tokens 最大长度 (token) 需要校验小于父级的长度<br>chunk_overlap 分段重叠指的是在对数据进行分段时，段与段之间存在一定的重叠部分（选填） |
| file | multipart/form-data | 需要上传的文件。<br>当知识库未设置任何参数的时候，首次上传需要提供以下参数，未提供则使用默认选项： |
| retrieval_model | object | 检索模式<br>search_method (string) 检索方法<br>hybrid_search 混合检索<br>semantic_search 语义检索<br>full_text_search 全文检索<br>reranking_enable (bool) 是否开启 rerank<br>reranking_model (object) Rerank 模型配置<br>reranking_provider_name (string) Rerank 模型的提供商<br>reranking_model_name (string) Rerank 模型的名称<br>top_k (int) 召回条数<br>score_threshold_enabled (bool) 是否开启召回分数限制<br>score_threshold (float) 召回分数限制 |
| embedding_model | string | Embedding 模型名称 |
| embedding_model_provider | string | Embedding 模型供应商 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/document/create-by-file' \
--header 'Authorization: Bearer {api_key}' \
--form 'data="{"indexing_technique":"high_quality","process_rule":{"rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":true},{"id":"remove_urls_emails","enabled":true}],"segmentation":{"separator":"###","max_tokens":500}},"mode":"custom"}}";type=text/plain' \
--form 'file=@"/path/to/file"'
```
### Response
```json
{
  "document": {
    "id": "",
    "position": 1,
    "data_source_type": "upload_file",
    "data_source_info": {
      "upload_file_id": ""
    },
    "dataset_process_rule_id": "",
    "name": "Dify.txt",
    "created_from": "api",
    "created_by": "",
    "created_at": 1695308667,
    "tokens": 0,
    "indexing_status": "waiting",
    "error": null,
    "enabled": true,
    "disabled_at": null,
    "disabled_by": null,
    "archived": false,
    "display_status": "queuing",
    "word_count": 0,
    "hit_count": 0,
    "doc_form": "text_model"
  },
  "batch": ""
}
```

## 通过文本更新文档
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/update-by-text
**说明**: 此接口基于已存在知识库，在此知识库的基础上通过文本更新文档
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| name | string | 文档名称（选填） |
| text | string | 文档内容（选填） |
| process_rule | object | 处理规则（选填）<br>mode (string) 清洗、分段模式 ，automatic 自动 / custom 自定义 / hierarchical 父子<br>rules (object) 自定义规则（自动模式下，该字段为空）<br>pre_processing_rules (array[object]) 预处理规则<br>id (string) 预处理规则的唯一标识符<br>枚举：<br>remove_extra_spaces 替换连续空格、换行符、制表符<br>remove_urls_emails 删除 URL、电子邮件地址<br>enabled (bool) 是否选中该规则，不传入文档 ID 时代表默认值<br>segmentation (object) 分段规则<br>separator 自定义分段标识符，目前仅允许设置一个分隔符。默认为 \n<br>max_tokens 最大长度（token）默认为 1000<br>parent_mode 父分段的召回模式 full-doc 全文召回 / paragraph 段落召回<br>subchunk_segmentation (object) 子分段规则<br>separator 分段标识符，目前仅允许设置一个分隔符。默认为 \*\*\*<br>max_tokens 最大长度 (token) 需要校验小于父级的长度<br>chunk_overlap 分段重叠指的是在对数据进行分段时，段与段之间存在一定的重叠部分（选填） |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/update-by-text' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"name": "name","text": "text"}'
```
### Response
```json
{
  "document": {
    "id": "",
    "position": 1,
    "data_source_type": "upload_file",
    "data_source_info": {
      "upload_file_id": ""
    },
    "dataset_process_rule_id": "",
    "name": "name.txt",
    "created_from": "api",
    "created_by": "",
    "created_at": 1695308667,
    "tokens": 0,
    "indexing_status": "waiting",
    "error": null,
    "enabled": true,
    "disabled_at": null,
    "disabled_by": null,
    "archived": false,
    "display_status": "queuing",
    "word_count": 0,
    "hit_count": 0,
    "doc_form": "text_model"
  },
  "batch": ""
}
```

## 通过文件更新文档
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/update-by-file
**说明**: 此接口基于已存在知识库，在此知识库的基础上通过文件更新文档的操作。
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| name | string | 文档名称（选填） |
| file | multipart/form-data | 需要上传的文件 |
| process_rule | object | 处理规则（选填）<br>mode (string) 清洗、分段模式 ，automatic 自动 / custom 自定义 / hierarchical 父子<br>rules (object) 自定义规则（自动模式下，该字段为空）<br>pre_processing_rules (array[object]) 预处理规则<br>id (string) 预处理规则的唯一标识符<br>枚举：<br>remove_extra_spaces 替换连续空格、换行符、制表符<br>remove_urls_emails 删除 URL、电子邮件地址<br>enabled (bool) 是否选中该规则，不传入文档 ID 时代表默认值<br>segmentation (object) 分段规则<br>separator 自定义分段标识符，目前仅允许设置一个分隔符。默认为 \n<br>max_tokens 最大长度（token）默认为 1000<br>parent_mode 父分段的召回模式 full-doc 全文召回 / paragraph 段落召回<br>subchunk_segmentation (object) 子分段规则<br>separator 分段标识符，目前仅允许设置一个分隔符。默认为 \*\*\*<br>max_tokens 最大长度 (token) 需要校验小于父级的长度<br>chunk_overlap 分段重叠指的是在对数据进行分段时，段与段之间存在一定的重叠部分（选填） |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/update-by-file' \
--header 'Authorization: Bearer {api_key}' \
--form 'data="{"name":"Dify","indexing_technique":"high_quality","process_rule":{"rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":true},{"id":"remove_urls_emails","enabled":true}],"segmentation":{"separator":"###","max_tokens":500}},"mode":"custom"}}";type=text/plain' \
--form 'file=@"/path/to/file"'
```
### Response
```json
{
  "document": {
    "id": "",
    "position": 1,
    "data_source_type": "upload_file",
    "data_source_info": {
      "upload_file_id": ""
    },
    "dataset_process_rule_id": "",
    "name": "Dify.txt",
    "created_from": "api",
    "created_by": "",
    "created_at": 1695308667,
    "tokens": 0,
    "indexing_status": "waiting",
    "error": null,
    "enabled": true,
    "disabled_at": null,
    "disabled_by": null,
    "archived": false,
    "display_status": "queuing",
    "word_count": 0,
    "hit_count": 0,
    "doc_form": "text_model"
  },
  "batch": "20230921150427533684"
}
```

## 获取文档嵌入状态（进度）
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents/{batch}/indexing-status
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| batch | string | 上传文档的批次号 |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/documents/{batch}/indexing-status' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "data": [
    {
      "id": "",
      "indexing_status": "indexing",
      "processing_started_at": 1681623462.0,
      "parsing_completed_at": 1681623462.0,
      "cleaning_completed_at": 1681623462.0,
      "splitting_completed_at": 1681623462.0,
      "completed_at": null,
      "paused_at": null,
      "error": null,
      "stopped_at": null,
      "completed_segments": 24,
      "total_segments": 100
    }
  ]
}
```

## 删除文档
**请求方法**: DELETE
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |

### Request (curl)
```bash
curl --location --request DELETE 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```text
204 No Content
```

## 知识库文档列表
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Query

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| keyword | string | 搜索关键词，可选，目前仅搜索文档名称 |
| page | string | 页码，可选 |
| limit | string | 返回条数，可选，默认 20，范围 1-100 |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/documents' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "data": [
    {
      "id": "",
      "position": 1,
      "data_source_type": "file_upload",
      "data_source_info": null,
      "dataset_process_rule_id": null,
      "name": "dify",
      "created_from": "",
      "created_by": "",
      "created_at": 1681623639,
      "tokens": 0,
      "indexing_status": "waiting",
      "error": null,
      "enabled": true,
      "disabled_at": null,
      "disabled_by": null,
      "archived": false
    }
  ],
  "has_more": false,
  "limit": 20,
  "total": 9,
  "page": 1
}
```

## 获取文档详情
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}
**说明**: 获取文档详情.
### Request (curl)
```bash
curl -X GET 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}' \
-H 'Authorization: Bearer {api_key}'
```
### Response
```json
{
"id": "f46ae30c-5c11-471b-96d0-464f5f32a7b2",
"position": 1,
"data_source_type": "upload_file",
"data_source_info": {
    "upload_file": {
        ...
    }
},
"dataset_process_rule_id": "24b99906-845e-499f-9e3c-d5565dd6962c",
"dataset_process_rule": {
    "mode": "hierarchical",
    "rules": {
        "pre_processing_rules": [
            {
                "id": "remove_extra_spaces",
                "enabled": true
            },
            {
                "id": "remove_urls_emails",
                "enabled": false
            }
        ],
        "segmentation": {
            "separator": "**********page_ending**********",
            "max_tokens": 1024,
            "chunk_overlap": 0
        },
        "parent_mode": "paragraph",
        "subchunk_segmentation": {
            "separator": "\n",
            "max_tokens": 512,
            "chunk_overlap": 0
        }
    }
},
"document_process_rule": {
    "id": "24b99906-845e-499f-9e3c-d5565dd6962c",
    "dataset_id": "48a0db76-d1a9-46c1-ae35-2baaa919a8a9",
    "mode": "hierarchical",
    "rules": {
        "pre_processing_rules": [
            {
                "id": "remove_extra_spaces",
                "enabled": true
            },
            {
                "id": "remove_urls_emails",
                "enabled": false
            }
        ],
        "segmentation": {
            "separator": "**********page_ending**********",
            "max_tokens": 1024,
            "chunk_overlap": 0
        },
        "parent_mode": "paragraph",
        "subchunk_segmentation": {
            "separator": "\n",
            "max_tokens": 512,
            "chunk_overlap": 0
        }
    }
},
"name": "xxxx",
"created_from": "web",
"created_by": "17f71940-a7b5-4c77-b60f-2bd645c1ffa0",
"created_at": 1750464191,
"tokens": null,
"indexing_status": "waiting",
"completed_at": null,
"updated_at": 1750464191,
"indexing_latency": null,
"error": null,
"enabled": true,
"disabled_at": null,
"disabled_by": null,
"archived": false,
"segment_count": 0,
"average_segment_length": 0,
"hit_count": null,
"display_status": "queuing",
"doc_form": "hierarchical_model",
"doc_language": "Chinese Simplified"
}
```

## 更新文档状态
**请求方法**: PATCH
**请求 URL**: /datasets/{dataset_id}/documents/status/{action}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| action | string | enable - 启用文档<br>disable - 禁用文档<br>archive - 归档文档<br>un_archive - 取消归档文档 |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| document_ids | array[string] | 文档 ID 列表 |

### Request (curl)
```bash
curl --location --request PATCH 'http://localhost/v1/datasets/{dataset_id}/documents/status/{action}' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{
    "document_ids": ["doc-id-1", "doc-id-2"]
}'
```
### Response
```json
{
  "result": "success"
}
```

## 获取上传文件
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/documents/{document_id}/upload-file
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| document_id | string | 文档 ID |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/documents/{document_id}/upload-file' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'
```
### Response
```json
{
  "id": "file_id",
  "name": "file_name",
  "size": 1024,
  "extension": "txt",
  "url": "preview_url",
  "download_url": "download_url",
  "mime_type": "text/plain",
  "created_by": "user_id",
  "created_at": 1728734540
}
```
