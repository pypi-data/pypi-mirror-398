# BinaryAdditionalResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_id** | **int** |  | 
**details** | [**BinaryAdditionalDetailsDataResponse**](BinaryAdditionalDetailsDataResponse.md) |  | 
**creation** | **datetime** |  | [optional] 

## Example

```python
from revengai.models.binary_additional_response import BinaryAdditionalResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BinaryAdditionalResponse from a JSON string
binary_additional_response_instance = BinaryAdditionalResponse.from_json(json)
# print the JSON string representation of the object
print(BinaryAdditionalResponse.to_json())

# convert the object into a dict
binary_additional_response_dict = binary_additional_response_instance.to_dict()
# create an instance of BinaryAdditionalResponse from a dict
binary_additional_response_from_dict = BinaryAdditionalResponse.from_dict(binary_additional_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


