# BaseResponseDict


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | **Dict[str, object]** |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_dict import BaseResponseDict

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseDict from a JSON string
base_response_dict_instance = BaseResponseDict.from_json(json)
# print the JSON string representation of the object
print(BaseResponseDict.to_json())

# convert the object into a dict
base_response_dict_dict = base_response_dict_instance.to_dict()
# create an instance of BaseResponseDict from a dict
base_response_dict_from_dict = BaseResponseDict.from_dict(base_response_dict_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


