# GetPublicUserResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**username** | **str** |  | 
**user_id** | **int** |  | 

## Example

```python
from revengai.models.get_public_user_response import GetPublicUserResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetPublicUserResponse from a JSON string
get_public_user_response_instance = GetPublicUserResponse.from_json(json)
# print the JSON string representation of the object
print(GetPublicUserResponse.to_json())

# convert the object into a dict
get_public_user_response_dict = get_public_user_response_instance.to_dict()
# create an instance of GetPublicUserResponse from a dict
get_public_user_response_from_dict = GetPublicUserResponse.from_dict(get_public_user_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


