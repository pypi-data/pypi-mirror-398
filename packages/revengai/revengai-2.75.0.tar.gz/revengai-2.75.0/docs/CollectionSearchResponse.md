# CollectionSearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[CollectionSearchResult]**](CollectionSearchResult.md) | The results of the search | 

## Example

```python
from revengai.models.collection_search_response import CollectionSearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionSearchResponse from a JSON string
collection_search_response_instance = CollectionSearchResponse.from_json(json)
# print the JSON string representation of the object
print(CollectionSearchResponse.to_json())

# convert the object into a dict
collection_search_response_dict = collection_search_response_instance.to_dict()
# create an instance of CollectionSearchResponse from a dict
collection_search_response_from_dict = CollectionSearchResponse.from_dict(collection_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


