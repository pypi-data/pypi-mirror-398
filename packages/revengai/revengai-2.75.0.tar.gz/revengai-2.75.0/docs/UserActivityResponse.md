# UserActivityResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**actions** | **str** |  | 
**activity_scope** | **str** |  | 
**creation** | **datetime** |  | 
**message** | **str** |  | 
**sources** | **str** |  | 
**username** | **str** |  | 

## Example

```python
from revengai.models.user_activity_response import UserActivityResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UserActivityResponse from a JSON string
user_activity_response_instance = UserActivityResponse.from_json(json)
# print the JSON string representation of the object
print(UserActivityResponse.to_json())

# convert the object into a dict
user_activity_response_dict = user_activity_response_instance.to_dict()
# create an instance of UserActivityResponse from a dict
user_activity_response_from_dict = UserActivityResponse.from_dict(user_activity_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


