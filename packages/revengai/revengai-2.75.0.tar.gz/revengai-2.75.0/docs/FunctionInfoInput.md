# FunctionInfoInput


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**func_types** | [**FunctionTypeInput**](FunctionTypeInput.md) |  | [optional] 
**func_deps** | [**List[FunctionInfoInputFuncDepsInner]**](FunctionInfoInputFuncDepsInner.md) | List of function dependencies | 

## Example

```python
from revengai.models.function_info_input import FunctionInfoInput

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionInfoInput from a JSON string
function_info_input_instance = FunctionInfoInput.from_json(json)
# print the JSON string representation of the object
print(FunctionInfoInput.to_json())

# convert the object into a dict
function_info_input_dict = function_info_input_instance.to_dict()
# create an instance of FunctionInfoInput from a dict
function_info_input_from_dict = FunctionInfoInput.from_dict(function_info_input_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


