# FunctionStringsResponse

Response for listing all the strings of a function.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**strings** | [**List[FunctionString]**](FunctionString.md) | The strings associated with this function | 
**total_strings** | **int** | The total number of strings associated with this function | 

## Example

```python
from revengai.models.function_strings_response import FunctionStringsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionStringsResponse from a JSON string
function_strings_response_instance = FunctionStringsResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionStringsResponse.to_json())

# convert the object into a dict
function_strings_response_dict = function_strings_response_instance.to_dict()
# create an instance of FunctionStringsResponse from a dict
function_strings_response_from_dict = FunctionStringsResponse.from_dict(function_strings_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


