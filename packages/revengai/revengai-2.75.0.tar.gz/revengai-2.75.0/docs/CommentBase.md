# CommentBase


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**content** | **str** | Comment text content | 

## Example

```python
from revengai.models.comment_base import CommentBase

# TODO update the JSON string below
json = "{}"
# create an instance of CommentBase from a JSON string
comment_base_instance = CommentBase.from_json(json)
# print the JSON string representation of the object
print(CommentBase.to_json())

# convert the object into a dict
comment_base_dict = comment_base_instance.to_dict()
# create an instance of CommentBase from a dict
comment_base_from_dict = CommentBase.from_dict(comment_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


