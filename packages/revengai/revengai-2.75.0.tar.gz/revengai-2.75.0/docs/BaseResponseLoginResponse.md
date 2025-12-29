# BaseResponseLoginResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**LoginResponse**](LoginResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_login_response import BaseResponseLoginResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseLoginResponse from a JSON string
base_response_login_response_instance = BaseResponseLoginResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseLoginResponse.to_json())

# convert the object into a dict
base_response_login_response_dict = base_response_login_response_instance.to_dict()
# create an instance of BaseResponseLoginResponse from a dict
base_response_login_response_from_dict = BaseResponseLoginResponse.from_dict(base_response_login_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


