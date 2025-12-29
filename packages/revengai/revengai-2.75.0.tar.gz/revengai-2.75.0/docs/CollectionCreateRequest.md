# CollectionCreateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**collection_name** | **str** |  | 
**description** | **str** |  | 
**collection_scope** | [**CollectionScope**](CollectionScope.md) |  | [optional] 
**tags** | **List[str]** |  | [optional] 
**binaries** | **List[int]** |  | [optional] 
**model_id** | **int** |  | 

## Example

```python
from revengai.models.collection_create_request import CollectionCreateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionCreateRequest from a JSON string
collection_create_request_instance = CollectionCreateRequest.from_json(json)
# print the JSON string representation of the object
print(CollectionCreateRequest.to_json())

# convert the object into a dict
collection_create_request_dict = collection_create_request_instance.to_dict()
# create an instance of CollectionCreateRequest from a dict
collection_create_request_from_dict = CollectionCreateRequest.from_dict(collection_create_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


