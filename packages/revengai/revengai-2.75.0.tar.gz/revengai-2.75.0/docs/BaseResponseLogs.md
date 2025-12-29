# BaseResponseLogs


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Logs**](Logs.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_logs import BaseResponseLogs

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseLogs from a JSON string
base_response_logs_instance = BaseResponseLogs.from_json(json)
# print the JSON string representation of the object
print(BaseResponseLogs.to_json())

# convert the object into a dict
base_response_logs_dict = base_response_logs_instance.to_dict()
# create an instance of BaseResponseLogs from a dict
base_response_logs_from_dict = BaseResponseLogs.from_dict(base_response_logs_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


