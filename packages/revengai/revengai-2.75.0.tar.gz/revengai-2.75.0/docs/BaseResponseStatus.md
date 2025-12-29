# BaseResponseStatus


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**StatusOutput**](StatusOutput.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_status import BaseResponseStatus

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseStatus from a JSON string
base_response_status_instance = BaseResponseStatus.from_json(json)
# print the JSON string representation of the object
print(BaseResponseStatus.to_json())

# convert the object into a dict
base_response_status_dict = base_response_status_instance.to_dict()
# create an instance of BaseResponseStatus from a dict
base_response_status_from_dict = BaseResponseStatus.from_dict(base_response_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


