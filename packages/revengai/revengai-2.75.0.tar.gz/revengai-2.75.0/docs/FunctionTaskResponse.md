# FunctionTaskResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**FunctionTaskStatus**](FunctionTaskStatus.md) |  | [optional] 
**error_message** | **str** |  | [optional] 

## Example

```python
from revengai.models.function_task_response import FunctionTaskResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionTaskResponse from a JSON string
function_task_response_instance = FunctionTaskResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionTaskResponse.to_json())

# convert the object into a dict
function_task_response_dict = function_task_response_instance.to_dict()
# create an instance of FunctionTaskResponse from a dict
function_task_response_from_dict = FunctionTaskResponse.from_dict(function_task_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


