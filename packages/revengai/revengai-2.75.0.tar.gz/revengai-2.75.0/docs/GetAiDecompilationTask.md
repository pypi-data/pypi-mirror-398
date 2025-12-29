# GetAiDecompilationTask


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** |  | 
**decompilation** | **str** |  | 
**raw_decompilation** | **str** |  | 
**function_mapping** | [**Dict[str, InverseFunctionMapItem]**](InverseFunctionMapItem.md) |  | 
**function_mapping_full** | [**FunctionMappingFull**](FunctionMappingFull.md) |  | 
**summary** | **str** |  | [optional] 
**ai_summary** | **str** |  | [optional] 
**raw_ai_summary** | **str** |  | [optional] 
**predicted_function_name** | **str** |  | [optional] 

## Example

```python
from revengai.models.get_ai_decompilation_task import GetAiDecompilationTask

# TODO update the JSON string below
json = "{}"
# create an instance of GetAiDecompilationTask from a JSON string
get_ai_decompilation_task_instance = GetAiDecompilationTask.from_json(json)
# print the JSON string representation of the object
print(GetAiDecompilationTask.to_json())

# convert the object into a dict
get_ai_decompilation_task_dict = get_ai_decompilation_task_instance.to_dict()
# create an instance of GetAiDecompilationTask from a dict
get_ai_decompilation_task_from_dict = GetAiDecompilationTask.from_dict(get_ai_decompilation_task_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


