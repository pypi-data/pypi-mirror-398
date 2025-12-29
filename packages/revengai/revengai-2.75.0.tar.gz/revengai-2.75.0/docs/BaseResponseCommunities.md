# BaseResponseCommunities


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Communities**](Communities.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_communities import BaseResponseCommunities

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseCommunities from a JSON string
base_response_communities_instance = BaseResponseCommunities.from_json(json)
# print the JSON string representation of the object
print(BaseResponseCommunities.to_json())

# convert the object into a dict
base_response_communities_dict = base_response_communities_instance.to_dict()
# create an instance of BaseResponseCommunities from a dict
base_response_communities_from_dict = BaseResponseCommunities.from_dict(base_response_communities_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


