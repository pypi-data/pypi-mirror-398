# CollectionBinaryResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**analysis_id** | **int** | Analysis ID | 
**binary_id** | **int** | Binary ID | 
**binary_name** | **str** | Binary name | 
**owner_id** | **int** | Binary owner | 
**sha_256_hash** | **str** | Binary SHA-256 hash | 
**created_at** | **datetime** | Binary creation date | 

## Example

```python
from revengai.models.collection_binary_response import CollectionBinaryResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionBinaryResponse from a JSON string
collection_binary_response_instance = CollectionBinaryResponse.from_json(json)
# print the JSON string representation of the object
print(CollectionBinaryResponse.to_json())

# convert the object into a dict
collection_binary_response_dict = collection_binary_response_instance.to_dict()
# create an instance of CollectionBinaryResponse from a dict
collection_binary_response_from_dict = CollectionBinaryResponse.from_dict(collection_binary_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


