# CollectionBinariesUpdateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binaries** | [**List[CollectionBinaryResponse]**](CollectionBinaryResponse.md) | Collection binaries | 

## Example

```python
from revengai.models.collection_binaries_update_response import CollectionBinariesUpdateResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CollectionBinariesUpdateResponse from a JSON string
collection_binaries_update_response_instance = CollectionBinariesUpdateResponse.from_json(json)
# print the JSON string representation of the object
print(CollectionBinariesUpdateResponse.to_json())

# convert the object into a dict
collection_binaries_update_response_dict = collection_binaries_update_response_instance.to_dict()
# create an instance of CollectionBinariesUpdateResponse from a dict
collection_binaries_update_response_from_dict = CollectionBinariesUpdateResponse.from_dict(collection_binaries_update_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


