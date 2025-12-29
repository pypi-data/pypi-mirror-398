# CalleesCallerFunctionsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**base_address** | **int** | Base address of the binary | 
**callees** | [**List[CalleeFunctionInfo]**](CalleeFunctionInfo.md) | List of functions called by the target function | 
**callers** | [**List[CallerFunctionInfo]**](CallerFunctionInfo.md) | List of functions that call the target function | 

## Example

```python
from revengai.models.callees_caller_functions_response import CalleesCallerFunctionsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CalleesCallerFunctionsResponse from a JSON string
callees_caller_functions_response_instance = CalleesCallerFunctionsResponse.from_json(json)
# print the JSON string representation of the object
print(CalleesCallerFunctionsResponse.to_json())

# convert the object into a dict
callees_caller_functions_response_dict = callees_caller_functions_response_instance.to_dict()
# create an instance of CalleesCallerFunctionsResponse from a dict
callees_caller_functions_response_from_dict = CalleesCallerFunctionsResponse.from_dict(callees_caller_functions_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


