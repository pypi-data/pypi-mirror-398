# BinaryAdditionalDetailsDataResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**file** | [**FileMetadata**](FileMetadata.md) |  | 
**pe** | [**PEModel**](PEModel.md) |  | [optional] 
**elf** | [**ELFModel**](ELFModel.md) |  | [optional] 

## Example

```python
from revengai.models.binary_additional_details_data_response import BinaryAdditionalDetailsDataResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BinaryAdditionalDetailsDataResponse from a JSON string
binary_additional_details_data_response_instance = BinaryAdditionalDetailsDataResponse.from_json(json)
# print the JSON string representation of the object
print(BinaryAdditionalDetailsDataResponse.to_json())

# convert the object into a dict
binary_additional_details_data_response_dict = binary_additional_details_data_response_instance.to_dict()
# create an instance of BinaryAdditionalDetailsDataResponse from a dict
binary_additional_details_data_response_from_dict = BinaryAdditionalDetailsDataResponse.from_dict(binary_additional_details_data_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


