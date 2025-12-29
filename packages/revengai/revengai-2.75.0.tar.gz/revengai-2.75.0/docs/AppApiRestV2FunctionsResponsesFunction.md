# AppApiRestV2FunctionsResponsesFunction

Function schema used in function strings response.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** |  | [optional] 
**function_vaddr** | **int** | Function virtual address | 

## Example

```python
from revengai.models.app_api_rest_v2_functions_responses_function import AppApiRestV2FunctionsResponsesFunction

# TODO update the JSON string below
json = "{}"
# create an instance of AppApiRestV2FunctionsResponsesFunction from a JSON string
app_api_rest_v2_functions_responses_function_instance = AppApiRestV2FunctionsResponsesFunction.from_json(json)
# print the JSON string representation of the object
print(AppApiRestV2FunctionsResponsesFunction.to_json())

# convert the object into a dict
app_api_rest_v2_functions_responses_function_dict = app_api_rest_v2_functions_responses_function_instance.to_dict()
# create an instance of AppApiRestV2FunctionsResponsesFunction from a dict
app_api_rest_v2_functions_responses_function_from_dict = AppApiRestV2FunctionsResponsesFunction.from_dict(app_api_rest_v2_functions_responses_function_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


