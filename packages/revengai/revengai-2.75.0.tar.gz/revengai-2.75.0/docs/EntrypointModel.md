# EntrypointModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **int** |  | 
**first_bytes** | **str** |  | 

## Example

```python
from revengai.models.entrypoint_model import EntrypointModel

# TODO update the JSON string below
json = "{}"
# create an instance of EntrypointModel from a JSON string
entrypoint_model_instance = EntrypointModel.from_json(json)
# print the JSON string representation of the object
print(EntrypointModel.to_json())

# convert the object into a dict
entrypoint_model_dict = entrypoint_model_instance.to_dict()
# create an instance of EntrypointModel from a dict
entrypoint_model_from_dict = EntrypointModel.from_dict(entrypoint_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


