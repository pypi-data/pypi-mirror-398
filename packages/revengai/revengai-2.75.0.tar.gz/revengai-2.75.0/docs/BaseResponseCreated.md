# BaseResponseCreated


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Created**](Created.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_created import BaseResponseCreated

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseCreated from a JSON string
base_response_created_instance = BaseResponseCreated.from_json(json)
# print the JSON string representation of the object
print(BaseResponseCreated.to_json())

# convert the object into a dict
base_response_created_dict = base_response_created_instance.to_dict()
# create an instance of BaseResponseCreated from a dict
base_response_created_from_dict = BaseResponseCreated.from_dict(base_response_created_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


