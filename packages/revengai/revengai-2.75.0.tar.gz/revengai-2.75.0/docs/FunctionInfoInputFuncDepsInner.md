# FunctionInfoInputFuncDepsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**name** | **str** | Name of the global variable | 
**size** | **int** | Size of the global variable in bytes | 
**members** | **Dict[str, int]** | Dictionary of enumeration members and their values | 
**artifact_type** | **str** | Type of artifact that the global variable is associated with | [optional] 
**type** | **str** | Data type of the global variable | 
**addr** | **int** | Memory address of the global variable | 

## Example

```python
from revengai.models.function_info_input_func_deps_inner import FunctionInfoInputFuncDepsInner

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionInfoInputFuncDepsInner from a JSON string
function_info_input_func_deps_inner_instance = FunctionInfoInputFuncDepsInner.from_json(json)
# print the JSON string representation of the object
print(FunctionInfoInputFuncDepsInner.to_json())

# convert the object into a dict
function_info_input_func_deps_inner_dict = function_info_input_func_deps_inner_instance.to_dict()
# create an instance of FunctionInfoInputFuncDepsInner from a dict
function_info_input_func_deps_inner_from_dict = FunctionInfoInputFuncDepsInner.from_dict(function_info_input_func_deps_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


