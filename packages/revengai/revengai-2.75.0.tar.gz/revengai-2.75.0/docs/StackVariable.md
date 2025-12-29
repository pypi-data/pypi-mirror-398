# StackVariable


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**offset** | **int** | Offset of the stack variable | 
**name** | **str** | Name of the stack variable | 
**type** | **str** | Data type of the stack variable | 
**size** | **int** | Size of the stack variable in bytes | 
**addr** | **int** | Memory address of the stack variable | 

## Example

```python
from revengai.models.stack_variable import StackVariable

# TODO update the JSON string below
json = "{}"
# create an instance of StackVariable from a JSON string
stack_variable_instance = StackVariable.from_json(json)
# print the JSON string representation of the object
print(StackVariable.to_json())

# convert the object into a dict
stack_variable_dict = stack_variable_instance.to_dict()
# create an instance of StackVariable from a dict
stack_variable_from_dict = StackVariable.from_dict(stack_variable_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


