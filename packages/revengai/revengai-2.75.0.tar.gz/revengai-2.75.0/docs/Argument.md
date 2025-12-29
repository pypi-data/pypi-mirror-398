# Argument


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**offset** | **int** | Offset of the argument in the function signature | 
**name** | **str** | Name of the argument | 
**type** | **str** | Data type of the argument | 
**size** | **int** | Size of the argument in bytes | 

## Example

```python
from revengai.models.argument import Argument

# TODO update the JSON string below
json = "{}"
# create an instance of Argument from a JSON string
argument_instance = Argument.from_json(json)
# print the JSON string representation of the object
print(Argument.to_json())

# convert the object into a dict
argument_dict = argument_instance.to_dict()
# create an instance of Argument from a dict
argument_from_dict = Argument.from_dict(argument_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


