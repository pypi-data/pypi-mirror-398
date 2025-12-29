# MetaModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**pagination** | [**PaginationModel**](PaginationModel.md) |  | [optional] 

## Example

```python
from revengai.models.meta_model import MetaModel

# TODO update the JSON string below
json = "{}"
# create an instance of MetaModel from a JSON string
meta_model_instance = MetaModel.from_json(json)
# print the JSON string representation of the object
print(MetaModel.to_json())

# convert the object into a dict
meta_model_dict = meta_model_instance.to_dict()
# create an instance of MetaModel from a dict
meta_model_from_dict = MetaModel.from_dict(meta_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


