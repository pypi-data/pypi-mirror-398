# FunctionLocalVariableResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**d_type** | **str** |  | 
**size** | **int** |  | 
**loc** | **str** |  | 
**name** | **str** |  | 

## Example

```python
from revengai.models.function_local_variable_response import FunctionLocalVariableResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionLocalVariableResponse from a JSON string
function_local_variable_response_instance = FunctionLocalVariableResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionLocalVariableResponse.to_json())

# convert the object into a dict
function_local_variable_response_dict = function_local_variable_response_instance.to_dict()
# create an instance of FunctionLocalVariableResponse from a dict
function_local_variable_response_from_dict = FunctionLocalVariableResponse.from_dict(function_local_variable_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


