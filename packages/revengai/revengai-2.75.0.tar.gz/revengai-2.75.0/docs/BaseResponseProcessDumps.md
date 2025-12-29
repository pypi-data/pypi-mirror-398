# BaseResponseProcessDumps


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**ProcessDumps**](ProcessDumps.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_process_dumps import BaseResponseProcessDumps

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseProcessDumps from a JSON string
base_response_process_dumps_instance = BaseResponseProcessDumps.from_json(json)
# print the JSON string representation of the object
print(BaseResponseProcessDumps.to_json())

# convert the object into a dict
base_response_process_dumps_dict = base_response_process_dumps_instance.to_dict()
# create an instance of BaseResponseProcessDumps from a dict
base_response_process_dumps_from_dict = BaseResponseProcessDumps.from_dict(base_response_process_dumps_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


