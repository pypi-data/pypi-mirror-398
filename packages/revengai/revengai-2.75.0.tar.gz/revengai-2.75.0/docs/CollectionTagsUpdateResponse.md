# CollectionTagsUpdateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tags** | **List[str]** | Collection tags | 

## Example

```python
from revengai.models.collection_tags_update_response import CollectionTagsUpdateResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionTagsUpdateResponse from a JSON string
collection_tags_update_response_instance = CollectionTagsUpdateResponse.from_json(json)
# print the JSON string representation of the object
print(CollectionTagsUpdateResponse.to_json())

# convert the object into a dict
collection_tags_update_response_dict = collection_tags_update_response_instance.to_dict()
# create an instance of CollectionTagsUpdateResponse from a dict
collection_tags_update_response_from_dict = CollectionTagsUpdateResponse.from_dict(collection_tags_update_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


