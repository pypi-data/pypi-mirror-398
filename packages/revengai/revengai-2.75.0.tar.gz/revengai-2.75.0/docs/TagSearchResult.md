# TagSearchResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tag_id** | **int** | The ID of the tag | 
**tag** | **str** | The name of the tag | 

## Example

```python
from revengai.models.tag_search_result import TagSearchResult

# TODO update the JSON string below
json = "{}"
# create an instance of TagSearchResult from a JSON string
tag_search_result_instance = TagSearchResult.from_json(json)
# print the JSON string representation of the object
print(TagSearchResult.to_json())

# convert the object into a dict
tag_search_result_dict = tag_search_result_instance.to_dict()
# create an instance of TagSearchResult from a dict
tag_search_result_from_dict = TagSearchResult.from_dict(tag_search_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


