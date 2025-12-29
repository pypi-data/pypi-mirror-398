# FunctionDataTypes


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**completed** | **bool** | Whether the service has completed data types generation | 
**status** | **str** | The current status of the data types service | 
**data_types** | [**FunctionInfoOutput**](FunctionInfoOutput.md) |  | [optional] 
**data_types_version** | **int** |  | [optional] 

## Example

```python
from revengai.models.function_data_types import FunctionDataTypes

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionDataTypes from a JSON string
function_data_types_instance = FunctionDataTypes.from_json(json)
# print the JSON string representation of the object
print(FunctionDataTypes.to_json())

# convert the object into a dict
function_data_types_dict = function_data_types_instance.to_dict()
# create an instance of FunctionDataTypes from a dict
function_data_types_from_dict = FunctionDataTypes.from_dict(function_data_types_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


