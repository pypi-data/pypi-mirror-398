# BaseResponseBasic


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Basic**](Basic.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_basic import BaseResponseBasic

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseBasic from a JSON string
base_response_basic_instance = BaseResponseBasic.from_json(json)
# print the JSON string representation of the object
print(BaseResponseBasic.to_json())

# convert the object into a dict
base_response_basic_dict = base_response_basic_instance.to_dict()
# create an instance of BaseResponseBasic from a dict
base_response_basic_from_dict = BaseResponseBasic.from_dict(base_response_basic_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


