# UpdateFunctionDataTypes


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data_types_version** | **int** | Version of the function data types, used to check this update is not overwriting a newer one | 
**data_types** | [**FunctionInfoInput**](FunctionInfoInput.md) | Function data types information to update | 

## Example

```python
from revengai.models.update_function_data_types import UpdateFunctionDataTypes

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateFunctionDataTypes from a JSON string
update_function_data_types_instance = UpdateFunctionDataTypes.from_json(json)
# print the JSON string representation of the object
print(UpdateFunctionDataTypes.to_json())

# convert the object into a dict
update_function_data_types_dict = update_function_data_types_instance.to_dict()
# create an instance of UpdateFunctionDataTypes from a dict
update_function_data_types_from_dict = UpdateFunctionDataTypes.from_dict(update_function_data_types_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


