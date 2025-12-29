# FunctionCapabilityResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**capabilities** | **List[str]** | The capabilities of the function | 

## Example

```python
from revengai.models.function_capability_response import FunctionCapabilityResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionCapabilityResponse from a JSON string
function_capability_response_instance = FunctionCapabilityResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionCapabilityResponse.to_json())

# convert the object into a dict
function_capability_response_dict = function_capability_response_instance.to_dict()
# create an instance of FunctionCapabilityResponse from a dict
function_capability_response_from_dict = FunctionCapabilityResponse.from_dict(function_capability_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


