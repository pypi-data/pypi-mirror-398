# FunctionInfoOutput


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**func_types** | [**FunctionTypeOutput**](FunctionTypeOutput.md) |  | [optional] 
**func_deps** | [**List[FunctionInfoInputFuncDepsInner]**](FunctionInfoInputFuncDepsInner.md) | List of function dependencies | 

## Example

```python
from revengai.models.function_info_output import FunctionInfoOutput

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionInfoOutput from a JSON string
function_info_output_instance = FunctionInfoOutput.from_json(json)
# print the JSON string representation of the object
print(FunctionInfoOutput.to_json())

# convert the object into a dict
function_info_output_dict = function_info_output_instance.to_dict()
# create an instance of FunctionInfoOutput from a dict
function_info_output_from_dict = FunctionInfoOutput.from_dict(function_info_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


