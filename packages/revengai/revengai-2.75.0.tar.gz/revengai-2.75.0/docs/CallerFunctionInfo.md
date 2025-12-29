# CallerFunctionInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Unique identifier of the function | 
**matched_function_id** | **int** |  | 
**dashboard_url** | **str** |  | 
**is_external** | **bool** | Indicates if the function is external | [optional] [default to False]
**caller_name** | **str** | Name of the calling function | 
**caller_vaddr** | **str** | Virtual address of the calling function | 

## Example

```python
from revengai.models.caller_function_info import CallerFunctionInfo

# TODO update the JSON string below
json = "{}"
# create an instance of CallerFunctionInfo from a JSON string
caller_function_info_instance = CallerFunctionInfo.from_json(json)
# print the JSON string representation of the object
print(CallerFunctionInfo.to_json())

# convert the object into a dict
caller_function_info_dict = caller_function_info_instance.to_dict()
# create an instance of CallerFunctionInfo from a dict
caller_function_info_from_dict = CallerFunctionInfo.from_dict(caller_function_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


