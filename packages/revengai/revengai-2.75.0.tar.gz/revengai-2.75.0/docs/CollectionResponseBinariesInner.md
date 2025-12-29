# CollectionResponseBinariesInner


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
from revengai.models.collection_response_binaries_inner import CollectionResponseBinariesInner

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionResponseBinariesInner from a JSON string
collection_response_binaries_inner_instance = CollectionResponseBinariesInner.from_json(json)
# print the JSON string representation of the object
print(CollectionResponseBinariesInner.to_json())

# convert the object into a dict
collection_response_binaries_inner_dict = collection_response_binaries_inner_instance.to_dict()
# create an instance of CollectionResponseBinariesInner from a dict
collection_response_binaries_inner_from_dict = CollectionResponseBinariesInner.from_dict(collection_response_binaries_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


