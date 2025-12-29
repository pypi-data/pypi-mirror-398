# CollectionListItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_name** | **str** | The name of the collection | 
**description** | **str** | The description of the collection | 
**collection_scope** | **str** | The scope of the collection | 
**collection_owner** | **str** | The owner of the collection | 
**official_collection** | **bool** | Whether the collection is maintained by RevEng.AI | 
**collection_tags** | **List[str]** | The tags of the collection | [optional] [default to []]
**collection_size** | **int** | The size of the collection | 
**collection_id** | **int** | The ID of the collection | 
**creation** | **datetime** | The current status of analysis | 
**model_name** | **str** | The model being used for the collection | 
**team_id** | **int** |  | [optional] 

## Example

```python
from revengai.models.collection_list_item import CollectionListItem

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionListItem from a JSON string
collection_list_item_instance = CollectionListItem.from_json(json)
# print the JSON string representation of the object
print(CollectionListItem.to_json())

# convert the object into a dict
collection_list_item_dict = collection_list_item_instance.to_dict()
# create an instance of CollectionListItem from a dict
collection_list_item_from_dict = CollectionListItem.from_dict(collection_list_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


