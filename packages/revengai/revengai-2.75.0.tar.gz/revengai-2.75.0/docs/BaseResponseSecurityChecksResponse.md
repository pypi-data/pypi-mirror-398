# BaseResponseSecurityChecksResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**SecurityChecksResponse**](SecurityChecksResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_security_checks_response import BaseResponseSecurityChecksResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseSecurityChecksResponse from a JSON string
base_response_security_checks_response_instance = BaseResponseSecurityChecksResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseSecurityChecksResponse.to_json())

# convert the object into a dict
base_response_security_checks_response_dict = base_response_security_checks_response_instance.to_dict()
# create an instance of BaseResponseSecurityChecksResponse from a dict
base_response_security_checks_response_from_dict = BaseResponseSecurityChecksResponse.from_dict(base_response_security_checks_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


