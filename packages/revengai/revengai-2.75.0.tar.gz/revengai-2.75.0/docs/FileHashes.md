# FileHashes


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**md5** | **str** |  | 
**sha1** | **str** |  | 
**sha256** | **str** |  | 
**sha512** | **str** |  | 
**sha3_224** | **str** |  | 
**sha3_256** | **str** |  | 
**sha3_384** | **str** |  | 
**sha3_512** | **str** |  | 

## Example

```python
from revengai.models.file_hashes import FileHashes

# TODO update the JSON string below
json = "{}"
# create an instance of FileHashes from a JSON string
file_hashes_instance = FileHashes.from_json(json)
# print the JSON string representation of the object
print(FileHashes.to_json())

# convert the object into a dict
file_hashes_dict = file_hashes_instance.to_dict()
# create an instance of FileHashes from a dict
file_hashes_from_dict = FileHashes.from_dict(file_hashes_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


