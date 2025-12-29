# BaseResponseListDieMatch


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**List[DieMatch]**](DieMatch.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_list_die_match import BaseResponseListDieMatch

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseListDieMatch from a JSON string
base_response_list_die_match_instance = BaseResponseListDieMatch.from_json(json)
# print the JSON string representation of the object
print(BaseResponseListDieMatch.to_json())

# convert the object into a dict
base_response_list_die_match_dict = base_response_list_die_match_instance.to_dict()
# create an instance of BaseResponseListDieMatch from a dict
base_response_list_die_match_from_dict = BaseResponseListDieMatch.from_dict(base_response_list_die_match_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


