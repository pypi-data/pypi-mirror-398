# FunctionDataTypesListItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**completed** | **bool** | Whether the service has completed data types generation | 
**status** | **str** | The current status of the data types service | 
**data_types** | [**FunctionInfoOutput**](FunctionInfoOutput.md) |  | [optional] 
**data_types_version** | **int** |  | [optional] 
**function_id** | **int** | Function id | 

## Example

```python
from revengai.models.function_data_types_list_item import FunctionDataTypesListItem

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionDataTypesListItem from a JSON string
function_data_types_list_item_instance = FunctionDataTypesListItem.from_json(json)
# print the JSON string representation of the object
print(FunctionDataTypesListItem.to_json())

# convert the object into a dict
function_data_types_list_item_dict = function_data_types_list_item_instance.to_dict()
# create an instance of FunctionDataTypesListItem from a dict
function_data_types_list_item_from_dict = FunctionDataTypesListItem.from_dict(function_data_types_list_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


