# GlobalVariable


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**addr** | **int** | Memory address of the global variable | 
**name** | **str** | Name of the global variable | 
**type** | **str** | Data type of the global variable | 
**size** | **int** | Size of the global variable in bytes | 
**artifact_type** | **str** | Type of artifact that the global variable is associated with | [optional] 

## Example

```python
from revengai.models.global_variable import GlobalVariable

# TODO update the JSON string below
json = "{}"
# create an instance of GlobalVariable from a JSON string
global_variable_instance = GlobalVariable.from_json(json)
# print the JSON string representation of the object
print(GlobalVariable.to_json())

# convert the object into a dict
global_variable_dict = global_variable_instance.to_dict()
# create an instance of GlobalVariable from a dict
global_variable_from_dict = GlobalVariable.from_dict(global_variable_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


