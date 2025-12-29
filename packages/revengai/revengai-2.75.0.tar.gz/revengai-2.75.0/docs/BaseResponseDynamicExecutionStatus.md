# BaseResponseDynamicExecutionStatus


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**AppServicesDynamicExecutionSchemasDynamicExecutionStatus**](AppServicesDynamicExecutionSchemasDynamicExecutionStatus.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_dynamic_execution_status import BaseResponseDynamicExecutionStatus

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseDynamicExecutionStatus from a JSON string
base_response_dynamic_execution_status_instance = BaseResponseDynamicExecutionStatus.from_json(json)
# print the JSON string representation of the object
print(BaseResponseDynamicExecutionStatus.to_json())

# convert the object into a dict
base_response_dynamic_execution_status_dict = base_response_dynamic_execution_status_instance.to_dict()
# create an instance of BaseResponseDynamicExecutionStatus from a dict
base_response_dynamic_execution_status_from_dict = BaseResponseDynamicExecutionStatus.from_dict(base_response_dynamic_execution_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


