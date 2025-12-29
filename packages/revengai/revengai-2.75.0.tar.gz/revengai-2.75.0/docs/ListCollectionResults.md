# ListCollectionResults


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[CollectionListItem]**](CollectionListItem.md) | Page containing the results of the collections search | 

## Example

```python
from revengai.models.list_collection_results import ListCollectionResults

# TODO update the JSON string below
json = "{}"
# create an instance of ListCollectionResults from a JSON string
list_collection_results_instance = ListCollectionResults.from_json(json)
# print the JSON string representation of the object
print(ListCollectionResults.to_json())

# convert the object into a dict
list_collection_results_dict = list_collection_results_instance.to_dict()
# create an instance of ListCollectionResults from a dict
list_collection_results_from_dict = ListCollectionResults.from_dict(list_collection_results_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


