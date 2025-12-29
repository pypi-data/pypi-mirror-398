# FunctionListItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **int** | Function id | 
**name** | **str** | Name of the function | 
**name_source_type** | **str** | The source (process) the function name came from | 
**mangled_name** | **str** | Mangled name of the function | 
**vaddr** | **int** | Function virtual address | 
**size** | **int** | Function size in bytes | 
**debug** | **bool** | Whether the function has debug information | 

## Example

```python
from revengai.models.function_list_item import FunctionListItem

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionListItem from a JSON string
function_list_item_instance = FunctionListItem.from_json(json)
# print the JSON string representation of the object
print(FunctionListItem.to_json())

# convert the object into a dict
function_list_item_dict = function_list_item_instance.to_dict()
# create an instance of FunctionListItem from a dict
function_list_item_from_dict = FunctionListItem.from_dict(function_list_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


