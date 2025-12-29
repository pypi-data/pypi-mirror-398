# RelativeBinaryResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_id** | **int** | ID of the relative binary | 
**name** | **str** | Name of the relative binary | 
**sha256** | **str** | SHA256 hash of the relative binary | 

## Example

```python
from revengai.models.relative_binary_response import RelativeBinaryResponse

# TODO update the JSON string below
json = "{}"
# create an instance of RelativeBinaryResponse from a JSON string
relative_binary_response_instance = RelativeBinaryResponse.from_json(json)
# print the JSON string representation of the object
print(RelativeBinaryResponse.to_json())

# convert the object into a dict
relative_binary_response_dict = relative_binary_response_instance.to_dict()
# create an instance of RelativeBinaryResponse from a dict
relative_binary_response_from_dict = RelativeBinaryResponse.from_dict(relative_binary_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


