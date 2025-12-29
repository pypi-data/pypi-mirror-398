# BaseResponseListFunctionNameHistory


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**List[FunctionNameHistory]**](FunctionNameHistory.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_list_function_name_history import BaseResponseListFunctionNameHistory

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseListFunctionNameHistory from a JSON string
base_response_list_function_name_history_instance = BaseResponseListFunctionNameHistory.from_json(json)
# print the JSON string representation of the object
print(BaseResponseListFunctionNameHistory.to_json())

# convert the object into a dict
base_response_list_function_name_history_dict = base_response_list_function_name_history_instance.to_dict()
# create an instance of BaseResponseListFunctionNameHistory from a dict
base_response_list_function_name_history_from_dict = BaseResponseListFunctionNameHistory.from_dict(base_response_list_function_name_history_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


