# BaseResponseFunctionDataTypesList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**FunctionDataTypesList**](FunctionDataTypesList.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_function_data_types_list import BaseResponseFunctionDataTypesList

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseFunctionDataTypesList from a JSON string
base_response_function_data_types_list_instance = BaseResponseFunctionDataTypesList.from_json(json)
# print the JSON string representation of the object
print(BaseResponseFunctionDataTypesList.to_json())

# convert the object into a dict
base_response_function_data_types_list_dict = base_response_function_data_types_list_instance.to_dict()
# create an instance of BaseResponseFunctionDataTypesList from a dict
base_response_function_data_types_list_from_dict = BaseResponseFunctionDataTypesList.from_dict(base_response_function_data_types_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


