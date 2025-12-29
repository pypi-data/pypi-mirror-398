# FunctionTypeOutput


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**addr** | **int** | Memory address of the function | 
**size** | **int** | Size of the function in bytes | 
**header** | [**FunctionHeader**](FunctionHeader.md) | Function header information | 
**stack_vars** | [**Dict[str, StackVariable]**](StackVariable.md) |  | [optional] 
**name** | **str** | Name of the function | 
**type** | **str** | Return type of the function | 
**artifact_type** | **str** | Type of artifact that the structure is associated with | [optional] [default to 'Function']

## Example

```python
from revengai.models.function_type_output import FunctionTypeOutput

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionTypeOutput from a JSON string
function_type_output_instance = FunctionTypeOutput.from_json(json)
# print the JSON string representation of the object
print(FunctionTypeOutput.to_json())

# convert the object into a dict
function_type_output_dict = function_type_output_instance.to_dict()
# create an instance of FunctionTypeOutput from a dict
function_type_output_from_dict = FunctionTypeOutput.from_dict(function_type_output_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


