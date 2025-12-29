# CollectionSearchResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_id** | **int** | The ID of the collection | 
**collection_name** | **str** | The name of the collection | 
**scope** | **str** | The scope of the collection | 
**last_updated_at** | **datetime** | The last update date of the collection | 
**created_at** | **datetime** | The creation date of the collection | 
**model_id** | **int** | The model ID of the binary | 
**model_name** | **str** | The name of the model | 
**owned_by** | **str** | The owner of the collection | 
**tags** | **List[str]** |  | [optional] 
**size** | **int** |  | [optional] 
**description** | **str** | The description of the collection | 
**team_id** | **int** |  | [optional] 

## Example

```python
from revengai.models.collection_search_result import CollectionSearchResult

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionSearchResult from a JSON string
collection_search_result_instance = CollectionSearchResult.from_json(json)
# print the JSON string representation of the object
print(CollectionSearchResult.to_json())

# convert the object into a dict
collection_search_result_dict = collection_search_result_instance.to_dict()
# create an instance of CollectionSearchResult from a dict
collection_search_result_from_dict = CollectionSearchResult.from_dict(collection_search_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


