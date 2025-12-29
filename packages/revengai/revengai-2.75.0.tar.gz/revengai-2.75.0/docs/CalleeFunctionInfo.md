# CalleeFunctionInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Unique identifier of the function | 
**matched_function_id** | **int** |  | 
**dashboard_url** | **str** |  | 
**is_external** | **bool** | Indicates if the function is external | [optional] [default to False]
**callee_name** | **str** | Name of the called function | 
**callee_vaddr** | **str** | Virtual address of the called function | 

## Example

```python
from revengai.models.callee_function_info import CalleeFunctionInfo

# TODO update the JSON string below
json = "{}"
# create an instance of CalleeFunctionInfo from a JSON string
callee_function_info_instance = CalleeFunctionInfo.from_json(json)
# print the JSON string representation of the object
print(CalleeFunctionInfo.to_json())

# convert the object into a dict
callee_function_info_dict = callee_function_info_instance.to_dict()
# create an instance of CalleeFunctionInfo from a dict
callee_function_info_from_dict = CalleeFunctionInfo.from_dict(callee_function_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


