# CheckSecurityChecksTaskResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**BinaryTaskStatus**](BinaryTaskStatus.md) |  | 

## Example

```python
from revengai.models.check_security_checks_task_response import CheckSecurityChecksTaskResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CheckSecurityChecksTaskResponse from a JSON string
check_security_checks_task_response_instance = CheckSecurityChecksTaskResponse.from_json(json)
# print the JSON string representation of the object
print(CheckSecurityChecksTaskResponse.to_json())

# convert the object into a dict
check_security_checks_task_response_dict = check_security_checks_task_response_instance.to_dict()
# create an instance of CheckSecurityChecksTaskResponse from a dict
check_security_checks_task_response_from_dict = CheckSecurityChecksTaskResponse.from_dict(check_security_checks_task_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


