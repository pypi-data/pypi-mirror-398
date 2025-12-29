# QueuedSecurityChecksTaskResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**task_id** | **str** |  | 

## Example

```python
from revengai.models.queued_security_checks_task_response import QueuedSecurityChecksTaskResponse

# TODO update the JSON string below
json = "{}"
# create an instance of QueuedSecurityChecksTaskResponse from a JSON string
queued_security_checks_task_response_instance = QueuedSecurityChecksTaskResponse.from_json(json)
# print the JSON string representation of the object
print(QueuedSecurityChecksTaskResponse.to_json())

# convert the object into a dict
queued_security_checks_task_response_dict = queued_security_checks_task_response_instance.to_dict()
# create an instance of QueuedSecurityChecksTaskResponse from a dict
queued_security_checks_task_response_from_dict = QueuedSecurityChecksTaskResponse.from_dict(queued_security_checks_task_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


