# BinaryExternalsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sha_256_hash** | **str** | SHA256 hash of the binary | 
**vt** | **Dict[str, object]** | VirusTotal information | 
**vt_last_updated** | **datetime** | VirusTotal last updated date | 
**mb** | **Dict[str, object]** | MalwareBazaar information | 
**mb_last_updated** | **datetime** | MalwareBazaar last updated date | 

## Example

```python
from revengai.models.binary_externals_response import BinaryExternalsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BinaryExternalsResponse from a JSON string
binary_externals_response_instance = BinaryExternalsResponse.from_json(json)
# print the JSON string representation of the object
print(BinaryExternalsResponse.to_json())

# convert the object into a dict
binary_externals_response_dict = binary_externals_response_instance.to_dict()
# create an instance of BinaryExternalsResponse from a dict
binary_externals_response_from_dict = BinaryExternalsResponse.from_dict(binary_externals_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


