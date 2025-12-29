# BaseResponseCheckSecurityChecksTaskResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**CheckSecurityChecksTaskResponse**](CheckSecurityChecksTaskResponse.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_check_security_checks_task_response import BaseResponseCheckSecurityChecksTaskResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseCheckSecurityChecksTaskResponse from a JSON string
base_response_check_security_checks_task_response_instance = BaseResponseCheckSecurityChecksTaskResponse.from_json(json)
# print the JSON string representation of the object
print(BaseResponseCheckSecurityChecksTaskResponse.to_json())

# convert the object into a dict
base_response_check_security_checks_task_response_dict = base_response_check_security_checks_task_response_instance.to_dict()
# create an instance of BaseResponseCheckSecurityChecksTaskResponse from a dict
base_response_check_security_checks_task_response_from_dict = BaseResponseCheckSecurityChecksTaskResponse.from_dict(base_response_check_security_checks_task_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


