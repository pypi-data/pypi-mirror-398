# BaseResponseUploadResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**UploadResponse**](UploadResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_upload_response import BaseResponseUploadResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseUploadResponse from a JSON string
base_response_upload_response_instance = BaseResponseUploadResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseUploadResponse.to_json())

# convert the object into a dict
base_response_upload_response_dict = base_response_upload_response_instance.to_dict()
# create an instance of BaseResponseUploadResponse from a dict
base_response_upload_response_from_dict = BaseResponseUploadResponse.from_dict(base_response_upload_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


