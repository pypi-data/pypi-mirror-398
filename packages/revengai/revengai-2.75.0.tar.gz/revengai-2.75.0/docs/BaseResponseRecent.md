# BaseResponseRecent


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Recent**](Recent.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_recent import BaseResponseRecent

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseRecent from a JSON string
base_response_recent_instance = BaseResponseRecent.from_json(json)
# print the JSON string representation of the object
print(BaseResponseRecent.to_json())

# convert the object into a dict
base_response_recent_dict = base_response_recent_instance.to_dict()
# create an instance of BaseResponseRecent from a dict
base_response_recent_from_dict = BaseResponseRecent.from_dict(base_response_recent_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


