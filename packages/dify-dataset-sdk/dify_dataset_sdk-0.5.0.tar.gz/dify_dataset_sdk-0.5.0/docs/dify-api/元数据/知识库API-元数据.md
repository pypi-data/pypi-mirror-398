# 知识库 API - 元数据

本文档基于控制台页面 /datasets?category=api 生成。

## 新增元数据
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/metadata
### Params

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| segment | object | type (string) 元数据类型，必填<br>name (string) 元数据名称，必填 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/metadata' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'\
--data-raw '{"type": "string", "name": "test"}'
```
### Response
```json
{
  "id": "abc",
  "type": "string",
  "name": "test"
}
```

## 更新元数据
**请求方法**: PATCH
**请求 URL**: /datasets/{dataset_id}/metadata/{metadata_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| metadata_id | string | 元数据 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| segment | object | name (string) 元数据名称，必填 |

### Request (curl)
```bash
curl --location --request PATCH 'http://localhost/v1/datasets/{dataset_id}/metadata/{metadata_id}' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'\
--data-raw '{"name": "test"}'
```
### Response
```json
{
  "id": "abc",
  "type": "string",
  "name": "test"
}
```

## 删除元数据
**请求方法**: DELETE
**请求 URL**: /datasets/{dataset_id}/metadata/{metadata_id}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| metadata_id | string | 元数据 ID |

### Request (curl)
```bash
curl --location --request DELETE 'http://localhost/v1/datasets/{dataset_id}/metadata/{metadata_id}' \
--header 'Authorization: Bearer {api_key}'
```

## 启用/禁用内置元数据
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/metadata/built-in/{action}
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |
| action | string | disable/enable |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/metadata/built-in/{action}' \
--header 'Authorization: Bearer {api_key}'
```

## 更新文档元数据
**请求方法**: POST
**请求 URL**: /datasets/{dataset_id}/documents/metadata
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| operation_data | object list | document_id (string) 文档 ID<br>metadata_list (list) 元数据列表<br>id (string) 元数据 ID<br>value (string) 元数据值<br>name (string) 元数据名称 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/{dataset_id}/documents/metadata' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'\
--data-raw '{"operation_data": [{"document_id": "document_id", "metadata_list": [{"id": "id", "value": "value", "name": "name"}]}]}'
```

## 查询知识库元数据列表
**请求方法**: GET
**请求 URL**: /datasets/{dataset_id}/metadata
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | 知识库 ID |

### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/{dataset_id}/metadata' \
--header 'Authorization: Bearer {api_key}'
```
### Response
```json
{
  "doc_metadata": [
    {
      "id": "",
      "name": "name",
      "type": "string",
      "use_count": 0,
    },
    ...
  ],
  "built_in_field_enabled": true
}
```
