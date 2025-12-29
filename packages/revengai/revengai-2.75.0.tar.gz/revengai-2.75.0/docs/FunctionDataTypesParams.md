# FunctionDataTypesParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_ids** | **List[int]** | The function ID&#39;s to generate/get data types for | 

## Example

```python
from revengai.models.function_data_types_params import FunctionDataTypesParams

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionDataTypesParams from a JSON string
function_data_types_params_instance = FunctionDataTypesParams.from_json(json)
# print the JSON string representation of the object
print(FunctionDataTypesParams.to_json())

# convert the object into a dict
function_data_types_params_dict = function_data_types_params_instance.to_dict()
# create an instance of FunctionDataTypesParams from a dict
function_data_types_params_from_dict = FunctionDataTypesParams.from_dict(function_data_types_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


