# FunctionDataTypesStatus


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Function id | 
**completed** | **bool** | Whether the service has completed data types generation | 
**status** | **str** | The current status of the data types service | 

## Example

```python
from revengai.models.function_data_types_status import FunctionDataTypesStatus

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionDataTypesStatus from a JSON string
function_data_types_status_instance = FunctionDataTypesStatus.from_json(json)
# print the JSON string representation of the object
print(FunctionDataTypesStatus.to_json())

# convert the object into a dict
function_data_types_status_dict = function_data_types_status_instance.to_dict()
# create an instance of FunctionDataTypesStatus from a dict
function_data_types_status_from_dict = FunctionDataTypesStatus.from_dict(function_data_types_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


