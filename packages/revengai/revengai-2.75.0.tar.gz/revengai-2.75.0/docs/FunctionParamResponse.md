# FunctionParamResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**d_type** | **str** |  | 
**loc** | **str** |  | 
**addr** | **str** |  | 
**length** | **int** |  | 
**name** | **str** |  | 

## Example

```python
from revengai.models.function_param_response import FunctionParamResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionParamResponse from a JSON string
function_param_response_instance = FunctionParamResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionParamResponse.to_json())

# convert the object into a dict
function_param_response_dict = function_param_response_instance.to_dict()
# create an instance of FunctionParamResponse from a dict
function_param_response_from_dict = FunctionParamResponse.from_dict(function_param_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


