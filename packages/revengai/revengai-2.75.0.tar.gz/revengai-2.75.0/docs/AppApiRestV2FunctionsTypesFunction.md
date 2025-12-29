# AppApiRestV2FunctionsTypesFunction


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Function id | 
**function_name** | **str** | Demangled name of the function | 
**function_mangled_name** | **str** | Mangled name of the function | 
**function_vaddr** | **int** | Function virtual address | 
**function_size** | **int** | Function size | 
**debug** | **bool** | Whether the function is debug | 
**embedding_3d** | **List[float]** |  | [optional] 
**embedding_1d** | **List[float]** |  | [optional] 

## Example

```python
from revengai.models.app_api_rest_v2_functions_types_function import AppApiRestV2FunctionsTypesFunction

# TODO update the JSON string below
json = "{}"
# create an instance of AppApiRestV2FunctionsTypesFunction from a JSON string
app_api_rest_v2_functions_types_function_instance = AppApiRestV2FunctionsTypesFunction.from_json(json)
# print the JSON string representation of the object
print(AppApiRestV2FunctionsTypesFunction.to_json())

# convert the object into a dict
app_api_rest_v2_functions_types_function_dict = app_api_rest_v2_functions_types_function_instance.to_dict()
# create an instance of AppApiRestV2FunctionsTypesFunction from a dict
app_api_rest_v2_functions_types_function_from_dict = AppApiRestV2FunctionsTypesFunction.from_dict(app_api_rest_v2_functions_types_function_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


