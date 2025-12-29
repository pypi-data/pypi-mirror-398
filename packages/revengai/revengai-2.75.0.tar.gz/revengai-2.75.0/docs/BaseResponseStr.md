# BaseResponseStr


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | **str** |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_str import BaseResponseStr

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseStr from a JSON string
base_response_str_instance = BaseResponseStr.from_json(json)
# print the JSON string representation of the object
print(BaseResponseStr.to_json())

# convert the object into a dict
base_response_str_dict = base_response_str_instance.to_dict()
# create an instance of BaseResponseStr from a dict
base_response_str_from_dict = BaseResponseStr.from_dict(base_response_str_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


