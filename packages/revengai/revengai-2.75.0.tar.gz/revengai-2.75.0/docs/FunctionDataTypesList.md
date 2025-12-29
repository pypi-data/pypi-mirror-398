# FunctionDataTypesList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_count** | **int** | Total number of functions in analysis | [optional] [default to 0]
**total_data_types_count** | **int** | Total number of functions with data types | [optional] [default to 0]
**items** | [**List[FunctionDataTypesListItem]**](FunctionDataTypesListItem.md) | List of function data types information | 

## Example

```python
from revengai.models.function_data_types_list import FunctionDataTypesList

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionDataTypesList from a JSON string
function_data_types_list_instance = FunctionDataTypesList.from_json(json)
# print the JSON string representation of the object
print(FunctionDataTypesList.to_json())

# convert the object into a dict
function_data_types_list_dict = function_data_types_list_instance.to_dict()
# create an instance of FunctionDataTypesList from a dict
function_data_types_list_from_dict = FunctionDataTypesList.from_dict(function_data_types_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


