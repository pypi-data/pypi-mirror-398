# BaseResponseGetAiDecompilationTask


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**GetAiDecompilationTask**](GetAiDecompilationTask.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_get_ai_decompilation_task import BaseResponseGetAiDecompilationTask

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseGetAiDecompilationTask from a JSON string
base_response_get_ai_decompilation_task_instance = BaseResponseGetAiDecompilationTask.from_json(json)
# print the JSON string representation of the object
print(BaseResponseGetAiDecompilationTask.to_json())

# convert the object into a dict
base_response_get_ai_decompilation_task_dict = base_response_get_ai_decompilation_task_instance.to_dict()
# create an instance of BaseResponseGetAiDecompilationTask from a dict
base_response_get_ai_decompilation_task_from_dict = BaseResponseGetAiDecompilationTask.from_dict(base_response_get_ai_decompilation_task_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


