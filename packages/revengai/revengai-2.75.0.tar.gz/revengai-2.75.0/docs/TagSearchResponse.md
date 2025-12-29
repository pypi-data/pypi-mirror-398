# TagSearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[TagSearchResult]**](TagSearchResult.md) | The results of the search | 

## Example

```python
from revengai.models.tag_search_response import TagSearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of TagSearchResponse from a JSON string
tag_search_response_instance = TagSearchResponse.from_json(json)
# print the JSON string representation of the object
print(TagSearchResponse.to_json())

# convert the object into a dict
tag_search_response_dict = tag_search_response_instance.to_dict()
# create an instance of TagSearchResponse from a dict
tag_search_response_from_dict = TagSearchResponse.from_dict(tag_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


