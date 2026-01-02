# 知识库 API - 错误信息

### 响应字段

- code (string) 返回的错误代码
- status (number) 返回的错误状态
- message (string) 返回的错误信息

### 示例

```json
{
  "code": "no_file_uploaded",
  "message": "Please upload your file.",
  "status": 400
}
```

### 常见错误码

| code                        | status | message                                                                                 |
| --------------------------- | ------ | --------------------------------------------------------------------------------------- |
| no_file_uploaded            | 400    | Please upload your file.                                                                |
| too_many_files              | 400    | Only one file is allowed.                                                               |
| file_too_large              | 413    | File size exceeded.                                                                     |
| unsupported_file_type       | 415    | File type not allowed.                                                                  |
| high_quality_dataset_only   | 400    | Current operation only supports 'high-quality' datasets.                                |
| dataset_not_initialized     | 400    | The dataset is still being initialized or indexing. Please wait a moment.               |
| archived_document_immutable | 403    | The archived document is not editable.                                                  |
| dataset_name_duplicate      | 409    | The dataset name already exists. Please modify your dataset name.                       |
| invalid_action              | 400    | Invalid action.                                                                         |
| document_already_finished   | 400    | The document has been processed. Please refresh the page or go to the document details. |
| document_indexing           | 400    | The document is being processed and cannot be edited.                                   |
| invalid_metadata            | 400    | The metadata content is incorrect. Please check and verify.                             |
