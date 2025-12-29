# FunctionsListRename


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**functions** | [**List[FunctionRenameMap]**](FunctionRenameMap.md) | A list of functions to rename | 

## Example

```python
from revengai.models.functions_list_rename import FunctionsListRename

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionsListRename from a JSON string
functions_list_rename_instance = FunctionsListRename.from_json(json)
# print the JSON string representation of the object
print(FunctionsListRename.to_json())

# convert the object into a dict
functions_list_rename_dict = functions_list_rename_instance.to_dict()
# create an instance of FunctionsListRename from a dict
functions_list_rename_from_dict = FunctionsListRename.from_dict(functions_list_rename_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


