# BaseResponseBinaryExternalsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**BinaryExternalsResponse**](BinaryExternalsResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_binary_externals_response import BaseResponseBinaryExternalsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseBinaryExternalsResponse from a JSON string
base_response_binary_externals_response_instance = BaseResponseBinaryExternalsResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseBinaryExternalsResponse.to_json())

# convert the object into a dict
base_response_binary_externals_response_dict = base_response_binary_externals_response_instance.to_dict()
# create an instance of BaseResponseBinaryExternalsResponse from a dict
base_response_binary_externals_response_from_dict = BaseResponseBinaryExternalsResponse.from_dict(base_response_binary_externals_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


