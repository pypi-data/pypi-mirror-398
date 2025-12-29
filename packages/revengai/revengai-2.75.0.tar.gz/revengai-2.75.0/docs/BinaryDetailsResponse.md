# BinaryDetailsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**arch** | **str** | The architecture of the binary | 
**bits** | **int** | The size of the binary in bits | 
**crc32** | **str** |  | 
**var_class** | **str** |  | 
**entropy** | **float** |  | 
**file_size** | **int** |  | 
**language** | **str** |  | 
**md5** | **str** |  | 
**machine** | **str** |  | 
**os** | **str** | OS target of the binary | 
**sha1** | **str** | SHA1 hash of the binary | 
**sha256** | **str** | SHA256 hash of the binary | 
**ssdeep** | **str** |  | 
**static** | **bool** |  | 
**stripped** | **bool** |  | 
**sub_sys** | **str** |  | 
**tlsh** | **str** |  | 
**type** | **str** |  | 
**debug** | **bool** |  | 
**first_seen** | **datetime** |  | 

## Example

```python
from revengai.models.binary_details_response import BinaryDetailsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BinaryDetailsResponse from a JSON string
binary_details_response_instance = BinaryDetailsResponse.from_json(json)
# print the JSON string representation of the object
print(BinaryDetailsResponse.to_json())

# convert the object into a dict
binary_details_response_dict = binary_details_response_instance.to_dict()
# create an instance of BinaryDetailsResponse from a dict
binary_details_response_from_dict = BinaryDetailsResponse.from_dict(binary_details_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


