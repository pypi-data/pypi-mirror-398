# 知识库 API - 标签

本文档基于控制台页面 /datasets?category=api 生成。

## 新增知识库类型标签
**请求方法**: POST
**请求 URL**: /datasets/tags
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| name | string | (text) 新标签名称，必填，最大长度为 50 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/tags' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"name": "testtag1"}'
```
### Response
```json
{
  "id": "eddb66c2-04a1-4e3a-8cb2-75abd01e12a6",
  "name": "testtag1",
  "type": "knowledge",
  "binding_count": 0
}
```

## 获取知识库类型标签
**请求方法**: GET
**请求 URL**: /datasets/tags
### Request (curl)
```bash
curl --location --request GET 'http://localhost/v1/datasets/tags' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json'
```
### Response
```json
[
    {
        "id": "39d6934c-ed36-463d-b4a7-377fa1503dc0",
        "name": "testtag1",
        "type": "knowledge",
        "binding_count": "0"
    },
    ...
]
```

## 修改知识库类型标签名称
**请求方法**: PATCH
**请求 URL**: /datasets/tags
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| name | string | (text) 修改后的标签名称，必填，最大长度为 50 |
| tag_id | string | (text) 标签 ID，必填 |

### Request (curl)
```bash
curl --location --request PATCH 'http://localhost/v1/datasets/tags' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"name": "testtag2", "tag_id": "e1a0a3db-ee34-4e04-842a-81555d5316fd"}
```
### Response
```json
{
  "id": "eddb66c2-04a1-4e3a-8cb2-75abd01e12a6",
  "name": "tag-renamed",
  "type": "knowledge",
  "binding_count": 0
}
```

## 删除知识库类型标签
**请求方法**: DELETE
**请求 URL**: /datasets/tags
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| tag_id | string | (text) 标签 ID，必填 |

### Request (curl)
```bash
curl --location --request DELETE 'http://localhost/v1/datasets/tags' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{ "tag_id": "e1a0a3db-ee34-4e04-842a-81555d5316fd"}
```
### Response
```json
{ "result": "success" }
```

## 绑定知识库到知识库类型标签
**请求方法**: POST
**请求 URL**: /datasets/tags/binding
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| tag_ids | list | (list) 标签 ID 列表，必填 |
| target_id | string | (text) 知识库 ID，必填 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/tags/binding' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"tag_ids": ["65cc29be-d072-4e26-adf4-2f727644da29","1e5348f3-d3ff-42b8-a1b7-0a86d518001a"], "target_id": "a932ea9f-fae1-4b2c-9b65-71c56e2cacd6"}'
```
### Response
```json
{ "result": "success" }
```

## 解绑知识库和知识库类型标签
**请求方法**: POST
**请求 URL**: /datasets/tags/unbinding
### Request Body

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| tag_id | string | (text) 标签 ID，必填 |
| target_id | string | (text) 知识库 ID，必填 |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/tags/unbinding' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
--data-raw '{"tag_id": "1e5348f3-d3ff-42b8-a1b7-0a86d518001a", "target_id": "a932ea9f-fae1-4b2c-9b65-71c56e2cacd6"}'
```
### Response
```json
{ "result": "success" }
```

## 查询知识库已绑定的标签
**请求方法**: POST
**请求 URL**: /datasets/<uuid:dataset_id>/tags
### Path

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| dataset_id | string | (text) 知识库 ID |

### Request (curl)
```bash
curl --location --request POST 'http://localhost/v1/datasets/<uuid:dataset_id>/tags' \
--header 'Authorization: Bearer {api_key}' \
--header 'Content-Type: application/json' \
```
### Response
```json
{
  "data":
    [
      {"id": "4a601f4f-f8a2-4166-ae7c-58c3b252a524",
      "name": "123"
      },
      ...
    ],
  "total": 3
}
```
