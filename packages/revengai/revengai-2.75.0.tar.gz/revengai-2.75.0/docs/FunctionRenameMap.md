# FunctionRenameMap


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | The ID of the function to rename | 
**new_name** | **str** | The new name for the function | 
**new_mangled_name** | **str** | The new mangled name for the function | 

## Example

```python
from revengai.models.function_rename_map import FunctionRenameMap

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionRenameMap from a JSON string
function_rename_map_instance = FunctionRenameMap.from_json(json)
# print the JSON string representation of the object
print(FunctionRenameMap.to_json())

# convert the object into a dict
function_rename_map_dict = function_rename_map_instance.to_dict()
# create an instance of FunctionRenameMap from a dict
function_rename_map_from_dict = FunctionRenameMap.from_dict(function_rename_map_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


