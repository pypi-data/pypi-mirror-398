# FunctionString


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The value of the string literal | 
**vaddr** | **int** | The vaddr of the string value | 

## Example

```python
from revengai.models.function_string import FunctionString

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionString from a JSON string
function_string_instance = FunctionString.from_json(json)
# print the JSON string representation of the object
print(FunctionString.to_json())

# convert the object into a dict
function_string_dict = function_string_instance.to_dict()
# create an instance of FunctionString from a dict
function_string_from_dict = FunctionString.from_dict(function_string_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


