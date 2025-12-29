# CollectionResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_id** | **int** | Collection ID | 
**collection_name** | **str** | Collection name | 
**description** | **str** | Collection description | 
**model_id** | **int** | Collection model ID | 
**user_id** | **int** | Collection user ID | 
**team_id** | **int** |  | [optional] 
**collection_scope** | [**CollectionScope**](CollectionScope.md) | Collection public status | 
**created_at** | **datetime** | Collection creation date | 
**updated_at** | **datetime** | Collection last update date | 
**tags** | **List[str]** |  | [optional] 
**binaries** | [**List[CollectionResponseBinariesInner]**](CollectionResponseBinariesInner.md) |  | [optional] 

## Example

```python
from revengai.models.collection_response import CollectionResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionResponse from a JSON string
collection_response_instance = CollectionResponse.from_json(json)
# print the JSON string representation of the object
print(CollectionResponse.to_json())

# convert the object into a dict
collection_response_dict = collection_response_instance.to_dict()
# create an instance of CollectionResponse from a dict
collection_response_from_dict = CollectionResponse.from_dict(collection_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


