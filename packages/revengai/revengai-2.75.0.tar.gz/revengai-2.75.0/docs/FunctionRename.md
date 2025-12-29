# FunctionRename


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**new_name** | **str** | The new name for the function | 
**new_mangled_name** | **str** | The new mangled name for the function | 

## Example

```python
from revengai.models.function_rename import FunctionRename

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionRename from a JSON string
function_rename_instance = FunctionRename.from_json(json)
# print the JSON string representation of the object
print(FunctionRename.to_json())

# convert the object into a dict
function_rename_dict = function_rename_instance.to_dict()
# create an instance of FunctionRename from a dict
function_rename_from_dict = FunctionRename.from_dict(function_rename_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


