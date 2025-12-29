# CollectionTagsUpdateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tags** | **List[str]** |  | 

## Example

```python
from revengai.models.collection_tags_update_request import CollectionTagsUpdateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionTagsUpdateRequest from a JSON string
collection_tags_update_request_instance = CollectionTagsUpdateRequest.from_json(json)
# print the JSON string representation of the object
print(CollectionTagsUpdateRequest.to_json())

# convert the object into a dict
collection_tags_update_request_dict = collection_tags_update_request_instance.to_dict()
# create an instance of CollectionTagsUpdateRequest from a dict
collection_tags_update_request_from_dict = CollectionTagsUpdateRequest.from_dict(collection_tags_update_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


