# BaseResponseCollectionTagsUpdateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**CollectionTagsUpdateResponse**](CollectionTagsUpdateResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_collection_tags_update_response import BaseResponseCollectionTagsUpdateResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseCollectionTagsUpdateResponse from a JSON string
base_response_collection_tags_update_response_instance = BaseResponseCollectionTagsUpdateResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseCollectionTagsUpdateResponse.to_json())

# convert the object into a dict
base_response_collection_tags_update_response_dict = base_response_collection_tags_update_response_instance.to_dict()
# create an instance of BaseResponseCollectionTagsUpdateResponse from a dict
base_response_collection_tags_update_response_from_dict = BaseResponseCollectionTagsUpdateResponse.from_dict(base_response_collection_tags_update_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


