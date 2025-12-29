# Params


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**debug_hash** | **str** |  | 
**binary_size** | **int** | The size of the binary data | 
**architecture** | **str** | The architecture of the binary data | 
**binary_type** | **str** | The type of binary data | 
**binary_format** | **str** | The format of the binary data | 
**binary_dynamic** | **bool** | Whether the binary data is dynamic | 
**model_name** | **str** | The name of the model | 

## Example

```python
from revengai.models.params import Params

# TODO update the JSON string below
json = "{}"
# create an instance of Params from a JSON string
params_instance = Params.from_json(json)
# print the JSON string representation of the object
print(Params.to_json())

# convert the object into a dict
params_dict = params_instance.to_dict()
# create an instance of Params from a dict
params_from_dict = Params.from_dict(params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


