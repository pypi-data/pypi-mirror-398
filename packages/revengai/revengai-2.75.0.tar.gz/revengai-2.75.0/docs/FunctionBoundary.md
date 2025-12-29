# FunctionBoundary


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**mangled_name** | **str** |  | 
**start_address** | **int** |  | 
**end_address** | **int** |  | 

## Example

```python
from revengai.models.function_boundary import FunctionBoundary

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionBoundary from a JSON string
function_boundary_instance = FunctionBoundary.from_json(json)
# print the JSON string representation of the object
print(FunctionBoundary.to_json())

# convert the object into a dict
function_boundary_dict = function_boundary_instance.to_dict()
# create an instance of FunctionBoundary from a dict
function_boundary_from_dict = FunctionBoundary.from_dict(function_boundary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


